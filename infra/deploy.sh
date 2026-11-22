#!/usr/bin/env bash
set -euo pipefail

release=${1:?Release directory required}
root=/opt/ocenomat
exec 9>"$root/deploy.lock"
flock -n 9 || { printf 'Another deployment is running\n' >&2; exit 1; }

compose=(docker compose --env-file "$root/.env" -f "$release/infra/compose.yaml" -f "$release/infra/compose.deploy.yaml")
for service in kompas-db-1 kompas-rustfs-1; do
  test "$(docker inspect -f '{{.State.Health.Status}}' "$service")" = healthy
done
docker volume inspect kompas_postgres-data kompas_rustfs-data >/dev/null

"${compose[@]}" build backend migrate frontend
"${compose[@]}" stop frontend backend
install -d -m 700 "$root/backups"
backup=$(mktemp "$root/backups/pre-deploy-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX.dump")
chmod 600 "$backup"
if ! docker exec kompas-db-1 sh -c 'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$backup"; then
  rm -f "$backup"
  exit 1
fi
test -s "$backup"
docker exec -i kompas-db-1 pg_restore --list < "$backup" >/dev/null

"${compose[@]}" run --rm --no-deps migrate
"${compose[@]}" up -d --no-deps --wait --wait-timeout 180 backend frontend
curl --fail --silent --show-error --retry 15 --retry-connrefused --retry-delay 2 --max-time 10 http://127.0.0.1:3000/login >/dev/null
printf 'Deployment complete. Database backup: %s\n' "$backup"

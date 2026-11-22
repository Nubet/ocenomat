import os
import subprocess
from pathlib import Path


def run_deploy(tmp_path, failure=""):
    root = tmp_path / "server"
    root.mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "commands"
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'printf "%s\\n" "$*" >> "$COMMAND_LOG"\n'
        'case "$*" in\n'
        '  "inspect "*) printf "healthy\\n" ;;\n'
        '  *"pg_dump"*) [ "$FAILURE" != backup ] || exit 1; printf dump ;;\n'
        '  *"pg_restore --list"*) [ "$FAILURE" != restore ] || exit 1 ;;\n'
        '  *"run --rm --no-deps migrate"*) [ "$FAILURE" != migrate ] || exit 1 ;;\n'
        'esac\n'
    )
    docker.chmod(0o755)
    curl = bin_dir / "curl"
    curl.write_text("#!/bin/sh\nexit 0\n")
    curl.chmod(0o755)
    source = (Path(__file__).parents[1] / "deploy.sh").read_text()
    script = tmp_path / "deploy.sh"
    script.write_text(source.replace("root=/opt/ocenomat", f"root={root}"))
    result = subprocess.run(
        ["bash", str(script), str(root / "release")],
        env={**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}",
             "COMMAND_LOG": str(log), "FAILURE": failure},
        capture_output=True,
        text=True,
    )
    return result, log.read_text(), root


def test_success_orders_backup_migration_and_start(tmp_path):
    result, commands, root = run_deploy(tmp_path)
    assert result.returncode == 0, result.stderr
    assert commands.index("build backend migrate frontend") < commands.index(
        "stop frontend backend"
    )
    assert commands.index("pg_dump") < commands.index("pg_restore --list")
    assert commands.index("pg_restore --list") < commands.index(
        "run --rm --no-deps migrate"
    )
    assert commands.index("run --rm --no-deps migrate") < commands.index(
        "up -d --no-deps"
    )
    assert len(list((root / "backups").glob("*.dump"))) == 1


def test_failed_backup_stops_before_migration(tmp_path):
    result, commands, root = run_deploy(tmp_path, "backup")
    assert result.returncode != 0
    assert "run --rm --no-deps migrate" not in commands
    assert "up -d --no-deps" not in commands
    assert not list((root / "backups").glob("*.dump"))


def test_failed_migration_never_starts_new_application(tmp_path):
    result, commands, root = run_deploy(tmp_path, "migrate")
    assert result.returncode != 0
    assert "up -d --no-deps" not in commands
    assert len(list((root / "backups").glob("*.dump"))) == 1

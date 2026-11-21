import "server-only";

import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { authConfig, sessionCookieOptions } from "./config";

export async function createAuthClient() {
  const config = authConfig();
  if (!config) throw new Error("Supabase Auth is not configured");
  const store = await cookies();
  return createServerClient(config.url, config.key, {
    cookieOptions: sessionCookieOptions,
    cookies: {
      getAll: () => store.getAll(),
      setAll(values) {
        try {
          values.forEach(({ name, value, options }) => store.set(name, value, options));
        } catch {
          // Server Components cannot write cookies; proxy refreshes them before rendering.
        }
      },
    },
  });
}

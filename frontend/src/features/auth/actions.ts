"use server";

import { redirect } from "next/navigation";
import { authConfig } from "./config";
import { createAuthClient } from "./server";
import { fetchProfile } from "./session";

export async function signIn(_previous: { error: string }, form: FormData) {
  const email = form.get("email");
  const password = form.get("password");
  if (
    typeof email !== "string" ||
    email.length > 320 ||
    !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim()) ||
    typeof password !== "string" ||
    !password ||
    password.length > 1024
  )
    return { error: "Podaj poprawny adres e-mail i hasło." };
  if (!authConfig()) return { error: "Logowanie nie jest jeszcze skonfigurowane." };
  const client = await createAuthClient();
  try {
    const { data, error } = await client.auth.signInWithPassword({ email: email.trim(), password });
    if (error || !data.session)
      return { error: "Nie udało się zalogować. Sprawdź dane lub spróbuj ponownie." };
    const profile = await fetchProfile(data.session.access_token);
    if (!profile.ok) {
      await client.auth.signOut({ scope: "local" });
      return {
        error:
          profile.status === 401 || profile.status === 403
            ? "Konto nie ma aktywnego dostępu do Kompasu. Skontaktuj się z administratorem."
            : "Serwer Kompasu jest niedostępny. Spróbuj ponownie.",
      };
    }
  } catch {
    await client.auth.signOut({ scope: "local" });
    return { error: "Usługa logowania jest niedostępna. Spróbuj ponownie." };
  }
  redirect("/");
}

export async function signOut() {
  const client = await createAuthClient();
  const { error } = await client.auth.signOut({ scope: "local" });
  if (error) throw new Error("Nie udało się wylogować. Spróbuj ponownie.");
  redirect("/login");
}

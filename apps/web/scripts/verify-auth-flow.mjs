const baseUrl = process.env.WEB_BASE_URL ?? "http://localhost:3000";
const unique = Date.now();
const email = `web-${unique}@example.com`;
const loginId = `web_${unique}`;
const password = "password123";
const cookieJar = new Map();

function getSetCookies(response) {
  if (typeof response.headers.getSetCookie === "function") {
    return response.headers.getSetCookie();
  }

  const cookie = response.headers.get("set-cookie");
  return cookie ? [cookie] : [];
}

function storeCookies(response) {
  for (const setCookie of getSetCookies(response)) {
    const [pair] = setCookie.split(";");
    const separatorIndex = pair.indexOf("=");
    if (separatorIndex === -1) {
      continue;
    }

    const name = pair.slice(0, separatorIndex);
    const value = pair.slice(separatorIndex + 1);
    if (value === "") {
      cookieJar.delete(name);
    } else {
      cookieJar.set(name, value);
    }
  }
}

function cookieHeader() {
  return Array.from(cookieJar.entries())
    .map(([name, value]) => `${name}=${value}`)
    .join("; ");
}

async function request(path, options = {}) {
  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(cookieJar.size > 0 ? { Cookie: cookieHeader() } : {}),
      ...options.headers
    }
  });
  storeCookies(response);

  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(`${options.method ?? "GET"} ${path} failed: ${response.status} ${JSON.stringify(body)}`);
  }

  return body;
}

const registered = await request("/api/backend/auth/register", {
  method: "POST",
  body: JSON.stringify({
    email,
    login_id: loginId,
    display_name: "Web Flow User",
    password
  })
});

if (!registered.user || !cookieJar.has("dw_fx_ledger_access_token")) {
  throw new Error("Register did not set auth cookies");
}

const loggedIn = await request("/api/backend/auth/login", {
  method: "POST",
  body: JSON.stringify({
    identifier: loginId,
    password
  })
});

if (!loggedIn.user || !cookieJar.has("dw_fx_ledger_refresh_token")) {
  throw new Error("Login did not set auth cookies");
}

const me = await request("/api/backend/auth/me");

if (me.email !== email || me.login_id !== loginId) {
  throw new Error("GET /auth/me returned an unexpected user");
}

await request("/api/backend/auth/refresh", {
  method: "POST"
});

await request("/api/backend/auth/logout", {
  method: "POST"
});

console.log(`auth flow ok: ${email}`);

const baseUrl = process.env.WEB_BASE_URL ?? "http://localhost:3000";
const unique = Date.now();

function createClient(label) {
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

  return {
    async request(path, options = {}) {
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
        const error = new Error(
          `${label}: ${options.method ?? "GET"} ${path} failed: ${response.status} ${JSON.stringify(body)}`
        );
        error.status = response.status;
        throw error;
      }

      return body;
    }
  };
}

async function register(client, suffix) {
  return client.request("/api/backend/auth/register", {
    method: "POST",
    body: JSON.stringify({
      email: `posts-${unique}-${suffix}@example.com`,
      login_id: `posts_${unique}_${suffix}`,
      display_name: `Posts ${suffix}`,
      password: "password123"
    })
  });
}

const owner = createClient("owner");
const other = createClient("other");

await register(owner, "owner");
await register(other, "other");

const created = await owner.request("/api/backend/posts", {
  method: "POST",
  body: JSON.stringify({
    title: "웹 게시글 테스트",
    content: "게시글 CRUD 검증 내용"
  })
});

const list = await owner.request("/api/backend/posts");
if (!list.items.some((post) => post.postId === created.postId)) {
  throw new Error("Created post was not found in the list");
}

const detail = await owner.request(`/api/backend/posts/${created.postId}`);
if (detail.title !== "웹 게시글 테스트" || detail.viewCount < 1) {
  throw new Error("Post detail did not match the created post");
}

let forbiddenUpdate = false;
try {
  await other.request(`/api/backend/posts/${created.postId}`, {
    method: "PUT",
    body: JSON.stringify({
      title: "권한 없는 수정",
      content: "수정 불가"
    })
  });
} catch (error) {
  forbiddenUpdate = error.status === 403;
}
if (!forbiddenUpdate) {
  throw new Error("Unauthorized update was not rejected");
}

let forbiddenDelete = false;
try {
  await other.request(`/api/backend/posts/${created.postId}`, {
    method: "DELETE"
  });
} catch (error) {
  forbiddenDelete = error.status === 403;
}
if (!forbiddenDelete) {
  throw new Error("Unauthorized delete was not rejected");
}

const updated = await owner.request(`/api/backend/posts/${created.postId}`, {
  method: "PUT",
  body: JSON.stringify({
    title: "수정된 웹 게시글",
    content: "수정된 내용"
  })
});
if (updated.title !== "수정된 웹 게시글") {
  throw new Error("Post update did not persist");
}

await owner.request(`/api/backend/posts/${created.postId}`, {
  method: "DELETE"
});

console.log(`posts flow ok: ${created.postId}`);

const baseUrl = process.env.WEB_BASE_URL ?? "http://localhost:3000";
const unique = Date.now();
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

    cookieJar.set(pair.slice(0, separatorIndex), pair.slice(separatorIndex + 1));
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

await request("/api/backend/auth/register", {
  method: "POST",
  body: JSON.stringify({
    email: `fx-web-${unique}@example.com`,
    login_id: `fx_web_${unique}`,
    display_name: "FX Web User",
    password: "password123"
  })
});

const created = await request("/api/backend/fx/buy-lots", {
  method: "POST",
  body: JSON.stringify({
    buyDate: "2025-03-06",
    buyKrwAmount: 41675154,
    buyExchangeRate: "1450.51"
  })
});

if (created.lotStatus !== "open" || created.usdAmount !== "28731.379997") {
  throw new Error(`Unexpected buy lot response: ${JSON.stringify(created)}`);
}

const list = await request("/api/backend/fx/buy-lots");
if (!list.items.some((lot) => lot.buyLotId === created.buyLotId)) {
  throw new Error("Created buy lot was not found in the list");
}

const editable = await request(`/api/backend/fx/buy-lots/${created.buyLotId}`, {
  method: "PUT",
  body: JSON.stringify({
    buyDate: "2025-03-07",
    buyKrwAmount: 41675154,
    buyExchangeRate: "1450.51"
  })
});
if (editable.buyDate !== "2025-03-07") {
  throw new Error(`Unexpected buy lot update response: ${JSON.stringify(editable)}`);
}

const sortedBuyLots = await request("/api/backend/fx/buy-lots?sort_by=buy_exchange_rate&sort_order=asc");
if (!Array.isArray(sortedBuyLots.items)) {
  throw new Error("Sorted buy lot list did not return items");
}

const sell = await request("/api/backend/fx/sell-transactions", {
  method: "POST",
  body: JSON.stringify({
    sellDate: "2026-06-04",
    sellUsdAmount: "214.93",
    sellExchangeRate: "1531.33",
    allocationStrategy: "highest_rate_first"
  })
});

if (sell.totalRealProfitKrw !== 17371 || sell.allocations.length !== 1) {
  throw new Error(`Unexpected sell transaction response: ${JSON.stringify(sell)}`);
}

const sellList = await request(
  "/api/backend/fx/sell-transactions?sort_by=total_real_profit_krw&sort_order=desc"
);
if (!sellList.items.some((transaction) => transaction.sellTransactionId === sell.sellTransactionId)) {
  throw new Error("Created sell transaction was not found in the list");
}

console.log(`fx flow ok: buy lot ${created.buyLotId}, sell transaction ${sell.sellTransactionId}`);

const fs = require("node:fs");
const path = require("node:path");
const { spawn } = require("node:child_process");

const FRONTEND_URL = process.env.DCFT_FRONTEND_URL || "http://127.0.0.1:5174/";
const API_URL = process.env.DCFT_STAGING_API_URL || "http://127.0.0.1:8200";
const CHROME_PATH = process.env.CHROME_PATH || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const OUT_DIR = process.env.DCFT_VIEWPORT_OUTPUT_DIR || path.resolve(process.cwd(), ".dcft", "outputs", "viewports");
const PORT = Number(process.env.DCFT_CHROME_DEBUG_PORT || 9344);

fs.mkdirSync(OUT_DIR, { recursive: true });

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForChrome() {
  for (let index = 0; index < 40; index += 1) {
    try {
      const response = await fetch(`http://127.0.0.1:${PORT}/json/version`);
      if (response.ok) return;
    } catch {}
    await sleep(250);
  }
  throw new Error("chrome_not_ready");
}

function cdp(wsUrl) {
  const ws = new WebSocket(wsUrl);
  let id = 0;
  const pending = new Map();
  ws.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
      const task = pending.get(message.id);
      pending.delete(message.id);
      if (message.error) task.reject(new Error(JSON.stringify(message.error)));
      else task.resolve(message.result);
    }
  });
  return new Promise((resolve, reject) => {
    ws.addEventListener("open", () => resolve({
      send(method, params = {}) {
        const callId = ++id;
        ws.send(JSON.stringify({ id: callId, method, params }));
        return new Promise((res, rej) => pending.set(callId, { resolve: res, reject: rej }));
      },
      close() {
        ws.close();
      },
    }));
    ws.addEventListener("error", reject);
  });
}

async function createToken() {
  const unique = crypto.randomUUID().replaceAll("-", "").slice(0, 8);
  const response = await fetch(`${API_URL}/onboarding/tenants`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      tenant_name: `Viewport ${unique}`,
      admin_username: `viewport_${unique}`,
      admin_password: "viewport-user-pass-123",
      plan: "business_basic",
    }),
  });
  if (!response.ok) throw new Error(`onboarding_failed:${response.status}`);
  const body = await response.json();
  return body.access_token;
}

async function newPage() {
  const response = await fetch(`http://127.0.0.1:${PORT}/json/new?${encodeURIComponent("about:blank")}`, { method: "PUT" });
  if (!response.ok) throw new Error(`new_page_failed:${response.status}`);
  return response.json();
}

async function inspect(client, viewport, token) {
  await client.send("Emulation.setDeviceMetricsOverride", {
    width: viewport.width,
    height: viewport.height,
    deviceScaleFactor: viewport.mobile ? 2 : 1,
    mobile: viewport.mobile,
  });
  await client.send("Page.navigate", { url: FRONTEND_URL });
  await sleep(1500);
  await client.send("Runtime.evaluate", { expression: `localStorage.setItem("dcft_token", ${JSON.stringify(token)});`, returnByValue: true });
  await client.send("Page.reload", { ignoreCache: true });
  await sleep(2200);
  const evaluation = await client.send("Runtime.evaluate", {
    expression: `JSON.stringify({
      viewport: "${viewport.name}",
      clientWidth: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
      bodyScrollWidth: document.body.scrollWidth,
      overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
      hasOnboarding: document.body.innerText.includes("Onboarding"),
      hasSubscription: document.body.innerText.includes("Subscription"),
      hasAnalytics: document.body.innerText.includes("Product analytics"),
      hasFeedback: document.body.innerText.includes("Controlled feedback"),
      hasStaging: document.body.innerText.includes("Staging posture"),
      passwordPrefilled: [...document.querySelectorAll("input[type=password]")].some((input) => input.value.length > 0)
    })`,
    returnByValue: true,
  });
  const screenshot = await client.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
  const file = path.join(OUT_DIR, `dcft-${viewport.name}.png`);
  fs.writeFileSync(file, Buffer.from(screenshot.data, "base64"));
  return { ...JSON.parse(evaluation.result.value), screenshot: file };
}

async function main() {
  const chrome = spawn(CHROME_PATH, [
    "--headless=new",
    `--remote-debugging-port=${PORT}`,
    `--user-data-dir=${path.join(OUT_DIR, "chrome-profile")}`,
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check",
    "about:blank",
  ], { stdio: "ignore" });
  try {
    await waitForChrome();
    const token = await createToken();
    const page = await newPage();
    const client = await cdp(page.webSocketDebuggerUrl);
    await client.send("Page.enable");
    await client.send("Runtime.enable");
    const results = [];
    for (const viewport of [
      { name: "mobile", width: 390, height: 844, mobile: true },
      { name: "tablet", width: 768, height: 1024, mobile: true },
      { name: "desktop", width: 1365, height: 768, mobile: false },
    ]) {
      results.push(await inspect(client, viewport, token));
    }
    client.close();
    const ok = results.every((item) => !item.overflow && item.hasOnboarding && item.hasSubscription && item.hasAnalytics && item.hasFeedback && item.hasStaging && !item.passwordPrefilled);
    console.log(JSON.stringify({ status: ok ? "ok" : "blocked", frontend_url: FRONTEND_URL, api_url: API_URL, results }, null, 2));
    process.exitCode = ok ? 0 : 1;
  } finally {
    chrome.kill();
  }
}

main().catch((error) => {
  console.error(`VIEWPORT_VALIDATION_FAILED: ${error.message}`);
  process.exit(1);
});

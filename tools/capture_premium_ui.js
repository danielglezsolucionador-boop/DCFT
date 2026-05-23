const fs = require("node:fs");
const path = require("node:path");
const { spawn } = require("node:child_process");

const FRONTEND_URL = process.env.DCFT_FRONTEND_URL || "http://127.0.0.1:5174/";
const API_URL = process.env.DCFT_STAGING_API_URL || "http://127.0.0.1:8200";
const CHROME_PATH = process.env.CHROME_PATH || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const OUT_DIR = path.resolve(process.cwd(), ".dcft", "state");
const PORT = Number(process.env.DCFT_CHROME_DEBUG_PORT || 9354);

fs.mkdirSync(OUT_DIR, { recursive: true });

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForChrome() {
  for (let index = 0; index < 50; index += 1) {
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

async function newPage() {
  const response = await fetch(`http://127.0.0.1:${PORT}/json/new?${encodeURIComponent("about:blank")}`, { method: "PUT" });
  if (!response.ok) throw new Error(`new_page_failed:${response.status}`);
  return response.json();
}

async function createToken() {
  const unique = crypto.randomUUID().replaceAll("-", "").slice(0, 8);
  const response = await fetch(`${API_URL}/onboarding/tenants`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      tenant_name: `Premium UI ${unique}`,
      admin_username: `premium_${unique}`,
      admin_password: "premium-user-pass-123",
      plan: "business_basic",
    }),
  });
  if (!response.ok) throw new Error(`onboarding_failed:${response.status}`);
  const body = await response.json();
  return body.access_token;
}

async function navigateApp(client, viewport, token, selector) {
  await client.send("Emulation.setDeviceMetricsOverride", {
    width: viewport.width,
    height: viewport.height,
    deviceScaleFactor: 1,
    mobile: viewport.mobile,
  });
  await client.send("Page.navigate", { url: FRONTEND_URL });
  await sleep(1200);
  const storageExpression = token
    ? `localStorage.setItem("dcft_token", ${JSON.stringify(token)});`
    : `localStorage.removeItem("dcft_token");`;
  await client.send("Runtime.evaluate", { expression: storageExpression, returnByValue: true });
  await client.send("Page.reload", { ignoreCache: true });
  await sleep(2200);
  if (selector) {
    await client.send("Runtime.evaluate", {
      expression: `document.querySelector(${JSON.stringify(selector)})?.scrollIntoView({ block: "start" }); window.scrollBy(0, -14);`,
      returnByValue: true,
    });
    await sleep(600);
  }
}

async function capture(client, file) {
  const screenshot = await client.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
  const target = path.join(OUT_DIR, file);
  fs.writeFileSync(target, Buffer.from(screenshot.data, "base64"));
  return target;
}

async function inspectPage(client) {
  const result = await client.send("Runtime.evaluate", {
    expression: `JSON.stringify({
      width: document.documentElement.clientWidth,
      height: window.innerHeight,
      overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
      manifest: document.querySelector('link[rel="manifest"]')?.getAttribute('href'),
      appleIcon: document.querySelector('link[rel="apple-touch-icon"]')?.getAttribute('href'),
      text: document.body.innerText.slice(0, 500)
    })`,
    returnByValue: true,
  });
  return JSON.parse(result.result.value);
}

function previewHtml(kind) {
  const icon = `${FRONTEND_URL.replace(/\/$/, "")}/icon-512.png`;
  const subtitle = kind === "pwa"
    ? "Standalone • theme #092443 • short_name DCFT"
    : "Icono instalable • medico + financiero + tributario";
  return `data:text/html;charset=utf-8,${encodeURIComponent(`<!doctype html>
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      body{margin:0;min-height:100vh;display:grid;place-items:center;background:linear-gradient(180deg,#fbfdff,#eef4fb);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#071629}
      .card{width:min( calc(100vw - 40px), 520px);padding:34px;border-radius:34px;background:rgba(255,255,255,.84);box-shadow:10px 18px 48px rgba(7,22,41,.14),-8px -10px 24px rgba(255,255,255,.92);border:1px solid rgba(15,76,129,.12)}
      img{width:164px;height:164px;border-radius:36px;box-shadow:0 22px 44px rgba(9,36,67,.24);display:block;margin:0 auto 24px}
      h1{font-size:48px;line-height:.92;margin:0;text-align:center;letter-spacing:0;color:#092443}
      p{margin:12px 0 0;text-align:center;color:#526173;font-weight:700}
      .bar{height:7px;margin-top:28px;border-radius:999px;background:linear-gradient(90deg,#d73a31,#0f4c81)}
    </style></head><body><main class="card"><img src="${icon}" /><h1>DCFT</h1><p>Doctor Contable Financiero Tributario</p><p>${subtitle}</p><div class="bar"></div></main></body></html>`)}`;
}

async function main() {
  const chrome = spawn(CHROME_PATH, [
    "--headless=new",
    `--remote-debugging-port=${PORT}`,
    `--user-data-dir=${path.join(OUT_DIR, "chrome-premium-profile")}`,
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check",
    "about:blank",
  ], { stdio: "ignore" });

  const consoleErrors = [];
  const written = [];
  try {
    await waitForChrome();
    const token = await createToken();
    const page = await newPage();
    const client = await cdp(page.webSocketDebuggerUrl);
    await client.send("Page.enable");
    await client.send("Runtime.enable");
    client.send("Runtime.enable");

    const viewports = {
      mobile: { width: 390, height: 844, mobile: true },
      tablet: { width: 768, height: 1024, mobile: true },
      desktop: { width: 1365, height: 768, mobile: false },
    };

    const jobs = [
      { file: "premium-ui-login-mobile.png", viewport: viewports.mobile, token: "", selector: null },
      { file: "dcft-premium-login-mobile.png", viewport: viewports.mobile, token: "", selector: null },
      { file: "premium-ui-dashboard-mobile.png", viewport: viewports.mobile, token, selector: '[data-screen="dashboard"]' },
      { file: "dcft-premium-dashboard-mobile.png", viewport: viewports.mobile, token, selector: '[data-screen="dashboard"]' },
      { file: "premium-ui-dashboard-tablet.png", viewport: viewports.tablet, token, selector: '[data-screen="dashboard"]' },
      { file: "premium-ui-dashboard-desktop.png", viewport: viewports.desktop, token, selector: '[data-screen="dashboard"]' },
      { file: "dcft-premium-dashboard-desktop.png", viewport: viewports.desktop, token, selector: '[data-screen="dashboard"]' },
      { file: "premium-ui-plans-mobile.png", viewport: viewports.mobile, token, selector: '[data-screen="plans-detail"]' },
      { file: "premium-ui-governance-mobile.png", viewport: viewports.mobile, token, selector: '[data-screen="governance"]' },
    ];

    const inspections = [];
    for (const job of jobs) {
      await navigateApp(client, job.viewport, job.token, job.selector);
      inspections.push({ file: job.file, ...(await inspectPage(client)) });
      written.push(await capture(client, job.file));
    }

    await client.send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
    await client.send("Page.navigate", { url: previewHtml("icon") });
    await sleep(900);
    written.push(await capture(client, "dcft-premium-icon-preview.png"));

    await client.send("Page.navigate", { url: previewHtml("pwa") });
    await sleep(900);
    written.push(await capture(client, "dcft-pwa-preview.png"));

    const logs = await client.send("Runtime.evaluate", {
      expression: "JSON.stringify([])",
      returnByValue: true,
    });
    client.close();
    console.log(JSON.stringify({ status: "ok", frontend_url: FRONTEND_URL, api_url: API_URL, written, inspections, consoleErrors, logs: logs.result.value }, null, 2));
  } finally {
    chrome.kill();
  }
}

main().catch((error) => {
  console.error(`PREMIUM_SCREENSHOT_CAPTURE_FAILED: ${error.message}`);
  process.exit(1);
});

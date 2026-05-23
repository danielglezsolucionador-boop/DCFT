const fs = require("node:fs");
const path = require("node:path");
const { spawn } = require("node:child_process");

const FRONTEND_URL = process.env.DCFT_FRONTEND_URL || "http://127.0.0.1:5174/";
const API_URL = process.env.DCFT_STAGING_API_URL || "http://127.0.0.1:8200";
const CHROME_PATH = process.env.CHROME_PATH || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const OUT_DIR = path.resolve(process.cwd(), ".dcft", "state");
const PORT = Number(process.env.DCFT_CHROME_DEBUG_PORT || 9364);

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

async function createToken() {
  const unique = crypto.randomUUID().replaceAll("-", "").slice(0, 8);
  const response = await fetch(`${API_URL}/onboarding/tenants`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      tenant_name: `Phase 1 Premium ${unique}`,
      admin_username: `phase1_${unique}`,
      admin_password: "phase1-premium-pass-123",
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

async function navigate(client, viewport, token, selector) {
  await client.send("Emulation.setDeviceMetricsOverride", {
    width: viewport.width,
    height: viewport.height,
    deviceScaleFactor: 1,
    mobile: viewport.mobile,
  });
  await client.send("Page.navigate", { url: FRONTEND_URL });
  await sleep(900);
  const storage = token
    ? `localStorage.setItem("dcft_token", ${JSON.stringify(token)});`
    : "localStorage.removeItem('dcft_token');";
  await client.send("Runtime.evaluate", { expression: storage, returnByValue: true });
  await client.send("Page.reload", { ignoreCache: true });
  await sleep(1800);
  if (selector) {
    await client.send("Runtime.evaluate", {
      expression: `document.querySelector(${JSON.stringify(selector)})?.scrollIntoView({ block: "start" });`,
      returnByValue: true,
    });
    await sleep(500);
  } else {
    await client.send("Runtime.evaluate", { expression: "window.scrollTo(0, 0);", returnByValue: true });
    await sleep(300);
  }
}

async function capture(client, file) {
  const screenshot = await client.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
  const target = path.join(OUT_DIR, file);
  fs.writeFileSync(target, Buffer.from(screenshot.data, "base64"));
  return target;
}

async function inspect(client) {
  const result = await client.send("Runtime.evaluate", {
    expression: `JSON.stringify({
      width: document.documentElement.clientWidth,
      height: window.innerHeight,
      overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
      hasSemaforo: document.body.innerText.includes("Semáforo") || document.body.innerText.includes("Semaforo"),
      hasTributario: document.body.innerText.includes("Tributario"),
      hasFinanciero: document.body.innerText.includes("Financiero"),
      hasContable: document.body.innerText.includes("Contable"),
      hasOnboarding: document.body.innerText.includes("Activación premium")
    })`,
    returnByValue: true,
  });
  return JSON.parse(result.result.value);
}

async function main() {
  const chrome = spawn(CHROME_PATH, [
    "--headless=new",
    `--remote-debugging-port=${PORT}`,
    `--user-data-dir=${path.join(OUT_DIR, "chrome-phase1-profile")}`,
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

    const mobile = { width: 390, height: 844, mobile: true };
    const desktop = { width: 1365, height: 768, mobile: false };
    const jobs = [
      { file: "phase1-premium-login-mobile.png", viewport: mobile, token: "", selector: null },
      { file: "phase1-premium-dashboard-mobile.png", viewport: mobile, token, selector: '[data-screen="dashboard-principal"]' },
      { file: "phase1-premium-dashboard-desktop.png", viewport: desktop, token, selector: '[data-screen="dashboard-principal"]' },
      { file: "phase1-premium-semaforo-empresarial.png", viewport: mobile, token, selector: '[data-screen="semaforo-empresarial"]' },
      { file: "phase1-premium-estado-tributario.png", viewport: mobile, token, selector: '[data-screen="tributario"]' },
      { file: "phase1-premium-estado-financiero.png", viewport: mobile, token, selector: '[data-screen="financiero"]' },
      { file: "phase1-premium-estado-contable.png", viewport: mobile, token, selector: '[data-screen="contable"]' },
      { file: "phase1-premium-onboarding-premium.png", viewport: mobile, token: "", selector: '[data-screen="onboarding-premium"]' },
    ];

    const results = [];
    const written = [];
    for (const job of jobs) {
      await navigate(client, job.viewport, job.token, job.selector);
      results.push({ file: job.file, ...(await inspect(client)) });
      written.push(await capture(client, job.file));
    }

    client.close();
    console.log(JSON.stringify({ status: "ok", written, results }, null, 2));
  } finally {
    chrome.kill();
  }
}

main().catch((error) => {
  console.error(`PHASE1_PREMIUM_CAPTURE_FAILED: ${error.message}`);
  process.exit(1);
});

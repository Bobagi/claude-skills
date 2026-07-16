#!/usr/bin/env node
// frontend-review capture engine — project-agnostic.
// Drives a headless Chromium (Puppeteer) to screenshot a running page at several
// viewports and collect cheap, high-signal DOM/layout metrics that feed the
// UX/a11y/consistency pillar. No project-specific knowledge lives here.
//
// Usage:
//   node capture.mjs --base https://app.example.com --out ./out \
//     --viewports 390x844,768x1024,1280x900,1440x900 \
//     --routes "/:home,#/account:account,#/login:login" \
//     [--cookie "session=abc;other=def"] [--cookie-domain app.example.com] \
//     [--wait 1200] [--full true]
//
// Output: <out>/<label>__<WxH>.png for each route×viewport, plus <out>/manifest.json
// with the collected layout signals (horizontal overflow, off-canvas elements,
// images missing alt, controls without an accessible name, inputs without labels,
// tiny tap targets, console errors).

import { createRequire } from 'module';
import { existsSync, mkdirSync, writeFileSync, readFileSync } from 'fs';
import { execSync } from 'child_process';
import path from 'path';
import os from 'os';

// ---------- tiny arg parser ----------
function parseArgs(argv) {
  const a = {};
  for (let i = 0; i < argv.length; i++) {
    const t = argv[i];
    if (t.startsWith('--')) {
      const key = t.slice(2);
      const next = argv[i + 1];
      if (next === undefined || next.startsWith('--')) { a[key] = true; }
      else { a[key] = next; i++; }
    }
  }
  return a;
}
const args = parseArgs(process.argv.slice(2));
function fail(msg) { console.error('capture: ' + msg); process.exit(2); }

if (!args.base) fail('--base <url> is required');
const base = String(args.base).replace(/\/+$/, '');
const origin = (() => { try { return new URL(base).origin; } catch { return base; } })();
const host = (() => { try { return new URL(base).host; } catch { return ''; } })();
const outDir = path.resolve(String(args.out || './frontend-review-out'));
const extraWait = parseInt(args.wait || '1200', 10);
const fullPage = String(args.full ?? 'true') !== 'false';
// Also capture a viewport-only "above the fold" shot — full-page mobile shots get downscaled too far
// to judge fine padding/spacing. Set --fold false to skip.
const foldShot = String(args.fold ?? 'true') !== 'false';
// deviceScaleFactor: bump to 2 for crisp detail when judging tight spacing (larger files).
const scale = Math.max(1, parseInt(args.scale || '1', 10));

const viewports = String(args.viewports || '390x844,768x1024,1280x900,1440x900')
  .split(',').map(s => s.trim()).filter(Boolean)
  .map(s => { const [w, h] = s.split('x').map(Number); return { w, h, label: `${w}x${h}` }; });

// routes: "path[:label]" comma-separated. path may be "/", "/foo", "#/foo", "/#/foo".
const routes = String(args.routes || '/:home').split(',').map(s => s.trim()).filter(Boolean)
  .map(spec => {
    const i = spec.lastIndexOf(':');
    // avoid splitting on the ":" of a protocol — routes are paths, so a ":" is a label sep
    let route = spec, label = '';
    if (i > 0) { route = spec.slice(0, i); label = spec.slice(i + 1); }
    if (!label) label = (route.replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '') || 'home');
    let url;
    if (/^https?:\/\//.test(route)) url = route;
    else if (route.startsWith('#')) url = origin + '/' + route;          // hash route
    else url = origin + (route.startsWith('/') ? route : '/' + route);
    return { url, label };
  });

// ---------- resolve puppeteer-core ----------
function resolvePuppeteer() {
  const candidates = [];
  // 1) env override
  if (process.env.PUPPETEER_DIR) candidates.push(process.env.PUPPETEER_DIR);
  // 2) local node_modules of the project being reviewed (cwd) and of this skill
  candidates.push(process.cwd(), path.dirname(new URL(import.meta.url).pathname));
  // 3) npx caches (where an earlier `npx puppeteer` downloaded it)
  try {
    const npxRoot = path.join(os.homedir(), '.npm', '_npx');
    if (existsSync(npxRoot)) {
      for (const d of execSync(`ls ${npxRoot}`, { encoding: 'utf8' }).split('\n').filter(Boolean)) {
        candidates.push(path.join(npxRoot, d));
      }
    }
  } catch { /* ignore */ }
  for (const c of candidates) {
    try {
      const req = createRequire(c.endsWith('/') ? c : c + '/');
      const p = req('puppeteer-core');
      return p.default || p;
    } catch { /* try next */ }
    try {
      const req = createRequire(path.join(c, 'node_modules') + '/');
      const p = req('puppeteer-core');
      return p.default || p;
    } catch { /* try next */ }
  }
  fail('could not resolve puppeteer-core. Install it (npm i -D puppeteer-core) or set PUPPETEER_DIR to a dir that has it.');
}

// ---------- resolve a chrome binary ----------
function resolveChrome() {
  if (process.env.CHROME_PATH && existsSync(process.env.CHROME_PATH)) return process.env.CHROME_PATH;
  const globs = [
    path.join(os.homedir(), '.cache/ms-playwright/chromium-*/chrome-linux*/chrome'),
    path.join(os.homedir(), '.cache/puppeteer/chrome/*/chrome-linux*/chrome'),
    '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser',
  ];
  for (const g of globs) {
    try {
      const hit = execSync(`ls -1 ${g} 2>/dev/null | head -1`, { encoding: 'utf8' }).trim();
      if (hit && existsSync(hit)) return hit;
    } catch { /* ignore */ }
  }
  for (const bin of ['google-chrome', 'chromium', 'chromium-browser']) {
    try { const p = execSync(`which ${bin} 2>/dev/null`, { encoding: 'utf8' }).trim(); if (p) return p; } catch { /* ignore */ }
  }
  fail('could not find a Chrome/Chromium binary. Set CHROME_PATH=/path/to/chrome.');
}

// ---------- in-page metrics (runs in the browser) ----------
function collectSignals() {
  const vw = window.innerWidth, vh = window.innerHeight;
  const out = { overflowX: false, scrollWidth: document.documentElement.scrollWidth, viewportWidth: vw,
    offCanvas: [], missingAlt: [], unnamedControls: [], unlabeledInputs: [], tinyTargets: [] };
  out.overflowX = document.documentElement.scrollWidth > vw + 2;
  const desc = (el) => {
    const id = el.id ? '#' + el.id : '';
    const cls = (typeof el.className === 'string' && el.className) ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : '';
    const txt = (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 30);
    return `${el.tagName.toLowerCase()}${id}${cls}${txt ? ` "${txt}"` : ''}`;
  };
  // True when some ancestor scrolls/clips horizontally — then a child past the right edge is an
  // in-container scroller (wide table, carousel), NOT page overflow. Avoids false positives.
  const insideHScroller = (el) => {
    for (let p = el.parentElement; p && p !== document.documentElement; p = p.parentElement) {
      const ox = getComputedStyle(p).overflowX;
      if (ox === 'auto' || ox === 'scroll' || ox === 'hidden') return true;
    }
    return false;
  };
  const all = Array.from(document.body.querySelectorAll('*'));
  for (const el of all) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    // element extending past the right edge (a common responsiveness bug)
    if (r.right > vw + 2 && r.width <= vw + 4 && getComputedStyle(el).position !== 'fixed' && !insideHScroller(el)) {
      if (out.offCanvas.length < 25) out.offCanvas.push({ el: desc(el), right: Math.round(r.right), vw });
    }
  }
  for (const img of document.querySelectorAll('img')) {
    // alt="" é a marcação CORRETA de imagem decorativa (WAI) — só acusar quando
    // o atributo está realmente ausente
    if (!img.hasAttribute('alt') && img.getAttribute('role') !== 'presentation' && img.getAttribute('aria-hidden') !== 'true') {
      if (out.missingAlt.length < 25) out.missingAlt.push({ el: desc(img), src: (img.currentSrc || img.src || '').slice(-60) });
    }
  }
  const accName = (el) => (el.getAttribute('aria-label') || el.getAttribute('title') ||
    (el.textContent || '').trim() ||
    (el.querySelector('img') ? (el.querySelector('img').alt || '') : '')).trim();
  for (const el of document.querySelectorAll('button, a[href], [role="button"]')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    if (!accName(el)) { if (out.unnamedControls.length < 25) out.unnamedControls.push({ el: desc(el) }); }
    if ((r.width < 24 || r.height < 24)) { if (out.tinyTargets.length < 25) out.tinyTargets.push({ el: desc(el), w: Math.round(r.width), h: Math.round(r.height) }); }
  }
  for (const inp of document.querySelectorAll('input:not([type=hidden]), select, textarea')) {
    const r = inp.getBoundingClientRect(); if (r.width === 0 || r.height === 0) continue;
    const labelled = inp.getAttribute('aria-label') || inp.getAttribute('aria-labelledby') || inp.getAttribute('title') ||
      inp.getAttribute('placeholder') || (inp.id && document.querySelector(`label[for="${inp.id}"]`)) || inp.closest('label');
    if (!labelled) { if (out.unlabeledInputs.length < 25) out.unlabeledInputs.push({ el: desc(inp) }); }
  }
  return out;
}

// ---------- main ----------
const puppeteer = resolvePuppeteer();
const chrome = resolveChrome();
mkdirSync(outDir, { recursive: true });

const cookies = [];
if (args.cookie) {
  const dom = String(args['cookie-domain'] || host);
  for (const pair of String(args.cookie).split(';').map(s => s.trim()).filter(Boolean)) {
    const eq = pair.indexOf('=');
    if (eq > 0) cookies.push({ name: pair.slice(0, eq), value: pair.slice(eq + 1), domain: dom, path: '/' });
  }
}
let storageCookies = [];
if (args.storage && existsSync(String(args.storage))) {
  try { const s = JSON.parse(readFileSync(String(args.storage), 'utf8')); storageCookies = s.cookies || []; } catch { /* ignore */ }
}

console.log(`capture: chrome=${chrome}`);
console.log(`capture: base=${base}  routes=${routes.length}  viewports=${viewports.map(v => v.label).join(',')}  out=${outDir}`);

const browser = await puppeteer.launch({ executablePath: chrome, headless: 'new',
  args: ['--no-sandbox', '--disable-dev-shm-usage', '--force-color-profile=srgb'] });

const manifest = { base, generatedAt: new Date().toISOString(), shots: [], errors: [] };

// Run interaction actions before a shot — unlocks tabs, sub-tabs, modals, filled forms.
// Action shapes: {wait:ms} | {press:'Escape'} | {click:'css'} | {fill:'css',value:'x'} | {clickText:'Trade'} | {clickXY:[x,y]} (canvas apps: Flutter web, jogos)
async function applyActions(page, actions) {
  for (const a of (actions || [])) {
    try {
      if (a.wait != null) { await new Promise(r => setTimeout(r, Number(a.wait))); }
      else if (a.press) { await page.keyboard.press(String(a.press)); }
      else if (a.fill) { await page.click(a.fill, { clickCount: 3 }); await page.type(a.fill, String(a.value ?? '')); }
      else if (a.click) { await page.click(a.click); }
      else if (a.clickXY) { await page.mouse.click(Number(a.clickXY[0]), Number(a.clickXY[1])); }
      else if (a.evalJs) { await page.evaluate(a.evalJs); }
      else if (a.clickText) {
        const ok = await page.evaluate((txt) => {
          const norm = s => (s || '').replace(/\s+/g, ' ').trim().toLowerCase();
          const want = norm(txt);
          const els = Array.from(document.querySelectorAll('button, a, [role="tab"], [role="button"], .subtab, summary, label'));
          const hit = els.find(e => norm(e.textContent) === want) || els.find(e => norm(e.textContent).includes(want));
          if (hit) { hit.scrollIntoView({ block: 'center' }); hit.click(); return true; }
          return false;
        }, a.clickText);
        if (!ok) console.log(`    (clickText "${a.clickText}" not found)`);
      }
    } catch (e) { console.log(`    (action failed: ${JSON.stringify(a).slice(0, 60)})`); }
  }
}

// Capture one labelled state (a route, or a scenario after its actions run).
async function capturePage({ label, url, vp, actions, full }) {
  const page = await browser.newPage();
  const consoleErrors = [];
  page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text().slice(0, 200)); });
  page.on('pageerror', e => consoleErrors.push(String(e).slice(0, 200)));
  await page.setViewport({ width: vp.w, height: vp.h, deviceScaleFactor: scale });
  const allCookies = [...cookies, ...storageCookies];
  if (allCookies.length) { try { await page.setCookie(...allCookies); } catch { /* ignore */ } }
  const wantFull = full != null ? full : fullPage;
  const file = path.join(outDir, `${label}__${vp.label}.png`);
  try {
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 35000 });
    await new Promise(r => setTimeout(r, extraWait));
    if (actions && actions.length) { await applyActions(page, actions); await new Promise(r => setTimeout(r, 600)); }
    const signals = await page.evaluate(collectSignals);
    await page.screenshot({ path: file, fullPage: wantFull });
    let foldFile = null;
    if (foldShot && wantFull) {
      foldFile = path.join(outDir, `${label}__${vp.label}__fold.png`);
      await page.screenshot({ path: foldFile, fullPage: false });
    }
    manifest.shots.push({ label, viewport: vp.label, url,
      file: path.basename(file), fold: foldFile ? path.basename(foldFile) : null, consoleErrors, signals });
    const flags = [];
    if (signals.overflowX) flags.push('H-OVERFLOW');
    if (signals.offCanvas.length) flags.push(`offcanvas:${signals.offCanvas.length}`);
    if (signals.missingAlt.length) flags.push(`alt:${signals.missingAlt.length}`);
    if (signals.unnamedControls.length) flags.push(`unnamed:${signals.unnamedControls.length}`);
    if (signals.unlabeledInputs.length) flags.push(`nolabel:${signals.unlabeledInputs.length}`);
    if (signals.tinyTargets.length) flags.push(`tiny:${signals.tinyTargets.length}`);
    if (consoleErrors.length) flags.push(`console:${consoleErrors.length}`);
    console.log(`  ✓ ${label} @ ${vp.label}${flags.length ? '  [' + flags.join(' ') + ']' : ''}`);
  } catch (e) {
    manifest.errors.push({ label, viewport: vp.label, error: String(e).slice(0, 200) });
    console.log(`  ✗ ${label} @ ${vp.label}: ${String(e).slice(0, 120)}`);
  } finally { await page.close(); }
}

// Optional scenarios file: [{label, url?, viewport?, actions?, full?}] for tabs/modals/sub-tabs/states.
let scenarios = [];
if (args.scenarios && existsSync(String(args.scenarios))) {
  try { scenarios = JSON.parse(readFileSync(String(args.scenarios), 'utf8')); }
  catch (e) { fail('bad --scenarios json: ' + e); }
}
const toUrl = (u) => !u ? base : (/^https?:/.test(u) ? u : (u.startsWith('#') ? origin + '/' + u : origin + (u.startsWith('/') ? u : '/' + u)));

try {
  if (String(args['scenarios-only'] ?? 'false') !== 'true') {
    for (const vp of viewports) for (const route of routes) await capturePage({ label: route.label, url: route.url, vp });
  }
  for (const sc of scenarios) {
    const [sw, sh] = String(sc.viewport || viewports[0].label).split('x').map(Number);
    const vp = { w: sw, h: sh, label: sc.viewport || viewports[0].label };
    await capturePage({ label: sc.label, url: toUrl(sc.url), vp, actions: sc.actions, full: sc.full });
  }
} finally { await browser.close(); }

writeFileSync(path.join(outDir, 'manifest.json'), JSON.stringify(manifest, null, 2));
console.log(`capture: wrote ${manifest.shots.length} screenshots + manifest.json to ${outDir}`);

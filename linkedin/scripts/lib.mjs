// Shared plumbing for every li.mjs subcommand.
// Everything here exists to make LinkedIn automation cheap in tokens:
// one browser connection, deduped text, compact stdout, bulk data to files.
import { chromium } from 'playwright';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { dirname, join, resolve } from 'path';
import { fileURLToPath } from 'url';

export const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
export const OUT = join(ROOT, '.out');

export const cfg = (() => {
  const f = join(ROOT, 'config.json');
  const d = { profileUrl: 'https://www.linkedin.com/in/me', cdp: 'http://localhost:9222', locale: 'pt' };
  if (!existsSync(f)) return d;
  return { ...d, ...JSON.parse(readFileSync(f, 'utf8')) };
})();

export const BASE = cfg.profileUrl.replace(/\/+$/, '');
export const url = (p = '') => BASE + '/' + p.replace(/^\/+/, '');

// Both UI languages in one regex: the profile can be switched to English and
// every aria-label changes with it. Matching both costs nothing and avoids a
// whole class of "worked yesterday, fails today" breakage.
export const RX = {
  save: /^(Salvar|Save)$/,
  add: /^(Adicionar|Add)$/,
  editIntro: /^(Editar perfil|Edit intro)$/,
  editAbout: /^(Editar sobre|Edit about)$/,
  contactInfo: /(Dados de contato|Contact info)/i,
  addLink: /(Adicionar link|Add link)/i,
  addSection: /(Adicionar seção|Add profile section)/i,
  addMedia: /(Adicionar conteúdo de mídia|Add media)/i,
};

export const SECTIONS = {
  main: '/',
  experience: '/details/experience/',
  education: '/details/education/',
  skills: '/details/skills/',
  projects: '/details/projects/',
  featured: '/details/featured/',
  languages: '/details/languages/',
  certifications: '/details/certifications/',
  courses: '/details/courses/',
  honors: '/details/honors/',
  volunteering: '/details/volunteering-experiences/',
  recommendations: '/details/recommendations/',
  publications: '/details/publications/',
  contact: '/overlay/contact-info/',
};

export const LANG_LEVEL = {
  elementary: 'LanguageProficiency_ELEMENTARY',
  limited: 'LanguageProficiency_LIMITED_WORKING',
  professional: 'LanguageProficiency_PROFESSIONAL_WORKING',
  advanced: 'LanguageProficiency_FULL_PROFESSIONAL',
  native: 'LanguageProficiency_NATIVE_OR_BILINGUAL',
};

// ---------------------------------------------------------------- browser

let _browser = null;
let _page = null;

export async function connect() {
  if (_page) return _page;
  try {
    _browser = await chromium.connectOverCDP(cfg.cdp, { timeout: 8000 });
  } catch {
    die(2, 'CHROME_DOWN — inicie:\n  chrome.exe --remote-debugging-port=9222 --user-data-dir=' + join(ROOT, 'chrome-profile'));
  }
  const ctx = _browser.contexts()[0];
  _page = ctx.pages().find(p => p.url().includes('linkedin.com')) ?? ctx.pages()[0] ?? await ctx.newPage();
  return _page;
}

export async function done(code = 0) {
  try { await _browser?.close(); } catch {}
  process.exit(code);
}

export function die(code, msg) {
  console.log(msg);
  process.exit(code);
}

/** Navigate + settle. `wait` is the post-load grace for LinkedIn's client render. */
export async function go(path, wait = 2800) {
  const p = await connect();
  await p.goto(path.startsWith('http') ? path : url(path), { waitUntil: 'domcontentloaded', timeout: 45000 });
  await p.waitForTimeout(wait);
  if (/\/(login|authwall|checkpoint|uas)\b/.test(p.url())) {
    die(2, 'NOT_LOGGED_IN — abra o Chrome de debug e faça login uma vez (a sessão persiste no user-data-dir).');
  }
  return p;
}

/**
 * Scroll so lazy/virtualized content renders.
 *
 * On several /details/ pages the window does NOT scroll — `<main>` is itself
 * the scroll container (document.scrollHeight stays at viewport height).
 * Scrolling the window there is a silent no-op and you read a truncated list,
 * which is exactly why skills used to under-count. Always drive whichever
 * element actually overflows.
 */
export async function scrollAll(p) {
  await p.evaluate(async () => {
    const m = document.querySelector('main');
    const el = (m && m.scrollHeight > m.clientHeight + 50) ? m : null;
    for (let i = 0; i < 10; i++) {
      if (el) el.scrollTop += el.clientHeight; else window.scrollBy(0, window.innerHeight);
      await new Promise(r => setTimeout(r, 130));
    }
    if (el) el.scrollTop = 0; else window.scrollTo(0, 0);
  });
  await p.waitForTimeout(400);
}

// ---------------------------------------------------------------- text

/**
 * LinkedIn renders every label twice (once visible, once for screen readers),
 * so a raw innerText dump is ~2x the tokens it needs to be. Dropping a line
 * that repeats the line before it removes the duplication without touching
 * legitimately repeated content further apart.
 */
export function dedupeLines(s) {
  const out = [];
  for (const raw of (s || '').replace(/\r/g, '').split('\n')) {
    const line = raw.trim();
    if (!line) continue;
    if (out.length && out[out.length - 1] === line) continue;
    out.push(line);
  }
  return out.join('\n');
}

const NOISE = [
  'Quem seus visitantes também viram', 'Pessoas também visualizaram', 'People also viewed',
  'Outros perfis semelhantes', 'Explore os principais artigos', 'Explore collaborative articles',
];

export function cleanText(s) {
  let t = dedupeLines(s);
  for (const n of NOISE) t = t.split(n)[0];
  return t.trim();
}

export const oneLine = (s, n = 160) => (s || '').replace(/\s+/g, ' ').trim().slice(0, n);

/**
 * The entries of a /details/<section>/ page, as { label, text }.
 *
 * LinkedIn stopped using <ul>/<li> for these lists — they are anonymous divs
 * with obfuscated classes, so there is nothing structural to select. The one
 * stable per-entry handle on your OWN profile is the edit pencil: every entry
 * has exactly one, and its aria-label names the entry.
 *
 * Pages like /details/skills/ are virtualized, so we scroll until the pencil
 * count stops growing instead of taking one pass (which under-counts badly).
 */
export async function entries(p) {
  // Virtualized lists DESTROY off-screen rows, so a single sweep at the end
  // undercounts just as badly as not scrolling. Harvest on every step instead
  // and accumulate, keyed by label.
  const harvest = () => p.evaluate(() => {
    const isPencil = (e) => /^(Editar|Edit )/i.test(e.getAttribute('aria-label') || '')
      && !/idioma do perfil|profile language/i.test(e.getAttribute('aria-label'));
    return [...document.querySelectorAll('main [aria-label]')].filter(isPencil).map(el => {
      // climb to the widest ancestor that still wraps this entry alone
      let node = el;
      while (node.parentElement && node.parentElement.tagName !== 'MAIN') {
        const up = node.parentElement;
        if ([...up.querySelectorAll('[aria-label]')].filter(isPencil).length > 1) break;
        node = up;
      }
      return { label: el.getAttribute('aria-label'), text: node.innerText || '' };
    });
  });

  // Labels are NOT unique — every language row is literally "Editar idioma" —
  // so key on label + a slice of the row text, then merge rows whose text is
  // just a shorter render of the same row (virtualization hydrates gradually).
  const norm = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const seen = new Map();
  const soak = (rows) => rows.forEach(r => {
    const key = r.label + '||' + norm(r.text).slice(0, 25);
    const cur = seen.get(key);
    if (!cur || r.text.length > cur.text.length) seen.set(key, r);
  });

  soak(await harvest());
  let stagnant = 0;
  for (let i = 0; i < 30 && stagnant < 3; i++) {
    const before = seen.size;
    const moved = await p.evaluate(() => {
      const m = document.querySelector('main');
      const el = (m && m.scrollHeight > m.clientHeight + 50) ? m : null;
      if (el) { const b = el.scrollTop; el.scrollTop += el.clientHeight * 0.9; return el.scrollTop !== b; }
      const b = window.scrollY; window.scrollBy(0, window.innerHeight * 0.9); return window.scrollY !== b;
    });
    await p.waitForTimeout(450);
    soak(await harvest());
    stagnant = (!moved || seen.size === before) ? stagnant + 1 : 0;
  }
  await p.evaluate(() => { const m = document.querySelector('main'); if (m) m.scrollTop = 0; window.scrollTo(0, 0); });

  // collapse partial renders: same label + one text contained in the other
  const out = [];
  for (const r of seen.values()) {
    const dup = out.find(o => o.label === r.label
      && (norm(o.text).startsWith(norm(r.text).slice(0, 20)) || norm(r.text).startsWith(norm(o.text).slice(0, 20))));
    if (dup) { if (r.text.length > dup.text.length) dup.text = r.text; continue; }
    out.push({ ...r });
  }
  return out.map(e => ({ label: e.label, text: dedupeLines(e.text).replace(/\n/g, ' | ').trim() }));
}

// ---------------------------------------------------------------- files

export function outFile(name, data) {
  mkdirSync(OUT, { recursive: true });
  const f = join(OUT, name);
  writeFileSync(f, typeof data === 'string' ? data : JSON.stringify(data, null, 2), 'utf8');
  return f;
}

export async function shot(p, name) {
  mkdirSync(OUT, { recursive: true });
  const f = join(OUT, name.endsWith('.png') ? name : name + '.png');
  await p.screenshot({ path: f }).catch(() => {});
  return f;
}

// ---------------------------------------------------------------- editing

/**
 * Empty a contenteditable rich-text box and PROVE it is empty.
 *
 * This is the single most dangerous operation in the whole skill. Ctrl+A +
 * Delete fails silently on these boxes; when it does, the new text is appended
 * to the old one, which blows past the field limit and loses the save. So we
 * try three strategies and hard-abort if the box still has content.
 */
export async function clearRichText(p, field) {
  const read = async () => (await field.innerText().catch(() => '')).trim();
  const strategies = [
    async () => { await field.fill(''); },
    async () => {
      await field.click();
      await p.waitForTimeout(250);
      await p.keyboard.press('ControlOrMeta+End');
      await p.keyboard.press('ControlOrMeta+Shift+Home');
      await p.keyboard.press('Delete');
    },
    async () => { await field.fill(''); },
  ];
  for (const s of strategies) {
    await s().catch(() => {});
    await p.waitForTimeout(500);
    if (!(await read())) { await field.click(); return true; }
  }
  return false;
}

/**
 * Typeahead inputs that accept free text (job title, degree, field of study).
 * click()/fill() fail because the dropdown listbox eats the pointer, so drive
 * it from the keyboard and dismiss the dropdown with Escape.
 */
export async function typeFree(p, input, value) {
  await input.focus();
  await p.keyboard.press('ControlOrMeta+A');
  await p.keyboard.press('Delete');
  await p.waitForTimeout(250);
  await p.keyboard.type(value, { delay: 35 });
  await p.waitForTimeout(500);
  await p.keyboard.press('Escape');
  await p.waitForTimeout(300);
}

/** Wait until an edit form is really hydrated — a blank form saved = data loss. */
export async function waitHydrated(p, kind = 'year') {
  const fn = {
    // experience/education: a date <select> must already carry a real year
    year: () => {
      const d = document.querySelector('dialog[open]');
      return !!d && [...d.querySelectorAll('select')].some(s => /^(19|20)\d\d$/.test(s.value));
    },
    // intro: the textbox must already carry the current value
    text: () => {
      const e = document.querySelector('dialog[open] [role="textbox"]');
      return !!e && (e.innerText || '').trim().length > 5;
    },
    // any input with a real value
    input: () => {
      const d = document.querySelector('dialog[open]');
      return !!d && [...d.querySelectorAll('input')].some(i => (i.value || '').length > 3);
    },
  }[kind];
  await p.waitForFunction(fn, null, { timeout: 30000 });
  await p.waitForTimeout(800);
}

/** Click the Salvar/Save button of the open dialog. */
export async function clickSave(p) {
  await p.getByRole('button', { name: RX.save }).first().click({ timeout: 10000 });
  await p.waitForTimeout(4000);
}

/** Reload the section and assert the new text is actually there. */
export async function verify(path, probe) {
  const p = await go(path, 3000);
  const txt = (await p.locator('main, dialog[open]').first().innerText().catch(() => '')).replace(/\s+/g, ' ');
  const needle = String(probe).replace(/\s+/g, ' ').slice(0, 60);
  return txt.includes(needle);
}

// ---------------------------------------------------------------- args

export function parseArgs(argv) {
  const flags = {};
  const rest = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const [k, v] = a.slice(2).split('=');
      flags[k] = v ?? (argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[++i] : true);
    } else rest.push(a);
  }
  return { flags, rest };
}

export const readText = (f) => readFileSync(f, 'utf8').replace(/\r\n/g, '\n').trimEnd();

#!/usr/bin/env node
// Single entry point for reading and editing the LinkedIn profile.
// Design rules:
//   1. Every command prints a handful of lines. Bulk data goes to .out/ and is
//      read from disk only when actually needed.
//   2. Writes are dry-run by default. --commit is the only thing that saves.
//   3. A commit always re-reads the page from scratch and asserts the change.
import {
  connect, go, done, die, url, BASE, SECTIONS, RX, LANG_LEVEL,
  cleanText, oneLine, outFile, shot, scrollAll, entries,
  clearRichText, typeFree, waitHydrated, clickSave, verify,
  parseArgs, readText,
} from './lib.mjs';

const { flags, rest } = parseArgs(process.argv.slice(2));
const cmd = rest.shift();
const COMMIT = !!flags.commit;
const MODE = COMMIT ? 'commit' : 'preview';

const LIMITS = { headline: 220, about: 2600, expDesc: 2000, projDesc: 2000 };

const ok = (m) => console.log('OK ' + m);
const info = (m) => console.log(m);

// ------------------------------------------------------------------ doctor

/**
 * Name/headline/metrics straight off the profile text.
 * The old class-based selectors (div.text-body-medium.break-words) rot every
 * time LinkedIn reships its CSS; the first two lines of `main` do not.
 */
async function readIntro(p) {
  const lines = cleanText(await p.locator('main').first().innerText().catch(() => '')).split('\n');
  const grab = (rx) => { const l = lines.find(x => rx.test(x)); return l ? Number(l.match(/[\d.]+/)?.[0].replace('.', '')) : null; };
  return {
    name: lines[0] || '',
    headline: lines[1] || '',
    location: lines[2] || '',
    views: grab(/visualiza(ções|coes) do perfil|profile views/i),
    searches: grab(/ocorrências em resultados de pesquisa|search appearances/i),
    impressions: grab(/impress(ão|ao|ions)/i),
    connections: grab(/conex(ões|oes)|connections/i),
  };
}

async function doctor() {
  const p = await go('/', 3000);
  const i = await readIntro(p);
  info('chrome  : up (' + BASE + ')');
  info('login   : ok');
  info('name    : ' + i.name);
  info('headline: ' + i.headline.length + '/' + LIMITS.headline + ' chars');
  await done();
}

/** The numbers that actually track recruiter reach. Run before/after changes. */
async function stats() {
  const p = await go('/', 3200);
  const i = await readIntro(p);
  info('views(90d)      : ' + i.views);
  info('search appear.  : ' + i.searches);
  info('impressions(7d) : ' + i.impressions);
  info('connections     : ' + i.connections);
  info('headline        : ' + i.headline.length + '/' + LIMITS.headline);
  outFile('stats.json', i);
  await done();
}

// -------------------------------------------------------------------- read

const DEFAULT_SECTIONS = ['main', 'experience', 'education', 'skills', 'projects', 'featured', 'languages', 'certifications', 'contact'];

async function read() {
  const want = flags.sections ? String(flags.sections).split(',').map(s => s.trim()) : DEFAULT_SECTIONS;
  const cap = Number(flags.max || 2000);
  const result = {};
  let txt = '';
  for (const key of want) {
    const path = SECTIONS[key];
    if (!path) { info(key.padEnd(15) + 'UNKNOWN SECTION'); continue; }
    try {
      const p = await go(path, 2600);
      await scrollAll(p);
      const landed = p.url();
      // a section with nothing in it bounces back to the profile page
      const empty = key !== 'main' && !/\/details\/|\/overlay\//.test(landed);
      const scope = landed.includes('/overlay/') ? 'dialog[open]' : 'main';
      const body = empty ? '' : cleanText(await p.locator(scope).first().innerText().catch(() => ''));
      result[key] = { empty, chars: body.length, text: body.slice(0, cap) };
      txt += '=== ' + key.toUpperCase() + (empty ? ' [VAZIA]' : '') + ' ===\n' + (body.slice(0, cap) || '(sem dados)') + '\n\n';
      info(key.padEnd(15) + (empty ? 'vazia' : body.length + ' chars'));
    } catch (e) {
      result[key] = { error: e.message.split('\n')[0].slice(0, 80) };
      info(key.padEnd(15) + 'ERRO: ' + result[key].error);
    }
  }
  outFile('profile.json', result);
  const f = outFile('profile.txt', txt);
  info('\n-> ' + f + '  (leia este arquivo; nao redirecione stdout)');
  await done();
}

async function get() {
  const key = rest[0];
  const path = SECTIONS[key];
  if (!path) die(1, 'secoes: ' + Object.keys(SECTIONS).join(', '));
  const p = await go(path, 2600);
  await scrollAll(p);
  const scope = p.url().includes('/overlay/') ? 'dialog[open]' : 'main';
  const body = cleanText(await p.locator(scope).first().innerText().catch(() => ''));
  console.log(body.slice(0, Number(flags.max || 3000)));
  await done();
}

/** aria-labels of every edit pencil — the only reliable handle for edit commands. */
async function pencils() {
  const key = rest[0] || 'experience';
  const p = await go(SECTIONS[key] || SECTIONS.experience, 2800);
  const labels = await p.evaluate(() =>
    [...document.querySelectorAll('main a[aria-label], main button[aria-label]')]
      .map(e => e.getAttribute('aria-label'))
      .filter(l => /Editar|Edit /i.test(l)));
  labels.forEach(l => console.log(l));
  await done();
}

// ------------------------------------------------------------ intro fields

async function setText() {
  const target = rest[0]; // headline | about
  if (!['headline', 'about'].includes(target)) die(1, 'uso: set-text <headline|about> --file F [--commit]');
  const text = readText(flags.file);
  const limit = target === 'headline' ? LIMITS.headline : LIMITS.about;
  // the field's own counter charges ~1 extra per line break, so keep a margin
  const budget = limit - (text.split('\n').length - 1) - 3;
  if (text.length > budget) die(1, `ABORT: ${text.length} chars, cabe ${budget} (limite ${limit} contando quebras de linha)`);

  const p = await go('/', 3000);
  await p.getByRole('link', { name: target === 'headline' ? RX.editIntro : RX.editAbout }).first().click({ timeout: 12000 });
  const field = p.locator('dialog[open] [role="textbox"]').first();
  await field.waitFor({ state: 'visible', timeout: 20000 });
  if (target === 'headline') await waitHydrated(p, 'text'); else await p.waitForTimeout(2500);

  const before = (await field.innerText().catch(() => '')).trim();
  info('before: ' + before.length + ' chars');
  await field.scrollIntoViewIfNeeded();
  if (!await clearRichText(p, field)) { await shot(p, target + '-abort'); die(3, 'ABORT: campo nao ficou vazio — nao digitei nada (risco de concatenar).'); }

  await p.keyboard.insertText(text);
  await p.waitForTimeout(1000);
  const after = (await field.innerText().catch(() => '')).trim();
  info('after : ' + after.length + ' chars');
  if (after.length < text.length * 0.9) info('WARN: texto parece truncado no campo');
  info('shot  : ' + await shot(p, `${target}-${MODE}`));

  if (!COMMIT) { info('PREVIEW (nada salvo)'); return done(); }
  await clickSave(p);
  ok(await verify('/', text.slice(0, 50)) ? 'salvo e verificado' : 'SALVO? readback nao encontrou o texto — confira');
  await done();
}

// -------------------------------------------------------------- experience

/** Open an entry's edit form by clicking its pencil (never by URL — that renders blank). */
async function openEntry(sectionKey, match) {
  const p = await go(SECTIONS[sectionKey], 3000);
  const label = await p.evaluate((m) => {
    const rx = new RegExp(m, 'i');
    const e = [...document.querySelectorAll('main a[aria-label], main button[aria-label]')]
      .filter(x => /Editar|Edit /i.test(x.getAttribute('aria-label')))
      .find(x => rx.test(x.getAttribute('aria-label')));
    return e ? e.getAttribute('aria-label') : null;
  }, match);
  if (!label) die(3, 'ABORT: nenhum lapis casa com /' + match + '/i — rode: li.mjs pencils ' + sectionKey);
  info('entry : ' + label);
  await p.getByRole('link', { name: label, exact: true }).first().click({ timeout: 12000 })
    .catch(async () => { await p.getByRole('button', { name: label, exact: true }).first().click({ timeout: 12000 }); });
  return p;
}

async function setExpDesc() {
  const text = readText(flags.file);
  if (text.length > LIMITS.expDesc - 30) die(1, `ABORT: ${text.length} chars (limite seguro ${LIMITS.expDesc - 30})`);
  const p = await openEntry('experience', flags.match);
  await waitHydrated(p, 'year');

  const desc = p.locator('dialog[open] [role="textbox"]').first();
  await desc.waitFor({ state: 'visible', timeout: 15000 });
  await desc.scrollIntoViewIfNeeded();
  info('before: ' + ((await desc.innerText().catch(() => '')).trim().length) + ' chars');
  if (!await clearRichText(p, desc)) { await shot(p, 'exp-abort'); die(3, 'ABORT: campo nao ficou vazio.'); }
  await p.keyboard.insertText(text);
  await p.waitForTimeout(1000);
  info('after : ' + ((await desc.innerText().catch(() => '')).trim().length) + ' chars');
  info('shot  : ' + await shot(p, 'exp-' + MODE));

  if (!COMMIT) { info('PREVIEW (nada salvo)'); return done(); }
  await clickSave(p);
  ok(await verify(SECTIONS.experience, text.slice(0, 60)) ? 'salvo e verificado' : 'SALVO? readback nao confirmou');
  await done();
}

async function setExpTitle() {
  const { match, value } = flags;
  const p = await openEntry('experience', match);
  await waitHydrated(p, 'year');
  // Locate the title input BY ITS CURRENT VALUE. The form also contains the
  // profile headline field; editing the wrong one silently rewrites the headline.
  const inputs = await p.locator('dialog[open] input[type="text"], dialog[open] input:not([type])').all();
  let target = null;
  for (const inp of inputs) {
    const v = (await inp.inputValue().catch(() => '')).trim();
    if (v && new RegExp(String(flags.current || match), 'i').test(v) && v.length < 120) { target = inp; break; }
  }
  if (!target) { await shot(p, 'title-abort'); die(3, 'ABORT: nao achei o input do cargo — passe --current "<valor exato atual>"'); }
  info('before: ' + JSON.stringify(await target.inputValue()));
  await typeFree(p, target, value);
  info('after : ' + JSON.stringify(await target.inputValue()));
  info('shot  : ' + await shot(p, 'title-' + MODE));
  if (!COMMIT) { info('PREVIEW (nada salvo)'); return done(); }
  await clickSave(p);
  ok(await verify(SECTIONS.experience, value) ? 'salvo e verificado' : 'SALVO? readback nao confirmou');
  await done();
}

async function setEdu() {
  const p = await openEntry('education', flags.match);
  await waitHydrated(p, 'input');
  for (const [flag, rx] of [['degree', /^Diploma$|^Degree$/], ['field', /Área de estudo|Field of study/]]) {
    if (!flags[flag]) continue;
    const loc = p.getByLabel(rx).first();
    await loc.waitFor({ state: 'visible', timeout: 10000 });
    const before = await loc.inputValue();
    await typeFree(p, loc, flags[flag]);
    info(flag + ': ' + JSON.stringify(before) + ' -> ' + JSON.stringify(await loc.inputValue()));
  }
  info('shot  : ' + await shot(p, 'edu-' + MODE));
  if (!COMMIT) { info('PREVIEW (nada salvo)'); return done(); }
  await clickSave(p);
  ok(await verify(SECTIONS.education, flags.degree || flags.field) ? 'salvo e verificado' : 'SALVO? readback nao confirmou');
  await done();
}

// ------------------------------------------------------------------ skills

async function addSkill() {
  const skills = rest;
  if (!skills.length) die(1, 'uso: add-skill "TypeScript" "Docker" [--commit]');
  const open = async () => {
    const p = await go('/', 2500);
    // a "Try Premium" banner intercepts pointer events on this link, so click it in-page
    await p.evaluate((rx) => {
      const a = [...document.querySelectorAll('main a')].find(e => new RegExp(rx, 'i').test(e.innerText || ''));
      a?.click();
    }, RX.addSection.source);
    await p.waitForTimeout(2500);
    // "Principal / Recomendado / Adicionais" are collapsed role=button accordions
    await p.evaluate(() => {
      const el = [...document.querySelectorAll('dialog[open] [role="button"]')]
        .find(e => /^(Principal|Core)$/.test((e.innerText || '').trim()));
      el?.click();
    });
    await p.waitForTimeout(1200);
    await p.evaluate(() => {
      const el = [...document.querySelectorAll('dialog[open] a, dialog[open] button')]
        .find(e => /Adicionar competências|Add skills/i.test(e.innerText || ''));
      el?.click();
    });
    await p.waitForTimeout(2500);
    return p;
  };

  const saved = [], dup = [], failed = [];
  for (const skill of skills) {
    try {
      const p = await open();
      const input = p.locator('dialog[open] input[type="text"], dialog[open] input:not([type])').first();
      await input.waitFor({ state: 'visible', timeout: 15000 });
      await input.click(); await input.fill('');
      await input.pressSequentially(skill, { delay: 60 });
      await p.waitForTimeout(1800);
      // this typeahead REQUIRES picking a suggestion; typed-only text is rejected
      const esc = skill.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      let opt = p.getByRole('option', { name: skill, exact: true }).first();
      if (!(await opt.isVisible().catch(() => false))) opt = p.getByRole('option', { name: new RegExp('^' + esc, 'i') }).first();
      if (!(await opt.isVisible().catch(() => false))) opt = p.locator('[role="option"]').first();
      await opt.waitFor({ state: 'visible', timeout: 6000 });
      const picked = (await opt.innerText().catch(() => skill)).split('\n')[0].trim();
      await opt.click();
      await p.waitForTimeout(700);
      if (!COMMIT) { info('PREVIEW ' + skill + ' -> "' + picked + '"'); continue; }
      await clickSave(p);
      // /details/skills/ is virtualized, so readback lies. LinkedIn's own duplicate
      // toast is the only trustworthy signal — it needs a few seconds to appear.
      await p.waitForTimeout(2500);
      const outcome = await p.evaluate(() => {
        const t = document.body.innerText || '';
        if (/já está no seu perfil|already on your profile/i.test(t)) return 'dup';
        if (!document.querySelector('dialog[open]')) return 'saved';
        return 'open:' + [...document.querySelectorAll('[role="alert"]')].map(e => e.innerText).join(' ').slice(0, 60);
      });
      if (outcome === 'saved') { saved.push(picked); info('SAVED ' + picked); }
      else if (outcome === 'dup') { dup.push(skill); info('DUP   ' + skill); }
      else { failed.push(skill); info('FAIL  ' + skill + ' :: ' + outcome); }
    } catch (e) {
      failed.push(skill); info('FAIL  ' + skill + ' :: ' + e.message.split('\n')[0].slice(0, 60));
    }
  }
  if (COMMIT) info(`\nsaved=${saved.length} dup=${dup.length} fail=${failed.length}` + (failed.length ? ' -> ' + JSON.stringify(failed) : ''));
  await done();
}

// --------------------------------------------------------------- languages

async function addLanguage() {
  const [name, levelKey] = rest;
  const level = LANG_LEVEL[levelKey] || levelKey;
  if (!name || !level) die(1, 'uso: add-language "Inglês" advanced|native|professional|limited|elementary [--commit]');
  const p = await go(SECTIONS.languages, 2500);
  let clicked = false;
  for (const role of ['button', 'link']) {
    if (clicked) break;
    try { await p.getByRole(role, { name: /Adicionar.*idioma|Add.*language/i }).first().click({ timeout: 4000 }); clicked = true; } catch {}
  }
  if (!clicked) die(2, 'FAIL: nao achei o botao de adicionar idioma');
  const input = p.locator('input[aria-label="Idioma*"], input[aria-label="Language*"]').first();
  await input.waitFor({ state: 'visible', timeout: 15000 });
  await input.click(); await input.fill('');
  // suggestions come in the UI language: "Inglês", not "English"
  await input.pressSequentially(name, { delay: 70 });
  await p.waitForTimeout(1500);
  const opt = p.getByRole('option', { name, exact: true }).first();
  await opt.waitFor({ state: 'visible', timeout: 8000 });
  await opt.click();
  await p.waitForTimeout(400);
  await p.locator('select:has(option[value^="LanguageProficiency_"])').first().selectOption(level);
  info('filled: ' + name + ' / ' + level);
  info('shot  : ' + await shot(p, 'lang-' + MODE));
  if (!COMMIT) { info('PREVIEW (nada salvo)'); return done(); }
  await clickSave(p);
  ok(await verify(SECTIONS.languages, name) ? 'salvo e verificado' : 'SALVO? readback nao confirmou');
  await done();
}

// ------------------------------------------------------- featured / project

async function addFeatured() {
  const link = rest[0];
  if (!link) die(1, 'uso: add-featured <url> [--title "T"] [--commit]');
  const p = await go(SECTIONS.featured, 3200);
  let opened = false;
  for (const rx of [/Menu de estouro em destaque/i, /Adicionar destaque/i, /Add featured/i, /^(Adicionar|Add)$/i]) {
    if (opened) break;
    try { await p.getByRole('button', { name: rx }).first().click({ timeout: 4000 }); opened = true; } catch {}
  }
  await p.waitForTimeout(1500);
  await p.getByRole('menuitem', { name: RX.addLink }).first().click({ timeout: 8000 });
  const urlInput = p.locator('dialog[open] input[type="text"], dialog[open] input:not([type])').first();
  await urlInput.waitFor({ state: 'visible', timeout: 20000 });
  await urlInput.fill(link);
  await p.waitForTimeout(700);
  await p.getByRole('button', { name: RX.add }).first().click({ timeout: 8000 });
  // LinkedIn fetches the link preview async (~9-12s) and only then fills the
  // required Título* and enables Salvar. Wait on the button, never on a timeout.
  try {
    await p.waitForFunction(() => {
      const d = document.querySelector('dialog[open]');
      const s = d && [...d.querySelectorAll('button')].find(b => /^(Salvar|Save)$/.test((b.innerText || '').trim()));
      return s && !s.disabled;
    }, null, { timeout: 45000 });
  } catch {
    await shot(p, 'featured-abort');
    die(3, 'ABORT: preview do link nao carregou. O fetcher e instavel — repita o comando (subdominio funciona melhor com barra final).');
  }
  const titleInput = p.locator('dialog[open] input').nth(1);
  let title = await titleInput.inputValue().catch(() => '');
  if (!title.trim()) {
    if (!flags.title) die(3, 'ABORT: Título* vazio e nenhum --title passado');
    await titleInput.fill(String(flags.title)); title = String(flags.title);
  }
  info('title : ' + JSON.stringify(title.slice(0, 80)));
  info('shot  : ' + await shot(p, 'featured-' + MODE));
  if (!COMMIT) { info('PREVIEW (nada salvo)'); return done(); }
  await clickSave(p);
  ok(await verify(SECTIONS.featured, title.slice(0, 30)) ? 'salvo e verificado' : 'SALVO? readback nao confirmou');
  await done();
}

async function addProject() {
  const proj = JSON.parse(readText(flags.file)); // { name, description, url? }
  if (proj.description && proj.description.length > LIMITS.projDesc) die(1, 'ABORT: descricao > ' + LIMITS.projDesc);
  const p = await go(SECTIONS.projects, 3200);
  let opened = false;
  for (const rx of [/Adicionar projeto novo/i, /Adicionar.*projeto/i, /Add.*project/i]) {
    for (const role of ['link', 'button']) {
      if (opened) break;
      try { await p.getByRole(role, { name: rx }).first().click({ timeout: 4000 }); opened = true; } catch {}
    }
  }
  if (!opened) die(2, 'FAIL: nao achei o controle de adicionar projeto');
  await p.locator('dialog[open]').first().waitFor({ state: 'visible', timeout: 20000 });
  await p.waitForTimeout(3000);
  // this form has no aria-labels — the fields are bound through <label>,
  // and here Descrição really is a <textarea>, not a contenteditable
  await p.getByLabel(/Nome do projeto|Project name/).first().fill(proj.name);
  await p.getByLabel(/Descrição|Description/).first().fill(proj.description || '');
  await p.waitForTimeout(500);
  if (proj.url) {
    await p.getByRole('button', { name: RX.addMedia }).first().click({ timeout: 8000 });
    await p.waitForTimeout(1600);
    await p.getByRole('menuitem', { name: RX.addLink }).first().click({ timeout: 8000 });
    const urlInput = p.locator('dialog[open] input[type="text"]').last();
    await urlInput.waitFor({ state: 'visible', timeout: 15000 });
    await urlInput.fill(proj.url);
    await p.waitForTimeout(700);
    await p.getByRole('button', { name: RX.add }).first().click({ timeout: 8000 });
    await p.waitForTimeout(11000);
  }
  info('shot  : ' + await shot(p, 'project-' + MODE));
  if (!COMMIT) { info('PREVIEW (nada salvo)'); return done(); }
  // two Salvar steps: one closes the media sub-form, one saves the project
  for (let i = 0; i < 2; i++) {
    try {
      const s = p.getByRole('button', { name: RX.save }).first();
      if (await s.isEnabled({ timeout: 5000 })) { await s.click({ timeout: 5000 }); await p.waitForTimeout(4500); }
    } catch {}
  }
  ok(await verify(SECTIONS.projects, proj.name) ? 'salvo e verificado' : 'SALVO? readback nao confirmou');
  await done();
}

// ----------------------------------------------------------------- contact

async function setSite() {
  const newSite = rest[0];
  if (!newSite) die(1, 'uso: set-site https://exemplo.com [--commit]');
  const p = await go('/', 3000);
  await p.getByRole('link', { name: RX.contactInfo }).first().click({ timeout: 12000 });
  await p.locator('dialog[open]').first().waitFor({ state: 'visible', timeout: 15000 });
  await p.waitForTimeout(1500);
  await p.locator('dialog[open]').getByRole('button', { name: /Editar|Edit/i }).first().click({ timeout: 8000 })
    .catch(async () => { await p.locator('dialog[open] a[href*="edit"]').first().click({ timeout: 8000 }); });
  await p.waitForTimeout(3000);
  let target = p.locator('dialog[open] input[aria-label*="site" i], dialog[open] input[aria-label*="Website" i]').first();
  if (!(await target.isVisible().catch(() => false))) {
    target = null;
    for (const inp of await p.locator('dialog[open] input').all()) {
      if (/^https?:|\.[a-z]{2,}$/i.test((await inp.inputValue().catch(() => '')).trim())) { target = inp; break; }
    }
  }
  if (!target) die(3, 'ABORT: nao achei o campo de site');
  info('before: ' + JSON.stringify(await target.inputValue()));
  await target.fill(newSite);
  info('after : ' + JSON.stringify(await target.inputValue()));
  info('shot  : ' + await shot(p, 'contact-' + MODE));
  if (!COMMIT) { info('PREVIEW (nada salvo)'); return done(); }
  await clickSave(p);
  ok(await verify(SECTIONS.contact, newSite.replace(/^https?:\/\//, '').replace(/\/$/, '')) ? 'salvo e verificado' : 'SALVO? readback nao confirmou');
  await done();
}

// ------------------------------------------------------------------- audit

/**
 * Scores the profile against references/best-practices.md.
 * Checks are quantitative on purpose: "section exists" passes forever and tells
 * you nothing, so every rule has a target number and reports the gap.
 */
async function audit() {
  const R = [];
  const add = (id, pass, msg) => R.push({ id, pass, msg });

  const p1 = await go('/', 3000);
  await scrollAll(p1);
  const main = cleanText(await p1.locator('main').first().innerText().catch(() => ''));
  const intro = await readIntro(p1);
  const h = intro.headline;

  add('headline-len', h.length >= 150, `headline ${h.length}/${LIMITS.headline} — o campo de maior peso na busca; encha ate ~200`);
  add('headline-keywords', (h.match(/[|·•]/g) || []).length >= 2, 'headline com 3+ blocos separados por | ou · (cargo | dominio | stack)');
  add('headline-role-first', /^[A-ZÀ-Ú][^|·•]{5,40}[|·•]/.test(h), 'headline deve comecar pelo CARGO-ALVO, nao por empresa/adjetivo');

  const sec = {};
  for (const k of ['experience', 'skills', 'featured', 'projects', 'languages', 'certifications', 'recommendations', 'education']) {
    const p = await go(SECTIONS[k], 2400);
    // an empty section bounces back to the profile page
    if (!/\/details\//.test(p.url())) { sec[k] = { empty: true, items: [] }; continue; }
    sec[k] = { empty: false, items: await entries(p) };
  }

  const aboutLen = (main.split(/\nSobre\n|\nAbout\n/)[1] || '').length;
  add('about-len', aboutLen >= 900, `Sobre ~${aboutLen}/${LIMITS.about} chars — as 3 primeiras linhas sao o que aparece antes do "ver mais"`);

  const exps = sec.experience.items;
  const short = (e) => e.label.replace(/^Editar\s*/i, '').split(' na empresa ')[0];
  const thin = exps.filter(e => e.text.length < 400);
  add('exp-descriptions', thin.length === 0, `${exps.length - thin.length}/${exps.length} experiencias com descricao real` + (thin.length ? ' — magras: ' + thin.map(short).join(', ') : ''));
  const withMetric = exps.filter(e => /\d+\s*(%|x\b|mil|k\b|ms\b|req|usuári|user|milh)/i.test(e.text));
  add('exp-metrics', withMetric.length >= Math.ceil(exps.length / 2), `${withMetric.length}/${exps.length} experiencias citam numero/metrica (latencia, volume, %) — recrutador tecnico le isso primeiro`);

  const nSkills = sec.skills.items.length;
  add('skills-count', nSkills >= 25, `${nSkills} competencias (limite 100). Alvo 40+; o Recruiter filtra por elas e so as 3 fixadas aparecem no perfil`);
  add('featured-count', sec.featured.items.length >= 3, `${sec.featured.items.length} itens em Em destaque (alvo 3+: CV, projeto, repo)`);
  add('projects-count', sec.projects.items.length >= 3, `${sec.projects.items.length} projetos (alvo 3+)`);
  add('recommendations', sec.recommendations.items.length >= 2, `${sec.recommendations.items.length} recomendacoes recebidas (alvo 2+; e o sinal social mais caro de falsificar)`);
  add('certifications', sec.certifications.items.length >= 1, `${sec.certifications.items.length} certificados`);
  add('languages', sec.languages.items.length >= 2, `${sec.languages.items.length} idiomas (ingles listado = entra em busca de vaga internacional)`);
  add('open-to-work', /Disponível para|Open to/i.test(main), 'sinal "Disponivel para" ativo — e um filtro booleano no LinkedIn Recruiter');
  add('custom-url', !/\/in\/[a-z-]*-[0-9a-f]{6,}/i.test(BASE), 'URL personalizada (sem hash)');
  add('contact-site', /Dados de contato|Contact info/i.test(main), 'Dados de contato com site/portfolio');

  const fails = R.filter(r => !r.pass);
  R.forEach(r => info((r.pass ? 'PASS ' : 'FAIL ') + r.id.padEnd(20) + r.msg));
  info(`\nscore ${R.length - fails.length}/${R.length}`);
  if (fails.length) info('acoes: ' + fails.map(f => f.id).join(', '));
  const f = outFile('audit.json', {
    intro, checks: R,
    counts: Object.fromEntries(Object.entries(sec).map(([k, v]) => [k, v.items.length])),
    items: Object.fromEntries(Object.entries(sec).map(([k, v]) =>
      [k, v.items.slice(0, 60).map(i => i.label.replace(/^Editar\s*/i, '') + ' (' + i.text.length + 'c)')])),
  });
  info('-> ' + f);
  await done();
}

// -------------------------------------------------------------------- main

const CMDS = {
  doctor, stats, read, get, pencils,
  'set-text': setText, 'set-exp-desc': setExpDesc, 'set-exp-title': setExpTitle, 'set-edu': setEdu,
  'add-skill': addSkill, 'add-language': addLanguage, 'add-featured': addFeatured, 'add-project': addProject,
  'set-site': setSite, audit,
};

if (!CMDS[cmd]) {
  console.log('comandos: ' + Object.keys(CMDS).join(', '));
  console.log('escritas sao dry-run; use --commit para salvar de verdade');
  process.exit(1);
}
try {
  await CMDS[cmd]();
} catch (e) {
  console.log('ERRO: ' + e.message.split('\n')[0].slice(0, 200));
  await done(1);
}

#!/usr/bin/env node
/**
 * Promo video recorder: plays scripted scenes in the REAL game (dist/ build)
 * on a virtual clock and saves every frame, so the footage is a perfect 60 fps
 * no matter how slow the machine is. Every sound effect call is logged with
 * its exact time, and `render-audio.mjs` later replays those calls through the
 * game's own synth offline, so audio and picture line up to the frame.
 *
 * Usage (after `npm run build`):
 *   node scripts/promo/record.mjs --lang pt-BR [--only hook,chain]
 * Output: promo/raw/<lang>/<scene>/f00001.jpg ... + events.json
 */
import { createServer } from 'node:http'
import { readFile, stat } from 'node:fs/promises'
import { mkdirSync, rmSync, writeFileSync } from 'node:fs'
import { extname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import puppeteer from 'puppeteer-core'
import { SCENES } from './scenes.mjs'

const ROOT = resolve(fileURLToPath(new URL('../..', import.meta.url)))
const DIST = join(ROOT, 'dist')
const OUT = join(ROOT, 'promo/raw')
const CHROME = process.env.CHROME_BIN ?? 'C:/Program Files/Google/Chrome/Application/chrome.exe'
const FPS = 60
const DT = 1000 / FPS
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png', '.woff2': 'font/woff2', '.json': 'application/json', '.mp3': 'audio/mpeg', '.ogg': 'audio/ogg' }

const args = process.argv.slice(2)
const opt = (name, dflt) => {
  const i = args.indexOf(`--${name}`)
  return i >= 0 ? args[i + 1] : dflt
}
const LANG = opt('lang', 'en-US')
const ONLY = opt('only', '')?.split(',').filter(Boolean)

// virtual clock: rAF, timers, performance.now and Date.now all follow __vt.advance()
const CLOCK = `(() => {
  let now = 0
  const epoch = Date.now()
  const RealDate = Date
  let raf = []
  let rafId = 0
  const timers = new Map()
  let tid = 0
  performance.now = () => now
  Date.now = () => epoch + now
  window.requestAnimationFrame = (cb) => { raf.push([++rafId, cb]); return rafId }
  window.cancelAnimationFrame = (id) => { raf = raf.filter((e) => e[0] !== id) }
  window.setTimeout = (cb, ms = 0, ...a) => { timers.set(++tid, { t: now + Math.max(0, +ms || 0), cb, a }); return tid }
  window.clearTimeout = (id) => { timers.delete(id) }
  window.setInterval = (cb, ms = 0, ...a) => { const iv = Math.max(1, +ms || 0); timers.set(++tid, { t: now + iv, cb, a, iv }); return tid }
  window.clearInterval = window.clearTimeout
  window.__vt = {
    get now() { return now },
    advance(dt) {
      const target = now + dt
      for (;;) {
        let next = null
        for (const [id, tm] of timers) if (tm.t <= target && (!next || tm.t < next[1].t)) next = [id, tm]
        if (!next) break
        const [id, tm] = next
        now = Math.max(now, tm.t)
        if (tm.iv) tm.t += tm.iv; else timers.delete(id)
        try { typeof tm.cb === 'function' ? tm.cb(...tm.a) : 0 } catch (e) { console.error(e) }
      }
      now = target
      const q = raf
      raf = []
      for (const [, cb] of q) { try { cb(now) } catch (e) { console.error(e) } }
    }
  }
})()`

const server = createServer(async (req, res) => {
  try {
    let p = decodeURIComponent(new URL(req.url, 'http://x').pathname)
    if (p === '/') p = '/index.html'
    const file = join(DIST, p)
    if (!(await stat(file)).isFile()) throw new Error()
    res.writeHead(200, { 'content-type': MIME[extname(file)] ?? 'application/octet-stream' })
    res.end(await readFile(file))
  } catch {
    res.writeHead(404)
    res.end()
  }
})
await new Promise((ok) => server.listen(0, '127.0.0.1', ok))
const port = server.address().port
const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: true,
  args: ['--no-sandbox', '--force-device-scale-factor=3', '--force-color-profile=srgb', '--autoplay-policy=no-user-gesture-required', '--mute-audio']
})

class Take {
  constructor(page, dir) {
    this.page = page
    this.dir = dir
    this.frame = 0
    this.recording = false
    this.marks = []
  }
  /** Advances the virtual clock by n frames, saving each one while recording. */
  async frames(n = 1) {
    for (let i = 0; i < n; i++) {
      await this.page.evaluate((dt) => window.__vt.advance(dt), DT)
      if (this.recording) {
        this.frame++
        const { data } = await this.cdp.send('Page.captureScreenshot', { format: 'jpeg', quality: 93, optimizeForSpeed: true })
        writeFileSync(join(this.dir, `f${String(this.frame).padStart(5, '0')}.jpg`), Buffer.from(data, 'base64'))
      }
    }
  }
  async seconds(s) {
    await this.frames(Math.round(s * FPS))
  }
  async start() {
    await this.page.evaluate(() => (window.__sfxLog.length = 0))
    this.t0 = await this.page.evaluate(() => window.__vt.now)
    this.recording = true
  }
  /** Named timestamp for the editor (e.g. the frame a big clear lands). */
  mark(name) {
    this.marks.push({ name, frame: this.frame })
  }
  async eval(fn, arg) {
    return this.page.evaluate(fn, arg)
  }
  /** Drags a tray piece onto (r, c) like a quick player: pick, glide, drop. */
  async drag(slot, r, c, { glide = 14, hold = 4 } = {}) {
    const from = await this.eval((s) => window.__bb.pieceHome(s), slot)
    const to = await this.eval(({ slot, r, c }) => window.__bb.fingerFor(slot, r, c), { slot, r, c })
    const ts = this.page.touchscreen
    await ts.touchStart(from.x, from.y)
    await this.frames(2)
    for (let i = 1; i <= glide; i++) {
      const k = i / glide
      const e = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2
      await ts.touchMove(from.x + (to.x - from.x) * e, from.y + (to.y - from.y) * e)
      await this.frames(1)
    }
    await this.frames(hold)
    await ts.touchEnd()
    await this.frames(1)
  }
  /** Greedy autoplayer: best move by lines cleared, then by snugness. */
  async bestMove() {
    return this.eval(() => {
      const core = window.__bb.core()
      const B = core.board
      const filled = (v) => v !== 0
      let best = null
      core.tray.forEach((p, slot) => {
        if (!p) return
        for (let r = 0; r < 8; r++)
          for (let c = 0; c < 8; c++) {
            if (!core.canPlaceAt(slot, r, c)) continue
            const b = B.slice()
            for (const [dr, dc] of p.cells) b[(r + dr) * 8 + c + dc] = 1
            let lines = 0
            for (let i = 0; i < 8; i++) {
              let row = true, col = true
              for (let j = 0; j < 8; j++) {
                if (!filled(b[i * 8 + j])) row = false
                if (!filled(b[j * 8 + i])) col = false
              }
              lines += (row ? 1 : 0) + (col ? 1 : 0)
            }
            let snug = 0
            for (const [dr, dc] of p.cells) {
              const rr = r + dr, cc = c + dc
              for (const [a, d] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
                const y = rr + a, x = cc + d
                if (y < 0 || y > 7 || x < 0 || x > 7 || filled(B[y * 8 + x])) snug++
              }
            }
            const score = lines * 100 + snug
            if (!best || score > best.score) best = { slot, r, c, lines, score }
          }
      })
      return best
    })
  }
  async autoplay(moves, { gap = 0.35 } = {}) {
    for (let i = 0; i < moves; i++) {
      const m = await this.bestMove()
      if (!m) break
      await this.drag(m.slot, m.r, m.c)
      if (m.lines > 0) this.mark(`clear${m.lines}`)
      await this.seconds(m.lines > 0 ? gap + 0.45 : gap)
    }
  }
}

async function openScene(scene, dir) {
  const page = await browser.newPage()
  page.on('console', (m) => {
    if (m.type() === 'error') console.log(`  [page] ${m.text()}`)
  })
  await page.setViewport({ width: 360, height: 640, deviceScaleFactor: 3, isMobile: true, hasTouch: true })
  await page.evaluateOnNewDocument(CLOCK)
  await page.evaluateOnNewDocument(
    (l, s) => {
      Object.defineProperty(navigator, 'languages', { get: () => [l] })
      Object.defineProperty(navigator, 'language', { get: () => l })
      try {
        localStorage.clear()
        for (const [k, v] of Object.entries(s)) localStorage.setItem(`bobagi-blocks.${k}`, JSON.stringify(v))
      } catch {}
    },
    LANG,
    scene.store()
  )
  await page.goto(`http://127.0.0.1:${port}/?debug=1&nohints=1${scene.url ?? ''}`, { waitUntil: 'domcontentloaded' })
  const take = new Take(page, dir)
  take.cdp = await page.createCDPSession()
  // drive the clock until the scene is up and the tray has settled
  for (let i = 0; i < 1200; i++) {
    await take.frames(1)
    const ready = await page.evaluate(() => !!(window.__bb && window.__bb.pieceHome && window.__bb.pieceHome(0)))
    if (ready) break
  }
  await page.evaluate(() => {
    window.__sfxLog = []
    const sfx = window.__bb.sfx
    for (const k of Object.keys(sfx)) {
      const orig = sfx[k]
      sfx[k] = (...a) => {
        window.__sfxLog.push({ name: k, args: a, t: window.__vt.now })
        return orig(...a)
      }
    }
  })
  // promo footage: no toast banners over the action (mission/achievement/rule tips)
  await page.evaluate(() => {
    window.__bb.scene.toast = () => {}
  })
  await take.seconds(scene.settle ?? 2.6)
  return take
}

const list = SCENES.filter((s) => !ONLY.length || ONLY.includes(s.name))
for (const scene of list) {
  const dir = join(OUT, LANG, scene.name)
  rmSync(dir, { recursive: true, force: true })
  mkdirSync(dir, { recursive: true })
  const t = Date.now()
  const take = await openScene(scene, dir)
  await scene.run(take)
  const log = await take.eval(() => window.__sfxLog)
  const events = log.map((e) => ({ ...e, t: (e.t - take.t0) / 1000 }))
  writeFileSync(join(dir, 'events.json'), JSON.stringify({ fps: FPS, frames: take.frame, marks: take.marks, sfx: events }, null, 1))
  console.log(`${LANG}/${scene.name}: ${take.frame} frames, ${events.length} sfx, marks ${take.marks.map((m) => `${m.name}@${m.frame}`).join(' ')} (${((Date.now() - t) / 1000).toFixed(0)} s)`)
  await take.page.close()
}
await browser.close()
server.close()

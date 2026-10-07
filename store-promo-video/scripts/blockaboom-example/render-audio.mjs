#!/usr/bin/env node
/**
 * Renders the sound effects of each recorded scene to a WAV, using the game's
 * own WebAudio synth: the page's AudioContext is swapped for an
 * OfflineAudioContext whose clock we set to each logged event time, then the
 * same `sfx.*` call the game made is replayed. Result: the real game sounds,
 * sample-accurate against the recorded frames.
 *
 * Usage: node scripts/promo/render-audio.mjs --lang pt-BR
 * Output: promo/raw/<lang>/<scene>/sfx.wav
 */
import { createServer } from 'node:http'
import { readFile, stat } from 'node:fs/promises'
import { existsSync, readdirSync, readFileSync, writeFileSync } from 'node:fs'
import { extname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import puppeteer from 'puppeteer-core'

const ROOT = resolve(fileURLToPath(new URL('../..', import.meta.url)))
const DIST = join(ROOT, 'dist')
const CHROME = process.env.CHROME_BIN ?? 'C:/Program Files/Google/Chrome/Application/chrome.exe'
const args = process.argv.slice(2)
const LANG = args[args.indexOf('--lang') + 1] ?? 'en-US'
const RAW = join(ROOT, 'promo/raw', LANG)
const ONLY = args.includes('--only') ? args[args.indexOf('--only') + 1].split(',') : null
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png', '.woff2': 'font/woff2', '.json': 'application/json' }

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
const browser = await puppeteer.launch({ executablePath: CHROME, headless: true, args: ['--no-sandbox', '--mute-audio'] })

for (const scene of readdirSync(RAW).filter((d) => !ONLY || ONLY.includes(d))) {
  const evFile = join(RAW, scene, 'events.json')
  if (!existsSync(evFile)) continue
  const ev = JSON.parse(readFileSync(evFile, 'utf8'))
  const seconds = ev.frames / ev.fps + 1.5
  const page = await browser.newPage()
  await page.evaluateOnNewDocument((len) => {
    const OAC = window.OfflineAudioContext
    window.__rt = 0
    window.__ctxs = []
    class Fake extends OAC {
      constructor() {
        super(2, Math.ceil(48000 * len), 48000)
        window.__ctxs.push(this)
      }
      get currentTime() {
        return window.__rt
      }
      resume() {
        return Promise.resolve()
      }
      suspend() {
        return Promise.resolve()
      }
      close() {
        return Promise.resolve()
      }
      createMediaElementSource() {
        return this.createGain()
      }
    }
    window.AudioContext = Fake
    window.webkitAudioContext = Fake
  }, seconds)
  await page.goto(`http://127.0.0.1:${port}/?debug=1&nohints=1`, { waitUntil: 'domcontentloaded' })
  await page.waitForFunction('window.__bb && window.__bb.sfx', { timeout: 30000 })
  const b64 = await page.evaluate(async (events) => {
    const sfx = window.__bb.sfx
    const before = window.__ctxs.length
    for (const e of events) {
      window.__rt = Math.max(0, e.t)
      sfx[e.name](...e.args)
    }
    const ctx = window.__ctxs[window.__ctxs.length - 1]
    if (!events.length || window.__ctxs.length === 0) return null
    void before
    const buf = await ctx.startRendering()
    const n = buf.length
    const ch = [buf.getChannelData(0), buf.getChannelData(buf.numberOfChannels > 1 ? 1 : 0)]
    const out = new DataView(new ArrayBuffer(44 + n * 4))
    const w = (o, s) => [...s].forEach((c, i) => out.setUint8(o + i, c.charCodeAt(0)))
    w(0, 'RIFF'); out.setUint32(4, 36 + n * 4, true); w(8, 'WAVE'); w(12, 'fmt ')
    out.setUint32(16, 16, true); out.setUint16(20, 1, true); out.setUint16(22, 2, true)
    out.setUint32(24, 48000, true); out.setUint32(28, 48000 * 4, true); out.setUint16(32, 4, true); out.setUint16(34, 16, true)
    w(36, 'data'); out.setUint32(40, n * 4, true)
    for (let i = 0; i < n; i++)
      for (let c = 0; c < 2; c++) out.setInt16(44 + i * 4 + c * 2, Math.max(-1, Math.min(1, ch[c][i])) * 32767, true)
    let s = ''
    const bytes = new Uint8Array(out.buffer)
    for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode(...bytes.subarray(i, i + 0x8000))
    return btoa(s)
  }, ev.sfx)
  if (b64) writeFileSync(join(RAW, scene, 'sfx.wav'), Buffer.from(b64, 'base64'))
  console.log(`${LANG}/${scene}: ${ev.sfx.length} sfx -> ${b64 ? 'sfx.wav' : 'no audio'}`)
  await page.close()
}
await browser.close()
server.close()

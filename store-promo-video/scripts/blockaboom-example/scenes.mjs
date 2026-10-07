/**
 * Scripted scenes for the promo video. Each one seeds localStorage (a veteran
 * player plus a crafted mid-run save), then `run(take)` plays real moves.
 * Boards are 8 strings of 8 chars: '.' empty, '1'..'7' block colors.
 * Every move is a real, legal move of the shipped game (store video policy:
 * real gameplay only); the editor adds cuts, zooms and text on top.
 */
const BUILT = ['praca', 'lampiao', 'banco', 'arvore', 'banca', 'fonte', 'casa', 'cafe', 'torre', 'porto', 'boia', 'pier', 'barco', 'armazem', 'guindaste', 'balsa', 'ponte', 'farol', 'parque', 'bilheteria', 'pipoca', 'tenda']
const day = (off) => new Date(Date.now() + off * 86400000).toISOString().slice(0, 10)

function veteran(extra = {}) {
  return {
    welcomed: true,
    hintsSeen: true,
    powerHint: true,
    best: 6120,
    map: 1,
    meta: { v: 1, bricks: 640, built: BUILT, skins: ['padrao'], skin: 'padrao', pendingGolden: 0, powerTokens: { swap: 1, undo: 0, hammer: 0 } },
    streak: { v: 1, lastSeen: day(-1), lastActive: day(-1), streak: 9, best: 12, freezes: 1, rewardedDay: day(-1), dailyDays: {}, trophies: {} },
    // everything already unlocked and today's missions done: no toasts over the action
    progress: {
      v: 1, games: 140, lines: 2400, goldens: 80, bestClear: 6, bestCombo: 8, dailyCount: 9, dailyLast: day(-1), map: 7, built: BUILT.length,
      unlocked: ['first_game', 'games_25', 'games_100', 'lines_100', 'lines_1000', 'clear_3', 'clear_4', 'combo_x3', 'golden_10', 'golden_50', 'map_5', 'map_10', 'map_20', 'daily_1', 'daily_7', 'build_first', 'districts_3', 'districts_4', 'districts_5'],
      pendingSync: []
    },
    missions: { v: 1, day: day(0), missions: [], bonusClaimed: true },
    ...extra
  }
}

function board(rows) {
  const b = []
  for (const row of rows) for (const ch of row) b.push(ch === '.' ? 0 : Number(ch))
  if (b.length !== 64) throw new Error('board needs 8x8')
  // a crafted board must not already hold a full line (it would clear on the next move)
  for (let i = 0; i < 8; i++) {
    let row = true, col = true
    for (let j = 0; j < 8; j++) {
      if (!b[i * 8 + j]) row = false
      if (!b[j * 8 + i]) col = false
    }
    if (row || col) throw new Error(`board already has a full ${row ? 'row' : 'col'} ${i}`)
  }
  return b
}

function save(rows, tray, { score = 2840, streak = 2, fever = 2, goldens = [] } = {}) {
  return {
    v: 5,
    seed: 4242,
    rngState: 4242,
    board: board(rows),
    tray: tray.map((shapeId, i) => ({ shapeId, uid: 11 + i })),
    goldens: goldens.map((shapeId, i) => ({ shapeId, uid: 20 + i })),
    score,
    streak,
    fever,
    over: false,
    moves: 37,
    uidSeq: 60,
    goal: null,
    victory: false,
    objective: null
  }
}

export const SCENES = [
  {
    // 0-2 s hook: one 3x3 drop wipes three rows AND three columns at once
    name: 'hook',
    store: () => veteran({
      save: save(
        ['..353...', '1.524.6.', '21437.66', '.2615346', '3.743215', '54...721', '12...563', '63...144'],
        ['d2h', 'sq3', 'c3a'],
        { score: 4820, streak: 4, fever: 4 }
      )
    }),
    run: async (t) => {
      await t.start()
      await t.seconds(0.2)
      await t.drag(1, 5, 2, { glide: 16, hold: 6 })
      t.mark('boom')
      await t.seconds(2.6)
    }
  },
  {
    // combo chain: every piece of the hand clears, the streak and fever climb
    name: 'chain',
    store: () => veteran({
      save: save(
        ['1..2..3.', '.4..5..6', '7.1..2..', '12345.67', '12345..7', '12....34', '7654.321', '1234.567'],
        ['d2v', 'l4h', 'c3a'],
        { score: 1960, streak: 1, fever: 3 }
      )
    }),
    run: async (t) => {
      await t.start()
      await t.seconds(0.15)
      await t.autoplay(6, { gap: 0.25 })
      await t.seconds(0.6)
    }
  },
  {
    // tension: the board is packed, one spot left, and it turns into a quad clear
    name: 'clutch',
    store: () => veteran({
      save: save(
        ['2.3415.6', '35.6.214', '412.653.', '5.423.16', '62.534.1', '.1234567', '.7654321', '...35627'],
        ['sq3', 'B5a', 'l5h'],
        { score: 5310, streak: 0, fever: 1 }
      )
    }),
    run: async (t) => {
      await t.start()
      await t.seconds(0.5)
      // hover the big piece over the hole for a beat before letting go
      await t.drag(1, 5, 0, { glide: 22, hold: 24 })
      t.mark('boom')
      await t.seconds(2.4)
    }
  },
  {
    name: 'maps',
    store: () => veteran({ map: 4 }),
    run: async (t) => {
      await t.start()
      await t.seconds(0.3)
      await t.autoplay(7, { gap: 0.3 })
      await t.seconds(0.4)
    }
  },
  {
    name: 'daily',
    store: () => veteran(),
    run: async (t) => {
      await t.eval(() => window.__bb.scene.switchMode('daily'))
      await t.seconds(0.4)
      await t.start()
      await t.seconds(1.6)
      await t.autoplay(3, { gap: 0.3 })
      await t.seconds(0.4)
    }
  },
  {
    // the village builds itself: "Build all" on a fresh district ends in the district finale
    name: 'village',
    store: () => veteran({ meta: { v: 1, bricks: 9000, built: ['praca', 'lampiao'], skins: ['padrao'], skin: 'padrao', pendingGolden: 0, powerTokens: { swap: 1, undo: 0, hammer: 0 } } }),
    run: async (t) => {
      await t.eval(() => window.__bb.scene.openVillage())
      await t.seconds(1.2)
      await t.start()
      await t.seconds(0.4)
      await t.eval(() => window.__bb.scene.scene.manager.getScene('village').onBuildAll())
      await t.seconds(6.5)
    }
  },
  {
    // finale: two half-built rows, one long bar, the board ends empty
    name: 'finale',
    store: () => veteran({
      save: save(
        ['........', '........', '........', '........', '........', '........', '1234.567', '7654.321'],
        ['d2h', 'd2v', 'sq2'],
        { score: 6080, streak: 5, fever: 5 }
      )
    }),
    run: async (t) => {
      await t.start()
      await t.seconds(0.3)
      await t.drag(1, 6, 4, { glide: 18, hold: 8 })
      t.mark('boom')
      await t.seconds(2.6)
    }
  }
]

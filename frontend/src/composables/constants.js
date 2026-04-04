export const VERDICT_MUST = 'MUST'
export const VERDICT_PASS = 'PASS'
export const VERDICT_SKIP = 'SKIP'
export const VERDICT_PREM = 'PREM'
export const VERDICT_FILL = 'FILL'

export const VERDICT_COLORS = {
  MUST: { border: '#10b981', bg: 'rgba(16,185,129,0.08)',  icon: '🟢', label: 'Must Play'      },
  FILL: { border: '#38bdf8', bg: 'rgba(56,189,248,0.07)',  icon: '🔵', label: 'Lineup Filler'  },
  PASS: { border: '#fbbf24', bg: 'rgba(251,191,36,0.06)',  icon: '🟡', label: 'Passable'       },
  SKIP: { border: '#f87171', bg: 'rgba(248,113,113,0.08)', icon: '🔴', label: 'Hard Skip'      },
  PREM: { border: '#a78bfa', bg: 'rgba(167,139,250,0.09)', icon: '👑', label: 'Premium Fix'    },
}

export const BRANCH_TYPES = {
  Ground:      ['medium_tank', 'light_tank', 'heavy_tank', 'tank_destroyer', 'spaa'],
  Aviation:    ['fighter', 'bomber', 'assault'],
  Helicopters: ['attack_helicopter', 'utility_helicopter'],
  Fleet:       ['destroyer', 'heavy_cruiser', 'light_cruiser', 'battleship', 'battlecruiser',
                'boat', 'heavy_boat', 'frigate', 'barge'],
}

export const TYPE_LABELS = {
  medium_tank:        '🛡️ Medium',    light_tank:         '💨 Light',
  heavy_tank:         '⚔️ Heavy',      tank_destroyer:     '🎯 Tank Dest.',
  spaa:               '🌀 SPAA',
  fighter:            '✈️ Fighter',    bomber:             '💣 Bomber',
  assault:            '🔥 Assault',    attack_helicopter:  '🚁 Atk Heli',
  utility_helicopter: '🔧 Util Heli',
  destroyer:          '🚢 Destroyer',  heavy_cruiser:      '🛳️ H.Cruiser',
  light_cruiser:      '🛳️ L.Cruiser',  battleship:         '⚓ Battleship',
  battlecruiser:      '⚓ B.Cruiser',  boat:               '⛵ Boat',
  heavy_boat:         '🚤 H.Boat',     frigate:            '🛥️ Frigate',
  barge:              '🪝 Barge',
}

export const TYPE_ICON = {
  medium_tank:        '🛡️', heavy_tank:        '⚔️', light_tank:   '💨',
  tank_destroyer:     '🎯', spaa:              '🌀',
  fighter:            '✈️', bomber:            '💣', assault:      '🔥',
  attack_helicopter:  '🚁', utility_helicopter:'🔧',
  destroyer:          '🚢', battleship:        '⚓', light_cruiser:'🛳️',
  heavy_cruiser:      '🛳️', battlecruiser:     '⚓', boat:         '⛵',
  heavy_boat:         '🚤', frigate:           '🛥️', barge:        '🪝',
}

export const CLASS_PREFIX = {
  Premium:     '★ ',
  Pack:        '📦 ',
  Squadron:    '✦ ',
  Marketplace: '🏪 ',
  Gift:        '🎁 ',
  Event:       '🎪 ',
  Standard:    '',
}

export const CLASS_BR_COLOR = {
  Premium:     '#fbbf24',
  Pack:        '#60a5fa',
  Squadron:    '#34d399',
  Marketplace: '#a78bfa',
  Gift:        '#f472b6',
  Event:       '#fb923c',
}

export const ROMAN = { 1:'I', 2:'II', 3:'III', 4:'IV', 5:'V', 6:'VI', 7:'VII', 8:'VIII' }

export const STD_CLASS = 'Standard'

export const MM_WINDOW      = 1.0
export const BR_FILL_WINDOW = 1.0
export const JUNK_FLOOR     = 35.0
export const YELLOW_FLOOR   = 35.0
export const YELLOW_PCTILE  = 0.30

export const RANK_PENALTY = {
  '-4': 0.05, '-3': 0.10, '-2': 0.30, '-1': 0.90,
   0: 1.00,    1: 1.00,    2: 0.35,    3: 0.15,    4: 0.06,
}
export const RANK_PENALTY_PREMIUM = {
  '-4': 1.00, '-3': 1.00, '-2': 1.00, '-1': 1.00,
   0: 1.00,    1: 1.00,    2: 0.35,    3: 0.15,    4: 0.06,
}

export const TYPE_CATEGORIES = {
  Ground:      BRANCH_TYPES.Ground,
  Aviation:    BRANCH_TYPES.Aviation,
  Helicopters: BRANCH_TYPES.Helicopters,
  LargeFleet:  ['destroyer', 'heavy_cruiser', 'light_cruiser', 'battleship', 'battlecruiser'],
  SmallFleet:  ['boat', 'heavy_boat', 'frigate', 'barge'],
}

export const LARGE_FLEET_TYPES = new Set(TYPE_CATEGORIES.LargeFleet)
export const SMALL_FLEET_TYPES = new Set(TYPE_CATEGORIES.SmallFleet)

export const TANK_TYPES = new Set(['medium_tank', 'heavy_tank', 'light_tank'])

export const DEFAULT_LINEUP_SLOTS = 4

export const LINEUP_PRIORITY = {
  Ground:      ['tank', 'spaa', 'tank_destroyer'],
  Aviation:    ['fighter', 'assault', 'bomber'],
  Helicopters: ['attack_helicopter', 'utility_helicopter'],
  LargeFleet:  ['destroyer', 'light_cruiser', 'heavy_cruiser',
                'battleship', 'battlecruiser'],
  SmallFleet:  ['boat', 'heavy_boat', 'frigate', 'barge'],
}

export const BR_ERA_THRESHOLDS = [2.3, 3.7, 5.3, 6.7, 8.3, 9.7, 11.3]

export const CROSS_THRESH       = 1.30  // hint если другая ветка на 30% сильнее
export const CROSS_SKIP_THRESH  = 1.40  // SKIP если на 40% сильнее + ниже BR
export const CROSS_BR_WINDOW    = 0.7   // смотреть вперёд (выше BR)
export const CROSS_BR_LOOKBACK  = 1.0   // смотреть назад  (ниже BR)
export const NO_CROSS_TYPES     = new Set(['spaa'])
export const FILL_MIN_SCORE     = 1.0   // минимальный META_SCORE для FILL-кандидата

export const REDBOOK_LOW_BATTLES = 100

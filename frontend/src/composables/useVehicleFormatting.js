import { useI18n } from 'vue-i18n'

export const NATION_FLAG = {
  usa:         '🇺🇸', germany:    '🇩🇪', ussr:        '🇷🇺',
  britain:     '🇬🇧', japan:      '🇯🇵', italy:       '🇮🇹',
  france:      '🇫🇷', sweden:     '🇸🇪', israel:      '🇮🇱',
  china:       '🇨🇳', finland:    '🇫🇮', netherlands: '🇳🇱',
  hungary:     '🇭🇺',
}

export const CLASS_PREFIX = {
  Premium:    '⭐ ',
  Pack:       '🎁 ',
  Squadron:   '✈️ ',
  Marketplace:'💎 ',
  Gift:       '🎀 ',
  Event:      '⚡ ',
  Standard:   '',
}

export function useFmtType() {
  const { t } = useI18n()
  return (type) => {
    if (!type) return '—'
    const key = `vehicle_types.${type}`
    const translated = t(key)
    return translated === key ? type : translated
  }
}

export const TYPE_LABELS_EN = {
  medium_tank:         'Medium Tank',   light_tank:          'Light Tank',
  heavy_tank:          'Heavy Tank',    tank_destroyer:       'Tank Destroyer',
  spaa:                'SPAA',          fighter:              'Fighter',
  bomber:              'Bomber',        assault:              'Assault',
  utility_helicopter:  'Utility Heli',  attack_helicopter:   'Attack Heli',
  destroyer:           'Destroyer',     heavy_cruiser:        'Heavy Cruiser',
  light_cruiser:       'Light Cruiser', battleship:           'Battleship',
  battlecruiser:       'Battlecruiser', boat:                 'Boat',
  heavy_boat:          'Heavy Boat',    frigate:              'Frigate',
  barge:               'Barge',
}

export function fmtType(t) {
  return TYPE_LABELS_EN[t] ?? t ?? '—'
}

export function fmtNation(n) {
  if (!n) return '—'
  const flag = NATION_FLAG[n.toLowerCase()] ?? '🏴'
  return `${flag} ${n}`
}

export function fmtBR(v) {
  const n = parseFloat(v)
  return isNaN(n) ? '—' : n.toFixed(1)
}

export function fmtSL(v) {
  if (v == null) return '—'
  const n = Math.round(v)
  return n.toLocaleString() + ' SL'
}

export function metaColor(score) {
  if (score >= 70) return '#34d399'
  if (score >= 45) return '#fbbf24'
  return '#f87171'
}

export function farmColor(score) {
  if (score >= 70) return '#a78bfa'
  if (score >= 45) return '#fbbf24'
  return '#94a3b8'
}

export function wrColor(wr) {
  if (wr >= 55) return '#34d399'
  if (wr <  48) return '#f87171'
  return '#e2e8f0'
}

export function vehicleDisplayName(v) {
  const prefix = CLASS_PREFIX[v?.VehicleClass ?? 'Standard'] ?? ''
  return prefix + (v?.Name ?? '')
}

export const SAFE_KEYS = {
  'Сыграно игр':    'battles',
  'Net SL за игру': 'net_sl',
  'SL за игру':     'sl',
  'RP за игру':     'rp',
}

export function normRow(v) {
  const row = { ...v }
  for (const [orig, safe] of Object.entries(SAFE_KEYS)) {
    if (orig in row) row[safe] = row[orig]
  }
  return row
}

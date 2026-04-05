<template>
  <div>
    <div class="controls-bar mb-4">
      <div class="controls-row">

        <div class="metric-group">
          <button
            v-for="m in METRICS"
            :key="m.key"
            :class="['metric-btn', metric === m.key && 'active']"
            @click="metric = m.key"
          >
            <span class="metric-icon">{{ m.icon }}</span>
            {{ t(`cost_tab.metric_${m.key}`) }}
          </button>
        </div>

        <div class="ctrl-divider" />

        <div class="class-chips">
          <span class="ctrl-label">{{ t('cost_tab.include') }}</span>
          <div class="chips-row">
            <button
              v-for="cls in CLASS_OPTIONS"
              :key="cls"
              :class="['cls-chip', selectedClasses.includes(cls) && 'active']"
              @click="toggleClass(cls)"
            >{{ t(`vehicle_classes.${cls}`) }}</button>
          </div>
        </div>

        <InfoTip align="right" class="ml-auto">
          <p><b>{{ t('cost_tab.tip_title') }}</b></p>
          <p>{{ t('cost_tab.tip_desc') }}</p>
          <div class="tip-row mt-2">
            <span class="tip-icon">📊</span>
            <span>{{ t('cost_tab.tip_bars') }}</span>
          </div>
          <div class="tip-row">
            <span class="tip-icon">🎨</span>
            <span>{{ t('cost_tab.tip_eras') }}</span>
          </div>
        </InfoTip>
      </div>
    </div>

    <div class="era-legend mb-4">
      <span
        v-for="e in 8"
        :key="e"
        class="era-pip"
      >
        <span class="era-dot" :style="{ background: ERA_COLORS[e] }" />
        {{ t('cost_tab.era') }} {{ e }}
      </span>
    </div>

    <div v-for="branch in BRANCHES" :key="branch.key" class="branch-section mb-6">

      <div class="branch-header">
        <span class="branch-icon">{{ branch.icon }}</span>
        <span class="branch-title">{{ t(`cost_tab.branch_${branch.key.toLowerCase()}`) }}</span>
        <span class="branch-sub">{{ t('cost_tab.n_vehicles', { n: branchVehicleCount(branch.key) }) }}</span>
      </div>

      <div class="chart-card">

        <div class="scale-row">
          <div class="nation-col" />
          <div class="bar-col">
            <div class="ticks">
              <span v-for="tick in SCALE_TICKS" :key="tick" class="tick-label"
                    :style="{ left: (tick / MAX_SCALE * 100) + '%' }">
                {{ tick === 0 ? '0' : (tick / 1e6) + 'M' }}
              </span>
            </div>
          </div>
          <div class="total-col" />
        </div>

        <div
          v-for="row in chartRows(branch.key)"
          :key="row.nation"
          class="bar-row"
        >
          <div class="nation-col">
            <span class="nation-flag">{{ NATION_FLAG[row.nation] ?? '🏳️' }}</span>
            <span class="nation-name">{{ row.nation }}</span>
          </div>

          <div class="bar-col">
            <div class="bar-track">
              <template v-for="e in 8" :key="e">
                <v-tooltip :disabled="!row.byEra[e]" location="top">
                  <template #activator="{ props }">
                    <div
                      v-if="row.byEra[e]"
                      v-bind="props"
                      class="bar-seg"
                      :style="{
                        width: segPct(row.byEra[e]) + '%',
                        background: ERA_COLORS[e],
                      }"
                    />
                  </template>
                  <span class="tooltip-content">
                    <b>{{ t('cost_tab.era') }} {{ e }}</b><br/>
                    {{ fmtFull(row.byEra[e]) }} {{ metricUnit }}<br/>
                    {{ row.countByEra[e] }} {{ t('cost_tab.vehicles') }}
                  </span>
                </v-tooltip>
              </template>
            </div>
          </div>

          <div class="total-col">
            <span class="total-label" :style="{ color: totalColor(row.total) }">
              {{ fmtM(row.total) }}
            </span>
          </div>
        </div>

        <div v-if="!chartRows(branch.key).length" class="no-data">
          {{ t('common.no_data') }}
        </div>

        <div v-else class="branch-summary">
          <span class="summary-item cheap">
            ✅ {{ t('cost_tab.cheapest') }}:
            <b>{{ chartRows(branch.key).at(-1)?.nation }}</b>
            · {{ fmtM(chartRows(branch.key).at(-1)?.total) }}
          </span>
          <span class="summary-item expensive">
            🔴 {{ t('cost_tab.priciest') }}:
            <b>{{ chartRows(branch.key)[0]?.nation }}</b>
            · {{ fmtM(chartRows(branch.key)[0]?.total) }}
          </span>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDataStore } from '../stores/useDataStore.js'
import InfoTip from '../components/InfoTip.vue'

const { t }   = useI18n()
const store   = useDataStore()

const ERA_COLORS = {
  1: '#6ee7b7',
  2: '#4ade80',
  3: '#a3e635',
  4: '#facc15',
  5: '#fb923c',
  6: '#f87171',
  7: '#c084fc',
  8: '#818cf8',
}

const NATION_FLAG = {
  USA:         '🇺🇸',
  Germany:     '🇩🇪',
  USSR:        '🇷🇺',
  Britain:     '🇬🇧',
  Japan:       '🇯🇵',
  Italy:       '🇮🇹',
  France:      '🇫🇷',
  Sweden:      '🇸🇪',
  Israel:      '🇮🇱',
  China:       '🇨🇳',
  Finland:     '🇫🇮',
  Netherlands: '🇳🇱',
  Hungary:     '🇭🇺',
}

const BRANCHES = [
  { key: 'Ground',      icon: '🛡️', types: ['medium_tank','light_tank','heavy_tank','tank_destroyer','spaa'] },
  { key: 'Aviation',    icon: '✈️', types: ['fighter','bomber','assault'] },
  { key: 'Helicopters', icon: '🚁', types: ['attack_helicopter','utility_helicopter'] },
  { key: 'Fleet',       icon: '⚓', types: ['destroyer','heavy_cruiser','light_cruiser','battleship','battlecruiser','boat','heavy_boat','frigate','barge'] },
]
const BRANCH_TYPE_SET = Object.fromEntries(
  BRANCHES.map(b => [b.key, new Set(b.types)])
)

const METRICS = [
  { key: 'rp', icon: '🔬' },
  { key: 'sl', icon: '💰' },
]

const CLASS_OPTIONS = ['Standard', 'Squadron', 'Premium', 'Pack', 'Event']

const metric          = ref('rp')
const selectedClasses = ref(['Standard'])

const MAX_SCALE = computed(() => metric.value === 'sl' ? 40_000_000 : 20_000_000)
const SCALE_TICKS = computed(() => {
  const m = MAX_SCALE.value
  return [0, m * 0.25, m * 0.5, m * 0.75, m]
})

function toggleClass(cls) {
  const i = selectedClasses.value.indexOf(cls)
  if (i === -1) selectedClasses.value.push(cls)
  else if (selectedClasses.value.length > 1) selectedClasses.value.splice(i, 1)
}

const sourceVehicles = computed(() =>
  store.allVehicles ?? store.filteredVehicles ?? []
)

const uniqueVehicles = computed(() => {
  const seen = new Set()
  const out  = []
  for (const v of sourceVehicles.value) {
    const key = v.vdb_identifier || `${v.Nation}__${v.Name}`
    if (!key || seen.has(key)) continue
    seen.add(key)
    out.push(v)
  }
  return out
})

// Pick value for current metric
function metricValue(v) {
  if (metric.value === 'rp') return Number(v.vdb_req_exp ?? 0)
  if (metric.value === 'sl') return Number(v.vdb_value   ?? 0)
  return 0
}

const metricUnit = computed(() => metric.value === 'rp' ? 'RP' : 'SL')

// Build aggregated data: { [branchKey]: { [nation]: { total, byEra, countByEra } } }
const aggregated = computed(() => {
  const result = {}
  for (const b of BRANCHES) result[b.key] = {}

  for (const v of uniqueVehicles.value) {
    // Class filter
    if (!selectedClasses.value.includes(v.VehicleClass)) continue

    // Era filter: keep era 1–8 always (no slider)
    const era = Number(v.vdb_era ?? 0)
    if (era < 1 || era > 8) continue

    // Skip vehicles with no value for chosen metric
    const val = metricValue(v)
    if (!val) continue

    // Find branch
    const vType = v.Type
    let bKey = null
    for (const b of BRANCHES) {
      if (BRANCH_TYPE_SET[b.key].has(vType)) { bKey = b.key; break }
    }
    if (!bKey) continue

    const nat = v.Nation
    if (!nat) continue

    if (!result[bKey][nat]) {
      result[bKey][nat] = { nation: nat, total: 0, byEra: {}, countByEra: {} }
    }
    const entry = result[bKey][nat]
    entry.total            += val
    entry.byEra[era]        = (entry.byEra[era]     ?? 0) + val
    entry.countByEra[era]   = (entry.countByEra[era] ?? 0) + 1
  }

  return result
})

function chartRows(branchKey) {
  const map = aggregated.value[branchKey] ?? {}
  return Object.values(map).sort((a, b) => b.total - a.total)
}

function branchVehicleCount(branchKey) {
  return uniqueVehicles.value.filter(v =>
    selectedClasses.value.includes(v.VehicleClass) &&
    Number(v.vdb_era ?? 0) >= 1 &&
    BRANCH_TYPE_SET[branchKey]?.has(v.Type)
  ).length
}


function fmtM(n) {
  if (!n) return '0'
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000)     return (n / 1_000).toFixed(0) + 'K'
  return String(n)
}

function fmtFull(n) {
  if (!n) return '0'
  return n.toLocaleString()
}

function segPct(val) {
  return Math.min((val / MAX_SCALE.value) * 100, 100)
}

function totalColor(total) {
  const pct = total / MAX_SCALE.value
  if (pct > 0.7) return '#f87171'
  if (pct > 0.5) return '#fb923c'
  return '#4ade80'
}
</script>

<style scoped>
.controls-bar {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid #1e3a5f;
  border-radius: 10px;
  padding: 12px 16px;
}
.controls-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}
.ctrl-divider {
  width: 1px;
  height: 36px;
  background: #1e3a5f;
  flex-shrink: 0;
}
.ctrl-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: .07em;
  color: #475569;
  display: block;
  margin-bottom: 4px;
}
.ml-auto { margin-left: auto; }

.metric-group { display: flex; gap: 4px; }
.metric-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: 6px;
  border: 1px solid #1e3a5f;
  background: transparent;
  color: #64748b;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all .15s;
}
.metric-btn:hover { border-color: #334155; color: #94a3b8; }
.metric-btn.active {
  border-color: #a78bfa;
  background: rgba(167,139,250,.12);
  color: #a78bfa;
}
.metric-icon { font-size: 14px; }

.chips-row { display: flex; gap: 4px; flex-wrap: wrap; margin-top: 2px; }
.cls-chip {
  padding: 3px 8px;
  border-radius: 4px;
  border: 1px solid #1e3a5f;
  background: transparent;
  color: #475569;
  font-size: 11px;
  cursor: pointer;
  transition: all .12s;
}
.cls-chip.active {
  border-color: #10b981;
  background: rgba(16,185,129,.1);
  color: #10b981;
}

.era-legend {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.era-pip {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: #94a3b8;
}
.era-dot {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  flex-shrink: 0;
}

.branch-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.branch-icon { font-size: 18px; }
.branch-title {
  font-family: 'Rajdhani', sans-serif;
  font-size: 15px;
  font-weight: 700;
  color: #a7f3d0;
  text-transform: uppercase;
  letter-spacing: .08em;
}
.branch-sub { font-size: 11px; color: #475569; }

.chart-card {
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid #1e3a5f;
  border-radius: 10px;
  padding: 12px 16px 8px;
  overflow: hidden;
}

.scale-row,
.bar-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.bar-row {
  padding: 5px 0;
  border-bottom: 1px solid rgba(30,58,95,0.4);
}
.bar-row:last-of-type { border-bottom: none; }

.chart-card:has(.bar-row:hover) .bar-row:not(:hover) {
  opacity: 0.35;
}

.nation-col {
  width: 120px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 6px;
}
.nation-flag { font-size: 16px; line-height: 1; }
.nation-name {
  font-size: 12px;
  font-weight: 600;
  color: #cbd5e1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bar-col {
  flex: 1;
  position: relative;
}

.total-col {
  width: 54px;
  flex-shrink: 0;
  text-align: right;
}
.total-label {
  font-family: 'Rajdhani', sans-serif;
  font-size: 14px;
  font-weight: 700;
}

.ticks {
  position: relative;
  height: 16px;
  margin-bottom: 4px;
}
.tick-label {
  position: absolute;
  transform: translateX(-50%);
  font-size: 10px;
  color: #475569;
  white-space: nowrap;
}
.tick-gridline {
  position: absolute;
  top: 100%;
  width: 1px;
  height: 9999px;
  background: rgba(30, 58, 95, 0.6);
  pointer-events: none;
  z-index: 0;
}

/* Bars */
.bar-track {
  display: flex;
  height: 20px;
  border-radius: 3px;
  overflow: hidden;
  background: rgba(30, 58, 95, 0.3);
  width: 100%;
  position: relative;
  z-index: 1;
}
.bar-seg {
  height: 100%;
  min-width: 1px;
  transition: filter .15s;
}
.bar-seg:hover { filter: brightness(1.3); cursor: default; }

.tooltip-content { font-size: 12px; line-height: 1.6; }

.branch-summary {
  display: flex;
  gap: 24px;
  padding-top: 10px;
  margin-top: 4px;
  border-top: 1px solid #1e3a5f;
  flex-wrap: wrap;
}
.summary-item { font-size: 11px; color: #64748b; }
.summary-item b { color: #94a3b8; }
.summary-item.cheap b     { color: #4ade80; }
.summary-item.expensive b { color: #f87171; }

.no-data {
  font-size: 12px;
  color: #475569;
  padding: 16px 0;
  text-align: center;
  font-style: italic;
}
</style>

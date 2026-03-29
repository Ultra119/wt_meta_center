<template>
  <div>
    <div class="controls-bar mb-3">
      <div class="controls-row">
        <v-select
          v-model="stepsPerBracket"
          :items="stepOptions"
          item-title="title"
          item-value="value"
          :label="t('brackets_tab.br_step')"
          density="compact"
          variant="outlined"
          hide-details
          style="width:130px"
        />
        <v-select
          v-model="topN"
          :items="topNOptions"
          item-title="label"
          item-value="value"
          :label="t('brackets_tab.top_n')"
          density="compact"
          variant="outlined"
          hide-details
          style="width:150px"
        />
        <v-select
          v-model="excludeTypes"
          :items="availableTypeOptions"
          item-title="label"
          item-value="value"
          :label="t('brackets_tab.excl_types')"
          density="compact"
          variant="outlined"
          hide-details
          multiple
          style="min-width:180px; max-width:300px"
        >
          <template #selection="{ index }">
            <div v-if="index === 0" class="excl-chips-row">
              <span
                v-for="type in excludeTypes.slice(0, 3)"
                :key="type"
                class="excl-chip"
                @click.stop="removeExcludeType(type)"
              >{{ getShortLabel(type) }} <span class="excl-chip-x">×</span></span>
              <span v-if="excludeTypes.length > 3" class="excl-overflow">
                +{{ excludeTypes.length - 3 }}
              </span>
            </div>
          </template>
        </v-select>
        <div class="tab-info">{{ t('brackets_tab.description') }}</div>
      </div>
    </div>

    <div v-if="pivot.rows.length" class="pivot-wrapper">
      <table class="pivot-table">
        <thead>
          <tr>
            <th class="br-col">{{ t('common.br') }}</th>
            <th v-for="nat in pivot.nations" :key="nat">{{ fmtNation(nat) }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in pivot.rows" :key="row.bracket">
            <td class="br-cell">{{ row.bracket }}</td>
            <td v-for="nat in pivot.nations" :key="nat" class="score-cell" :style="{ color: scoreColor(row[nat]) }">
              {{ row[nat] > 0 ? row[nat].toFixed(1) : '—' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <v-alert v-else type="info" variant="tonal" density="compact">
      {{ t('brackets_tab.no_data') }}
    </v-alert>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDataStore, WT_BR_STEPS } from '../stores/useDataStore.js'
import { metaColor, fmtNation } from '../composables/useVehicleFormatting.js'
import { BRANCH_TYPES, TYPE_LABELS, TYPE_ICON, LARGE_FLEET_TYPES, SMALL_FLEET_TYPES } from '../composables/constants.js'

const { t }  = useI18n()
const store  = useDataStore()

const stepsPerBracket = ref(3)
const topN            = ref(5)
const excludeTypes    = ref([])

const stepOptions = computed(() =>
  [1, 2, 3, 4, 6].map(n => ({
    value: n,
    title: `${(WT_BR_STEPS[n] - WT_BR_STEPS[0]).toFixed(1)} BR`,
  }))
)

const availableTypeOptions = computed(() => {
  const active = []
  if (store.showGround) {
    active.push(...BRANCH_TYPES.Ground)
  }
  if (store.showAviation) {
    active.push(...BRANCH_TYPES.Aviation)
  }
  if (store.showLargeFleet) {
    active.push(...[...LARGE_FLEET_TYPES])
  }
  if (store.showSmallFleet) {
    active.push(...[...SMALL_FLEET_TYPES])
  }
  return active.map(type => ({
    value:      type,
    label:      `${TYPE_ICON[type] ?? ''} ${t(`vehicle_types.${type}`, TYPE_LABELS[type] ?? type)}`,
    shortLabel: `${TYPE_ICON[type] ?? ''} ${(TYPE_LABELS[type] ?? type).replace(/^[^\s]+\s/, '')}`,
    icon:       TYPE_ICON[type] ?? '?',
  }))
})

watch(availableTypeOptions, (opts) => {
  const available = new Set(opts.map(o => o.value))
  excludeTypes.value = excludeTypes.value.filter(t => available.has(t))
})

function getShortLabel(type) {
  const opt = availableTypeOptions.value.find(o => o.value === type)
  return opt ? opt.shortLabel : type
}

function removeExcludeType(type) {
  excludeTypes.value = excludeTypes.value.filter(t => t !== type)
}

const topNOptions = computed(() => [
  { label: t('common.top_all'), value: 0 },
  { label: 'Top-3',  value: 3 },
  { label: 'Top-5',  value: 5 },
  { label: 'Top-7',  value: 7 },
  { label: 'Top-10', value: 10 },
])

function buildWtBrackets(stepsN) {
  const step = Math.max(1, stepsN)
  const n    = WT_BR_STEPS.length
  const boundaryIndices = []
  for (let i = 0; i < n; i += step) boundaryIndices.push(i)
  if (boundaryIndices[boundaryIndices.length - 1] !== n - 1) boundaryIndices.push(n - 1)
  const boundaryBrs = boundaryIndices.map(i => WT_BR_STEPS[i])
  return boundaryBrs.slice(0, -1).map((br, i) => ({
    label: step === 1 ? br.toFixed(1) : `${br.toFixed(1)}–${boundaryBrs[i + 1].toFixed(1)}`,
    min:   br,
    max:   boundaryBrs[i + 1] + 0.01,
  }))
}

function weightedMeta(pool) {
  if (!pool.length) return 0
  const total = pool.reduce((s, v) => s + (v['Сыграно игр'] ?? 0), 0)
  if (total < 1) return pool.reduce((s, v) => s + v.META_SCORE, 0) / pool.length
  return pool.reduce((s, v) => s + v.META_SCORE * (v['Сыграно игр'] ?? 0), 0) / total
}

const pivot = computed(() => {
  const excluded = new Set(excludeTypes.value)
  let vehicles = excluded.size
    ? store.filteredVehicles.filter(v => !excluded.has(v.Type))
    : store.filteredVehicles
  if (!vehicles.length) return { rows: [], nations: [] }

  const brackets = buildWtBrackets(stepsPerBracket.value)
  const nations  = [...new Set(vehicles.map(v => v.Nation))].sort()
  const n        = topN.value || null

  const rows = brackets.map(b => {
    const inBracket = vehicles.filter(v => v.BR >= b.min && v.BR < b.max)
    const row = { bracket: b.label }
    for (const nat of nations) {
      const pool = n
        ? [...inBracket.filter(v => v.Nation === nat)].sort((a, b) => b.META_SCORE - a.META_SCORE).slice(0, n)
        : inBracket.filter(v => v.Nation === nat)
      row[nat] = Math.round(weightedMeta(pool) * 10) / 10
    }
    return row
  })

  return { rows: rows.filter(r => nations.some(nat => r[nat] > 0)), nations }
})

function scoreColor(score) {
  if (!score) return '#334155'
  return metaColor(score)
}
</script>

<style scoped>
/* ── Shared controls-bar (mirrors ProgressionTab) ─────────────────── */
.controls-bar {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid #1e3a5f;
  border-radius: 10px;
  padding: 10px 14px;
}
.controls-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.tab-info { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #64748b; }

/* Single wrapper — row of custom chips */
.excl-chips-row {
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  align-items: center;
  gap: 4px;
  overflow: hidden;
  max-width: 100%;
}

.excl-chip {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 600;
  color: #a7f3d0;
  background: rgba(167, 243, 208, 0.08);
  border: 1px solid rgba(167, 243, 208, 0.25);
  border-radius: 4px;
  padding: 1px 5px;
  white-space: nowrap;
  cursor: pointer;
  transition: background 0.12s, border-color 0.12s;
}
.excl-chip:hover {
  background: rgba(248, 113, 113, 0.12);
  border-color: rgba(248, 113, 113, 0.4);
  color: #f87171;
}
.excl-chip-x { font-size: 11px; opacity: 0.6; }

.excl-overflow {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 700;
  color: #64748b;
  background: rgba(100, 116, 139, 0.12);
  border: 1px solid #334155;
  border-radius: 4px;
  padding: 1px 5px;
  white-space: nowrap;
  flex-shrink: 0;
}
.pivot-wrapper { overflow-x: auto; border: 1px solid #1e3a5f; border-radius: 8px; max-height: calc(100vh - 230px); overflow-y: auto; }
.pivot-table { border-collapse: collapse; width: 100%; font-family: 'JetBrains Mono', monospace; font-size: 12px; }
.pivot-table thead th {
  background: #1e293b; color: #a7f3d0; font-family: 'Rajdhani', sans-serif; font-weight: 600;
  font-size: 11px; letter-spacing: .08em; padding: 8px 12px; text-align: center;
  border-bottom: 1px solid #1e3a5f; white-space: nowrap; position: sticky; top: 0; z-index: 1;
}
.pivot-table tbody tr:hover td { background: #1e293b; }
.pivot-table td { background: #0f172a; color: #e2e8f0; padding: 6px 12px; text-align: center; border-bottom: 1px solid #1e293b; }
.br-col, .br-cell { text-align: left !important; padding-left: 14px !important; color: #94a3b8 !important; font-weight: 600; min-width: 100px; }
.score-cell { font-weight: 600; }
</style>

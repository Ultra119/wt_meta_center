<template>
  <v-navigation-drawer
    permanent
    :width="272"
    color="#0a1628"
    style="border-right: 1px solid #1e3a5f; top: 48px; height: calc(100% - 48px);"
  >
    <div class="pa-3">
        <div v-if="hiddenCount > 0" class="filters-hint">
          <span class="mdi mdi-filter-off-outline hint-icon" />
          {{ t('sidebar.filters_hidden', { n: hiddenCount }) }}
        </div>
      </Transition>

      <!-- Режим -->
      <div v-if="store.periods.length > 1" class="sidebar-section">
        <div class="sidebar-label">{{ t('sidebar.period') }}</div>
        <div class="seg-ctrl w-100 period-ctrl">
          <template v-if="store.periods.length <= 5">
            <button
              v-for="p in store.periods"
              :key="p"
              class="seg-btn period-btn"
              :class="{ 'seg-btn--active': store.currentPeriod === p }"
              :title="formatPeriodLabel(p)"
              @click="store.currentPeriod = p"
            >{{ periodShort(p) }}</button>
          </template>

          <template v-else>
            <v-select
              :model-value="store.currentPeriod"
              :items="periodItems"
              item-title="label"
              item-value="value"
              density="compact"
              variant="outlined"
              hide-details
              class="period-select"
              @update:model-value="v => store.currentPeriod = v"
            />
          </template>
        </div>
      </div>

      <!-- ── Mode ───────────────────────────────────────────────── -->
      <Transition name="section-fade">
        <div v-if="cfg.mode" class="sidebar-section">
        <div class="sidebar-label">{{ t('sidebar.mode') }}</div>
        <div class="seg-ctrl w-100">
          <button
            v-for="m in MODES"
            :key="m.value"
            class="seg-btn"
            :class="{ 'seg-btn--active': store.mode === m.value }"
            @click="store.mode = m.value"
          >{{ t(`modes.${m.value}`) }}</button>
        </div>
        </div>
      </Transition>

      <!-- BR диапазон -->
      <Transition name="section-fade">
        <div v-if="cfg.brRange" class="sidebar-section">
        <div class="sidebar-label">
          {{ t('sidebar.br_range') }}
          <span class="sidebar-value">{{ store.brRange[0].toFixed(1) }} – {{ store.brRange[1].toFixed(1) }}</span>
        </div>
        <v-range-slider
          :model-value="store.brRange"
          :min="store.BR_MIN"
          :max="store.BR_MAX"
          :step="0.1"
          color="primary"
          track-color="#1e293b"
          density="compact"
          class="mt-1"
          @update:model-value="v => store.brRange = v.map(snapBR)"
        />
        </div>
      </Transition>

      <!-- Минимум боёв -->
      <Transition name="section-fade">
        <div v-if="cfg.minBattles" class="sidebar-section">
        <div class="sidebar-label">{{ t('sidebar.min_battles') }}</div>
        <v-text-field
          v-model.number="store.minBattles"
          type="number"
          min="0"
          step="100"
          density="compact"
          variant="outlined"
          hide-details
          class="mt-1 battles-input"
        />
        </div>
      </Transition>

      <!-- Классы техники -->
      <Transition name="section-fade">
        <div v-if="cfg.classes" class="sidebar-section">
        <div class="sidebar-label">{{ t('sidebar.vehicle_class') }}</div>
        <div class="classes-grid">
          <v-checkbox
            v-for="cls in ALL_CLASSES"
            :key="cls"
            v-model="store.classes"
            :value="cls"
            :label="t(`vehicle_classes.${cls}`)"
            density="compact"
            hide-details
            color="primary"
            class="class-cb"
          />
        </div>
        </div>
      </Transition>

      <!-- Тип техники -->
      <Transition name="section-fade">
        <div v-if="cfg.types" class="sidebar-section">
        <div class="sidebar-label">{{ t('sidebar.vehicle_type') }}</div>
        <div class="type-grid">
          <v-checkbox v-model="store.showGround"     :label="t('sidebar.ground')"       density="compact" hide-details color="accent" class="type-cb" />
          <v-checkbox v-model="store.showAviation"    :label="t('sidebar.aviation')"     density="compact" hide-details color="accent" class="type-cb" />
          <v-checkbox v-model="store.showHelicopters" :label="t('sidebar.helicopters')"  density="compact" hide-details color="accent" class="type-cb" />
          <v-checkbox v-model="store.showLargeFleet" :label="t('sidebar.large_fleet')"  density="compact" hide-details color="accent" class="type-cb" />
          <v-checkbox v-model="store.showSmallFleet" :label="t('sidebar.small_fleet')"  density="compact" hide-details color="accent" class="type-cb" />
        </div>
        <v-alert v-if="mixWarning" type="warning" density="compact" variant="tonal" class="mt-2 text-caption">
          {{ mixWarning }}
        </v-alert>
        </div>
      </Transition>

      <!-- Датасет -->
      <div v-if="store.metaInfo" class="sidebar-section">
        <div class="sidebar-label">{{ t('common.dataset') }}</div>
        <div class="sidebar-info">
          <div>📦 {{ t('common.records', { n: store.metaInfo.total_records?.toLocaleString() }) }}</div>
          <div>{{ t('sidebar.dataset_date', { date: generatedDate }) }}</div>
        </div>
      </div>

    </div>
  </v-navigation-drawer>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n }  from 'vue-i18n'
import { useDataStore }     from '../stores/useDataStore.js'
import { formatPeriodLabel } from '../stores/useDataStore.js'

const { t }  = useI18n()
const store  = useDataStore()

const ALL_FILTER_KEYS = ['mode', 'brRange', 'minBattles', 'classes', 'types']

const cfg = computed(() => {
  const base = Object.fromEntries(ALL_FILTER_KEYS.map(k => [k, true]))
  return store.tabFilterConfig ? { ...base, ...store.tabFilterConfig } : base
})

const hiddenCount = computed(() =>
  ALL_FILTER_KEYS.filter(k => !cfg.value[k]).length
)

const ALL_CLASSES = ['Standard','Premium','Pack','Squadron','Marketplace','Gift','Event']
const MODES       = [
  { value: 'Realistic' },
  { value: 'Arcade'    },
  { value: 'Simulator' },
]

function periodShort(p) {
  if (!p || p === 'All') return 'All'
  const parts = p.split('-')
  if (parts.length !== 2) return p
  try {
    const d = new Date(parseInt(parts[1], 10), parseInt(parts[0], 10) - 1, 1)
    const mon = d.toLocaleDateString(undefined, { month: 'short' })
    const yr  = String(d.getFullYear()).slice(2)
    return `${mon}'${yr}`
  } catch {
    return p
  }
}

const periodItems = computed(() =>
  store.periods.map(p => ({ value: p, label: formatPeriodLabel(p) }))
)

const activePeriodRecords = computed(() => {
  const counts = store.metaInfo?.period_records
  if (!counts) return null
  return counts[store.currentPeriod] ?? null
})

function snapBR(val) {
  const base = Math.floor(val)
  const frac = val - base
  const snapped = [0, 0.3, 0.7].reduce((best, f) =>
    Math.abs(frac - f) < Math.abs(frac - best) ? f : best
  , 0)
  return parseFloat((base + snapped).toFixed(1))
}

const mixWarning = computed(() => {
  const fleet  = store.showLargeFleet || store.showSmallFleet
  const ground = store.showGround || store.showAviation || store.showHelicopters
  const none   = !store.showGround && !store.showAviation && !store.showLargeFleet && !store.showSmallFleet
  if (none)            return t('sidebar.warn_none')
  if (fleet && ground) return t('sidebar.warn_mix')
  return null
})

const generatedDate = computed(() => {
  const d = store.metaInfo?.generated_at
  if (!d) return '—'
  return new Date(d).toLocaleDateString(undefined, { day: '2-digit', month: '2-digit', year: 'numeric' })
})
</script>

<style scoped>
.sidebar-section {
  margin-bottom: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid #1e293b;
}
.sidebar-section:last-child { border-bottom: none; }
.sidebar-label {
  display: flex;
  justify-content: space-between;
  font-family: 'Rajdhani', sans-serif;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: #475569;
  margin-bottom: 6px;
  text-transform: uppercase;
}
.sidebar-value  { color: #a7f3d0; font-family: 'JetBrains Mono', monospace; }
.sidebar-info   { font-size: 11px; color: #475569; line-height: 1.6; }
.classes-grid   { display: grid; grid-template-columns: 1fr 1fr; gap: 0; }
.class-cb  :deep(.v-label) { font-size: 11px; color: #94a3b8; }
.type-grid  { display: flex; flex-direction: column; }
.type-cb   :deep(.v-label) { font-size: 12px; color: #e2e8f0; }
.battles-input { max-width: 120px; }
.battles-input :deep(input) {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  color: #a7f3d0;
}
.seg-ctrl {
  display: inline-flex;
  gap: 4px;
  background: rgba(10, 22, 40, 0.8);
  padding: 3px;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
}
.seg-btn {
  flex: 1;
  padding: 5px 10px;
  border: 1px solid transparent;
  border-radius: 5px;
  background: transparent;
  color: #475569;
  font-family: 'Rajdhani', sans-serif;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  cursor: pointer;
  white-space: nowrap;
  text-align: center;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}
.seg-btn:hover:not(.seg-btn--active) {
  color: #94a3b8;
  background: rgba(255, 255, 255, 0.04);
}
.seg-btn--active {
  background: rgba(56, 189, 248, 0.12);
  border-color: rgba(56, 189, 248, 0.5);
  color: #38bdf8;
}
.period-ctrl  { flex-wrap: wrap; }
.period-btn   { font-size: 10px; padding: 4px 6px; flex: 0 1 auto; }

.period-select { font-size: 12px; }
.filters-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
  padding: 6px 10px;
  background: rgba(167, 139, 250, 0.07);
  border: 1px solid rgba(167, 139, 250, 0.2);
  border-radius: 6px;
  font-size: 10px;
  color: #7c6fad;
  letter-spacing: 0.04em;
}
.hint-icon { font-size: 13px; flex-shrink: 0; }

.section-fade-enter-active,
.section-fade-leave-active { transition: opacity 0.2s ease, transform 0.2s ease, max-height 0.25s ease; max-height: 300px; overflow: hidden; }
.section-fade-enter-from,
.section-fade-leave-to     { opacity: 0; transform: translateY(-4px); max-height: 0; }

.hint-fade-enter-active,
.hint-fade-leave-active { transition: opacity 0.2s ease; }
.hint-fade-enter-from,
.hint-fade-leave-to     { opacity: 0; }

.period-select :deep(.v-field__input) {
  font-family: 'Rajdhani', sans-serif;
  font-size: 12px;
  font-weight: 700;
  color: #38bdf8;
  padding-top: 4px;
  padding-bottom: 4px;
  min-height: unset;
}
</style>

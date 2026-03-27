<template>
  <v-navigation-drawer
    permanent
    :width="272"
    color="#0a1628"
    style="border-right: 1px solid #1e3a5f; top: 48px; height: calc(100% - 48px);"
  >
    <div class="pa-3">

      <!-- Режим -->
      <div class="sidebar-section">
        <div class="sidebar-label">{{ t('sidebar.mode') }}</div>
        <v-btn-toggle v-model="store.mode" mandatory density="compact" rounded="lg" class="w-100">
          <v-btn value="Realistic" size="small" class="flex-grow-1">{{ t('modes.Realistic') }}</v-btn>
          <v-btn value="Arcade"    size="small" class="flex-grow-1">{{ t('modes.Arcade')    }}</v-btn>
          <v-btn value="Simulator" size="small" class="flex-grow-1">{{ t('modes.Simulator') }}</v-btn>
        </v-btn-toggle>
      </div>

      <!-- BR диапазон -->
      <div class="sidebar-section">
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

      <!-- Минимум боёв -->
      <div class="sidebar-section">
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

      <!-- Классы техники -->
      <div class="sidebar-section">
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

      <!-- Тип техники -->
      <div class="sidebar-section">
        <div class="sidebar-label">{{ t('sidebar.vehicle_type') }}</div>
        <div class="type-grid">
          <v-checkbox v-model="store.showGround"     :label="t('sidebar.ground')"       density="compact" hide-details color="accent" class="type-cb" />
          <v-checkbox v-model="store.showAviation"   :label="t('sidebar.aviation')"     density="compact" hide-details color="accent" class="type-cb" />
          <v-checkbox v-model="store.showLargeFleet" :label="t('sidebar.large_fleet')"  density="compact" hide-details color="accent" class="type-cb" />
          <v-checkbox v-model="store.showSmallFleet" :label="t('sidebar.small_fleet')"  density="compact" hide-details color="accent" class="type-cb" />
        </div>
        <v-alert v-if="mixWarning" type="warning" density="compact" variant="tonal" class="mt-2 text-caption">
          {{ mixWarning }}
        </v-alert>
      </div>

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
import { useDataStore } from '../stores/useDataStore.js'

const { t }  = useI18n()
const store  = useDataStore()

const ALL_CLASSES = ['Standard','Premium','Pack','Squadron','Marketplace','Gift','Event']

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
  const ground = store.showGround     || store.showAviation
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
.sidebar-value { color: #a7f3d0; font-family: 'JetBrains Mono', monospace; }
.classes-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0; }
.class-cb :deep(.v-label) { font-size: 11px; color: #94a3b8; }
.type-grid { display: flex; flex-direction: column; }
.type-cb :deep(.v-label) { font-size: 12px; color: #e2e8f0; }
.battles-input { max-width: 120px; }
.battles-input :deep(input) {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  color: #a7f3d0;
}
</style>
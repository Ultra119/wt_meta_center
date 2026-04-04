<template>
  <div>
    <div class="controls-bar mb-4">
      <div class="controls-row">

        <div class="br-slider-wrap">
          <div class="br-slider-header">
            <span class="br-slider-title">{{ t('farm_tab.target_br') }}</span>
            <span class="br-value-badge">{{ displayBR(targetBr) }}</span>
          </div>
          <v-slider
            v-model="brIndex"
            :min="0"
            :max="WT_BR_STEPS.length - 1"
            :step="1"
            hide-details
            color="#a78bfa"
            track-color="#1e3a5f"
            thumb-color="#a78bfa"
            class="br-slider"
          />
        </div>

        <v-divider vertical class="ctrl-divider" />

        <v-select
          v-model="nation"
          :items="nationItems"
          item-title="title"
          item-value="value"
          :label="t('farm_tab.nation')"
          prepend-inner-icon="mdi-flag"
          density="compact"
          variant="outlined"
          hide-details
          style="max-width:200px"
        />

        <v-select
          v-model="vehicleType"
          :items="typeOptions"
          :label="t('farm_tab.veh_type')"
          density="compact"
          variant="outlined"
          hide-details
          style="max-width:180px"
        />

        <InfoTip align="right" class="ml-auto">
          <p><b>{{ t('tabs.farm') }}</b></p>
          <p>{{ t('farm_tab.tip_desc') }}</p>
          <div class="tip-row" style="margin-top:8px">
            <span class="tip-icon">⚓</span>
            <span><b class="tip-label">{{ t('farm_tab.role_anchor') }}</b> — {{ t('farm_tab.tip_anchor') }}</span>
          </div>
          <div class="tip-row">
            <span class="tip-icon">💎</span>
            <span><b class="tip-label">{{ t('farm_tab.gems_label') }}</b> — {{ t('farm_tab.tip_gems') }}</span>
          </div>
        </InfoTip>
      </div>
    </div>

    <template v-if="result">

      <div class="anchor-banner mb-4">
        <div class="anchor-left">
          <span class="anchor-icon">⚓</span>
          <div class="anchor-info">
            <span class="anchor-label">{{ t('farm_tab.anchor_label') }}</span>
            <span class="anchor-name">{{ vehicleDisplayName(result.anchor) }}</span>
            <span class="anchor-br">{{ displayBR(result.anchor.BR) }}</span>
          </div>
        </div>
        <div class="anchor-right">
          <div class="anchor-score-label">{{ t('farm_tab.anchor_farm') }}</div>
          <div class="anchor-score-value">{{ result.anchor.FARM_SCORE?.toFixed(1) }}</div>
          <div class="anchor-score-bar">
            <div class="anchor-score-fill" :style="{ width: result.anchor.FARM_SCORE + '%' }" />
          </div>
        </div>
      </div>

      <div class="section-header mb-2">
        <span class="section-title">{{ t('farm_tab.main_set') }}</span>
        <span class="section-sub">BR {{ displayBR(targetBr - 1.0) }} – {{ displayBR(targetBr) }}</span>
      </div>
      <div class="table-wrap mb-5">
        <v-data-table
          :headers="farmHeaders"
          :items="mainSetRows"
          :items-per-page="-1"
          hide-default-footer
          density="compact"
          class="wt-table"
          @click:row="(_, { item }) => openVehicle(item)"
        >
          <template #item.Роль="{ item }">
            <v-chip
              :color="roleColor(item.Роль)"
              size="x-small"
              variant="tonal"
              class="role-chip"
            >{{ item.Роль }}</v-chip>
          </template>
          <template #item.Name_Display="{ item }">
            <span class="cell-name">{{ item.Name_Display }}</span>
          </template>
          <template #item.BR="{ item }">
            <span class="cell-br">{{ displayBR(item.BR) }}</span>
          </template>
          <template #item.FARM_SCORE="{ item }">
            <div class="score-cell">
              <span :style="{ color: farmColor(item.FARM_SCORE) }">{{ item.FARM_SCORE?.toFixed(1) }}</span>
              <div class="score-bar-bg">
                <div class="score-bar-fill" :style="{ width: item.FARM_SCORE + '%', background: farmColor(item.FARM_SCORE) }" />
              </div>
            </div>
          </template>
          <template #item.net_sl="{ item }">
            <span class="cell-sl">{{ item.net_sl?.toLocaleString() }}</span>
          </template>
        </v-data-table>
      </div>

      <div class="section-header mb-2">
        <span class="section-title gems-title">{{ t('farm_tab.gems') }}</span>
        <span class="section-sub">BR {{ displayBR(targetBr - 2.0) }} – {{ displayBR(targetBr - 1.0) }}</span>
      </div>
      <template v-if="result.gems.length">
        <div class="table-wrap">
          <v-data-table
            :headers="gemHeaders"
            :items="gemRows"
            :items-per-page="-1"
            hide-default-footer
            density="compact"
            class="wt-table"
            @click:row="(_, { item }) => openVehicle(item)"
          >
            <template #item.Name_Display="{ item }">
              <span class="cell-name">{{ item.Name_Display }}</span>
            </template>
            <template #item.BR="{ item }">
              <span class="cell-br">{{ displayBR(item.BR) }}</span>
            </template>
            <template #item.FARM_SCORE="{ item }">
              <div class="score-cell">
                <span :style="{ color: farmColor(item.FARM_SCORE) }">{{ item.FARM_SCORE?.toFixed(1) }}</span>
                <div class="score-bar-bg">
                  <div class="score-bar-fill" :style="{ width: item.FARM_SCORE + '%', background: farmColor(item.FARM_SCORE) }" />
                </div>
              </div>
            </template>
            <template #item.delta="{ item }">
              <span class="cell-delta">+{{ item.delta }}%</span>
            </template>
          </v-data-table>
        </div>
      </template>
      <p v-else class="text-muted-sm">{{ t('farm_tab.gems_empty') }}</p>
    </template>

    <v-alert v-else-if="noAnchor" type="error" variant="tonal" density="compact">
      {{ t('farm_tab.no_anchor') }}
    </v-alert>
  </div>
</template>

<script setup>
import { ref, computed, inject } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDataStore, WT_BR_STEPS } from '../stores/useDataStore.js'
import { vehicleDisplayName, farmColor, normRow } from '../composables/useVehicleFormatting.js'
import { TYPE_CATEGORIES } from '../composables/constants.js'
import InfoTip from '../components/InfoTip.vue'

const { t }       = useI18n()
const store       = useDataStore()
const openVehicle = inject('openVehicle')

const DEFAULT_BR  = 7.0
const brIndex     = ref(WT_BR_STEPS.indexOf(DEFAULT_BR) !== -1 ? WT_BR_STEPS.indexOf(DEFAULT_BR) : 0)
const targetBr    = computed(() => WT_BR_STEPS[brIndex.value])

function displayBR(br) {
  const n = parseFloat(br)
  return isNaN(n) ? '—' : n.toFixed(1)
}

const nation      = ref('All')
const vehicleType = ref('All')

const nationItems = computed(() =>
  (store.nations ?? []).map(n => ({
    title: n === 'All' ? t('common.all') : n,
    value: n,
  }))
)

const typeOptions = computed(() => {
  const cats = [t('common.all')]
  if (store.showGround)      cats.push(t('sidebar.ground'))
  if (store.showAviation)    cats.push(t('sidebar.aviation'))
  if (store.showHelicopters) cats.push(t('sidebar.helicopters'))
  if (store.showLargeFleet)  cats.push(t('sidebar.large_fleet'))
  if (store.showSmallFleet)  cats.push(t('sidebar.small_fleet'))
  return cats
})

function getFarmSet(vehicles, tBr, nat, vType) {
  let df = [...vehicles]
  if (nat !== 'All') df = df.filter(v => v.Nation === nat)

  const catKeyByLabel = {
    [t('sidebar.ground')]:      'Ground',
    [t('sidebar.aviation')]:    'Aviation',
    [t('sidebar.helicopters')]: 'Helicopters',
    [t('sidebar.large_fleet')]: 'LargeFleet',
    [t('sidebar.small_fleet')]: 'SmallFleet',
  }
  const catKey = catKeyByLabel[vType]
  if (catKey) df = df.filter(v => (TYPE_CATEGORIES[catKey] ?? []).includes(v.Type))

  const anchor = df
    .filter(v => Math.abs(v.BR - tBr) <= 0.15)
    .sort((a, b) => b.FARM_SCORE - a.FARM_SCORE)[0]
  if (!anchor) return null

  const anchorFarm = anchor.FARM_SCORE ?? 0

  const mainSet = df
    .filter(v => v.BR >= tBr - 1.0 && v.BR <= tBr + 0.15)
    .sort((a, b) => b.FARM_SCORE - a.FARM_SCORE)
    .slice(0, 7)
    .map(v => ({
      ...v,
      Роль: Math.abs(v.BR - tBr) <= 0.15        ? t('farm_tab.role_anchor')
           : v.FARM_SCORE >= anchorFarm * 0.9   ? t('farm_tab.role_top')
           : t('farm_tab.role_reserve'),
    }))

  const gems = df
    .filter(v => v.BR >= tBr - 2.0 && v.BR < tBr - 0.85 && v.FARM_SCORE > anchorFarm)
    .sort((a, b) => b.FARM_SCORE - a.FARM_SCORE)
    .slice(0, 5)
    .map(v => ({
      ...v,
      _delta: anchorFarm > 0
        ? Math.round(((v.FARM_SCORE - anchorFarm) / anchorFarm) * 100)
        : 0,
    }))

  return { anchor, mainSet, gems }
}

const result   = computed(() =>
  getFarmSet(store.filteredVehicles, targetBr.value, nation.value, vehicleType.value)
)
const noAnchor = computed(() => !result.value)

function toRows(list) {
  return list.map(v => ({
    ...normRow(v),
    Name_Display: vehicleDisplayName(v),
    delta: v._delta ?? 0,
  }))
}
const mainSetRows = computed(() => toRows(result.value?.mainSet ?? []))
const gemRows     = computed(() => toRows(result.value?.gems    ?? []))

function roleColor(role) {
  if (role === t('farm_tab.role_anchor')) return '#a78bfa'  // purple — anchor
  if (role === t('farm_tab.role_top'))    return '#34d399'  // green  — top farmer
  return '#64748b'                                          // grey   — reserve
}

const farmHeaders = computed(() => [
  { title: t('farm_tab.role'),        key: 'Роль',         width: 120, sortable: false },
  { title: t('farm_tab.col_vehicle'), key: 'Name_Display', width: 200 },
  { title: t('common.br'),            key: 'BR',           width: 65  },
  { title: t('common.battles'),       key: 'battles',      width: 80  },
  { title: t('common.wr'),            key: 'WR',           width: 65  },
  { title: t('common.kd'),            key: 'KD',           width: 60  },
  { title: t('farm_tab.col_farm'),    key: 'FARM_SCORE',   width: 120 },
  { title: t('farm_tab.col_net_sl'),  key: 'net_sl',       width: 110 },
])

const gemHeaders = computed(() => [
  { title: t('farm_tab.col_vehicle'), key: 'Name_Display', width: 200 },
  { title: t('common.br'),            key: 'BR',           width: 65  },
  { title: t('common.battles'),       key: 'battles',      width: 80  },
  { title: t('farm_tab.col_farm'),    key: 'FARM_SCORE',   width: 120 },
  { title: '↑ vs anchor',             key: 'delta',        width: 90  },
])
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
  gap: 14px;
}
.ctrl-divider {
  align-self: stretch;
  opacity: 0.3;
}
.ml-auto { margin-left: auto; }

.br-slider-wrap {
  min-width: 200px;
  max-width: 280px;
  flex: 1;
}
.br-slider-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2px;
}
.br-slider-title {
  font-size: 11px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: .06em;
}
.br-value-badge {
  font-family: 'Rajdhani', sans-serif;
  font-size: 20px;
  font-weight: 700;
  color: #a78bfa;
  line-height: 1;
  min-width: 38px;
  text-align: right;
}
.br-slider :deep(.v-slider-thumb__label) { display: none; }
.br-slider :deep(.v-slider-track__fill)  { border-radius: 4px; }

.anchor-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: rgba(30, 58, 95, 0.5);
  border: 1px solid #10b981;
  border-radius: 10px;
  padding: 12px 16px;
}
.anchor-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.anchor-icon { font-size: 22px; }
.anchor-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.anchor-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: .08em;
  color: #64748b;
}
.anchor-name {
  font-family: 'Rajdhani', sans-serif;
  font-size: 16px;
  font-weight: 700;
  color: #a7f3d0;
}
.anchor-br {
  font-size: 12px;
  color: #94a3b8;
}
.anchor-right {
  text-align: right;
  min-width: 100px;
}
.anchor-score-label {
  font-size: 10px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: .06em;
}
.anchor-score-value {
  font-family: 'Rajdhani', sans-serif;
  font-size: 24px;
  font-weight: 700;
  color: #a78bfa;
  line-height: 1.1;
}
.anchor-score-bar {
  height: 3px;
  background: #1e3a5f;
  border-radius: 2px;
  margin-top: 4px;
  overflow: hidden;
}
.anchor-score-fill {
  height: 100%;
  background: #a78bfa;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.section-header {
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.section-title {
  font-family: 'Rajdhani', sans-serif;
  font-size: 13px;
  font-weight: 700;
  color: #a7f3d0;
  letter-spacing: .08em;
  text-transform: uppercase;
}
.gems-title { color: #a78bfa; }
.section-sub {
  font-size: 11px;
  color: #475569;
}

.table-wrap {
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  overflow: hidden;
}
.cell-name  { font-weight: 600; color: #e2e8f0; }
.cell-br    { font-family: 'Rajdhani', sans-serif; font-weight: 600; color: #94a3b8; }
.cell-sl    { color: #34d399; font-weight: 600; }
.cell-delta { color: #a78bfa; font-weight: 700; font-size: 12px; }

.role-chip { font-size: 10px !important; font-weight: 700; }

.score-cell {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 80px;
}
.score-bar-bg {
  height: 3px;
  background: rgba(100,116,139,0.2);
  border-radius: 2px;
  overflow: hidden;
}
.score-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.2s;
}

.text-muted-sm {
  font-size: 11px;
  color: #475569;
  font-style: italic;
  padding: 8px 0;
}
</style>

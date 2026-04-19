<template>
  <div>

    <div class="controls-bar mb-4">
      <div class="controls-row">

        <div class="br-ctrl">
          <div class="ctrl-label">{{ t('farm_tab.target_br') }}</div>
          <div class="br-ctrl-inner">
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
            <span class="br-badge">{{ fmtBR(targetBr) }}</span>
          </div>
        </div>

        <div class="ctrl-divider" />

        <div>
          <div class="ctrl-label">{{ t('farm_tab.nation') }}</div>
          <v-select
            v-model="nation"
            :items="nationItems"
            item-title="title"
            item-value="value"
            density="compact"
            variant="outlined"
            hide-details
            style="min-width:150px"
          />
        </div>

        <InfoTip align="right" class="ml-auto">
          <p><b>{{ t('tabs.farm') }}</b></p>
          <p>{{ t('farm_tab.tip_desc') }}</p>
          <div class="tip-row" style="margin-top:8px">
            <span class="mdi mdi-anchor tip-icon" />
            <span><b>{{ t('farm_tab.role_anchor') }}</b> — {{ t('farm_tab.tip_anchor') }}</span>
          </div>
          <div class="tip-row">
            <span class="mdi mdi-diamond-stone tip-icon" style="color:#a78bfa" />
            <span><b>{{ t('farm_tab.gems_label') }}</b> — {{ t('farm_tab.tip_gems') }}</span>
          </div>
        </InfoTip>

      </div>
    </div>

    <div v-if="store.filtering" class="no-data">
      <span class="mdi mdi-loading mdi-spin" style="margin-right:6px" />{{ t('common.loading') }}
    </div>

    <div v-else-if="noAnchor" class="no-data">
      {{ t('farm_tab.no_anchor') }}
    </div>

    <template v-else-if="result">

      <div class="anchor-banner mb-4">
        <div class="anchor-left">
          <span class="mdi mdi-anchor anchor-icon" />
          <div class="anchor-info">
            <span class="ctrl-label">{{ t('farm_tab.anchor_label') }}</span>
            <span class="anchor-name">
              <span
                v-if="anchorClassIcon"
                class="mdi cell-class-icon"
                :class="anchorClassIcon"
                :style="anchorClassColor ? `color:${anchorClassColor}` : ''"
              />
              {{ vehicleDisplayName(result.anchor) }}
            </span>
            <span class="anchor-meta">
              BR {{ fmtBR(result.anchor.BR) }}
              &nbsp;·&nbsp;
              {{ t('farm_tab.anchor_farm') }} <b style="color:#a78bfa">{{ result.anchor.FARM_SCORE?.toFixed(1) }}</b>
            </span>
          </div>
        </div>
        <div class="anchor-bar-wrap">
          <div class="anchor-bar-bg">
            <div class="anchor-bar-fill" :style="{ width: result.anchor.FARM_SCORE + '%' }" />
          </div>
          <span class="anchor-score">{{ result.anchor.FARM_SCORE?.toFixed(1) }}</span>
        </div>
      </div>

      <div class="section-header mb-2">
        <span class="mdi mdi-tools" style="margin-right:5px;opacity:.7" />
        <span class="section-title">{{ t('farm_tab.main_set') }}</span>
        <span class="section-sub">BR {{ fmtBR(targetBr - 1.0) }} – {{ fmtBR(targetBr) }}</span>
      </div>

      <div class="table-wrap mb-5">
        <v-data-table
          :headers="farmHeaders"
          :items="mainSetRows"
          :items-per-page="-1"
          hide-default-footer
          density="compact"
          class="wt-table"
          :row-props="rowProps"
          @click:row="(_, { item }) => openVehicle(item)"
        >
          <template #item.role="{ item }">
            <span class="role-badge" :style="{ color: roleColor(item.role), borderColor: roleColor(item.role) + '44' }">
              {{ item.role }}
            </span>
          </template>
          <template #item.Name_Display="{ item }">
            <span class="cell-name">
              <span v-if="item.classIcon" class="mdi cell-class-icon" :class="item.classIcon" :style="item.classColor ? `color:${item.classColor}` : ''" />
              {{ item.Name_Display }}
            </span>
          </template>
          <template #item.BR="{ item }">
            <span style="font-family:'Rajdhani',sans-serif;font-weight:600;color:#94a3b8">{{ fmtBR(item.BR) }}</span>
          </template>
          <template #item.FARM_SCORE="{ item }">
            <div class="score-cell">
              <span class="cell-score" :style="{ color: farmColor(item.FARM_SCORE) }">{{ item.FARM_SCORE?.toFixed(1) }}</span>
              <div class="score-bar-bg">
                <div class="score-bar-fill" :style="{ width: item.FARM_SCORE + '%', background: farmColor(item.FARM_SCORE) }" />
              </div>
            </div>
          </template>
          <template #item.net_sl="{ item }">
            <span style="color:#34d399;font-weight:600">{{ item.net_sl != null ? item.net_sl.toLocaleString() : '—' }}</span>
          </template>
        </v-data-table>
      </div>

      <div class="section-header mb-2">
        <span class="mdi mdi-diamond-stone" style="margin-right:5px;color:#a78bfa" />
        <span class="section-title" style="color:#a78bfa">{{ t('farm_tab.gems') }}</span>
        <span class="section-sub">BR {{ fmtBR(targetBr - 2.0) }} – {{ fmtBR(targetBr - 1.0) }}</span>
      </div>

      <div v-if="gemRows.length" class="table-wrap">
        <v-data-table
          :headers="gemHeaders"
          :items="gemRows"
          :items-per-page="-1"
          hide-default-footer
          density="compact"
          class="wt-table"
          :row-props="rowProps"
          @click:row="(_, { item }) => openVehicle(item)"
        >
          <template #item.Name_Display="{ item }">
            <span class="cell-name">
              <span v-if="item.classIcon" class="mdi cell-class-icon" :class="item.classIcon" :style="item.classColor ? `color:${item.classColor}` : ''" />
              {{ item.Name_Display }}
            </span>
          </template>
          <template #item.BR="{ item }">
            <span style="font-family:'Rajdhani',sans-serif;font-weight:600;color:#94a3b8">{{ fmtBR(item.BR) }}</span>
          </template>
          <template #item.FARM_SCORE="{ item }">
            <div class="score-cell">
              <span class="cell-score" :style="{ color: farmColor(item.FARM_SCORE) }">{{ item.FARM_SCORE?.toFixed(1) }}</span>
              <div class="score-bar-bg">
                <div class="score-bar-fill" :style="{ width: item.FARM_SCORE + '%', background: farmColor(item.FARM_SCORE) }" />
              </div>
            </div>
          </template>
          <template #item.delta="{ item }">
            <span style="color:#a78bfa;font-weight:700">+{{ item.delta }}%</span>
          </template>
        </v-data-table>
      </div>
      <p v-else class="no-data">{{ t('farm_tab.gems_empty') }}</p>

    </template>

  </div>
</template>

<script setup>
import { ref, shallowRef, computed, watchEffect, nextTick, inject } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTabFilters }   from '../composables/useTabFilters.js'
import { useDataStore, WT_BR_STEPS } from '../stores/useDataStore.js'
import {
  vehicleDisplayName, vehicleClassMdiIcon, vehicleClassMdiColor,
  farmColor, fmtBR, fmtNation, normRow,
} from '../composables/useVehicleFormatting.js'
import InfoTip from '../components/InfoTip.vue'

const { t }       = useI18n()
const store       = useDataStore()
const openVehicle = inject('openVehicle')

useTabFilters()

const DEFAULT_BR = 7.0
const brIndex    = ref(WT_BR_STEPS.indexOf(DEFAULT_BR) !== -1 ? WT_BR_STEPS.indexOf(DEFAULT_BR) : 0)
const targetBr   = computed(() => WT_BR_STEPS[brIndex.value])

const nation = ref('All')
const nationItems = computed(() =>
  (store.nations ?? []).map(n => ({
    title: n === 'All' ? t('common.all') : fmtNation(n),
    value: n,
  }))
)

function buildFarmSet(vehicles, tBr, nat) {
  const df = nat === 'All' ? vehicles : vehicles.filter(v => v.Nation === nat)

  const anchor = df
    .filter(v => Math.abs(v.BR - tBr) <= 0.15)
    .sort((a, b) => (b.FARM_SCORE ?? 0) - (a.FARM_SCORE ?? 0))[0]
  if (!anchor) return null

  const anchorFarm = anchor.FARM_SCORE ?? 0

  const mainSet = df
    .filter(v => v.BR >= tBr - 1.0 && v.BR <= tBr + 0.15)
    .sort((a, b) => (b.FARM_SCORE ?? 0) - (a.FARM_SCORE ?? 0))
    .slice(0, 7)
    .map(v => ({
      ...v,
      role: Math.abs(v.BR - tBr) <= 0.15
        ? t('farm_tab.role_anchor')
        : (v.FARM_SCORE ?? 0) >= anchorFarm * 0.9
          ? t('farm_tab.role_top')
          : t('farm_tab.role_reserve'),
    }))

  const gems = df
    .filter(v => v.BR >= tBr - 2.0 && v.BR < tBr - 0.85 && (v.FARM_SCORE ?? 0) > anchorFarm)
    .sort((a, b) => (b.FARM_SCORE ?? 0) - (a.FARM_SCORE ?? 0))
    .slice(0, 5)
    .map(v => ({
      ...v,
      _delta: anchorFarm > 0
        ? Math.round(((v.FARM_SCORE - anchorFarm) / anchorFarm) * 100)
        : 0,
    }))

  return { anchor, mainSet, gems }
}

function toRows(list) {
  return list.map(v => ({
    ...normRow(v),
    Name_Display: vehicleDisplayName(v),
    classIcon:    vehicleClassMdiIcon(v),
    classColor:   vehicleClassMdiColor(v),
    delta:        v._delta ?? 0,
  }))
}

const result      = shallowRef(null)
const noAnchor    = shallowRef(false)
const mainSetRows = shallowRef([])
const gemRows     = shallowRef([])

watchEffect(() => {
  const vehicles = store.filteredVehicles
  const tBr      = targetBr.value
  const nat      = nation.value
  nextTick(() => {
    const r        = buildFarmSet(vehicles, tBr, nat)
    result.value   = r
    noAnchor.value = !r
    mainSetRows.value = toRows(r?.mainSet ?? [])
    gemRows.value     = toRows(r?.gems    ?? [])
  })
})

const anchorClassIcon  = computed(() => result.value ? vehicleClassMdiIcon(result.value.anchor)  : null)
const anchorClassColor = computed(() => result.value ? vehicleClassMdiColor(result.value.anchor) : null)

function rowProps({ index }) {
  return { class: index % 2 === 0 ? 'row-even' : 'row-odd' }
}

function roleColor(role) {
  if (role === t('farm_tab.role_anchor')) return '#a78bfa'
  if (role === t('farm_tab.role_top'))    return '#34d399'
  return '#64748b'
}

const farmHeaders = computed(() => [
  { title: t('farm_tab.role'),        key: 'role',         width: 110, sortable: false },
  { title: t('farm_tab.col_vehicle'), key: 'Name_Display', sortable: false },
  { title: t('common.br'),            key: 'BR',           width: 65  },
  { title: t('common.battles'),       key: 'battles',      width: 80  },
  { title: t('common.wr'),            key: 'WR',           width: 65  },
  { title: t('farm_tab.col_farm'),    key: 'FARM_SCORE',   width: 130 },
  { title: t('farm_tab.col_net_sl'),  key: 'net_sl',       width: 110 },
])

const gemHeaders = computed(() => [
  { title: t('farm_tab.col_vehicle'), key: 'Name_Display', sortable: false },
  { title: t('common.br'),            key: 'BR',           width: 65  },
  { title: t('common.battles'),       key: 'battles',      width: 80  },
  { title: t('farm_tab.col_farm'),    key: 'FARM_SCORE',   width: 130 },
  { title: '↑ vs anchor',            key: 'delta',        width: 90  },
])
</script>

<style scoped>
.br-ctrl { flex: 1; min-width: 180px; max-width: 300px; }
.br-ctrl-inner {
  display: flex;
  align-items: center;
  gap: 8px;
}
.br-badge {
  font-family: 'Rajdhani', sans-serif;
  font-size: 22px;
  font-weight: 700;
  color: #a78bfa;
  line-height: 1;
  min-width: 42px;
  text-align: right;
  flex-shrink: 0;
}
.br-slider :deep(.v-slider-thumb__label) { display: none; }

.anchor-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: rgba(167, 139, 250, 0.05);
  border: 1px solid rgba(167, 139, 250, 0.3);
  border-radius: 10px;
  padding: 12px 16px;
}
.anchor-left  { display: flex; align-items: center; gap: 12px; }
.anchor-icon  { font-size: 20px; color: #a7f3d0; flex-shrink: 0; }
.anchor-info  { display: flex; flex-direction: column; gap: 2px; }
.anchor-name  {
  font-family: 'Rajdhani', sans-serif;
  font-size: 17px;
  font-weight: 700;
  color: #a7f3d0;
}
.anchor-meta { font-size: 11px; color: #64748b; }

.anchor-bar-wrap {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  min-width: 110px;
}
.anchor-score {
  font-family: 'Rajdhani', sans-serif;
  font-size: 26px;
  font-weight: 700;
  color: #a78bfa;
  line-height: 1;
}
.anchor-bar-bg {
  width: 100%;
  height: 3px;
  background: #1e3a5f;
  border-radius: 2px;
  overflow: hidden;
}
.anchor-bar-fill {
  height: 100%;
  background: #a78bfa;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.section-header  { display: flex; align-items: baseline; gap: 8px; }
.section-title {
  font-family: 'Rajdhani', sans-serif;
  font-size: 12px;
  font-weight: 700;
  color: #a7f3d0;
  letter-spacing: .1em;
  text-transform: uppercase;
}
.section-sub { font-size: 11px; color: #475569; }

.role-badge {
  display: inline-block;
  font-family: 'Rajdhani', sans-serif;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .06em;
  text-transform: uppercase;
  padding: 2px 7px;
  border: 1px solid;
  border-radius: 4px;
  white-space: nowrap;
  background: transparent;
}

.score-cell { display: flex; flex-direction: column; gap: 3px; min-width: 80px; }
.score-bar-bg {
  height: 3px;
  background: rgba(100, 116, 139, 0.2);
  border-radius: 2px;
  overflow: hidden;
}
.score-bar-fill { height: 100%; border-radius: 2px; transition: width 0.2s; }
</style>

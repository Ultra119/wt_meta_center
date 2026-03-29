<template>
  <div>
    <div class="controls-bar mb-4">
      <div class="controls-row">
        <v-select
          v-model="targetBr"
          :items="brOptions"
          item-title="label"
          item-value="value"
          :label="t('farm_tab.target_br')"
          prepend-inner-icon="mdi-target"
          density="compact"
          variant="outlined"
          hide-details
          style="width:130px"
        />
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
          style="max-width:220px"
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
        <v-btn color="primary" prepend-icon="mdi-calculator" @click="calculate">
          {{ t('common.calculate') }}
        </v-btn>
      </div>
    </div>

    <template v-if="result">
      <v-alert color="#1e3a5f" class="mb-4" style="border:1px solid #10b981;">
        <span style="color:#a7f3d0; font-size:14px;">
          <b>{{ t('farm_tab.anchor_label') }}</b>
          {{ vehicleDisplayName(result.anchor) }}
          <span style="color:#94a3b8;">{{ t('farm_tab.anchor_br', { br: fmtBR(result.anchor.BR) }) }}</span>
          · {{ t('farm_tab.anchor_farm') }}
          <b style="color:#a78bfa;">{{ result.anchor.FARM_SCORE?.toFixed(1) }}</b>
        </span>
      </v-alert>

      <div class="section-title">{{ t('farm_tab.main_set') }}</div>
      <v-data-table
        :headers="farmHeaders"
        :items="mainSetRows"
        :items-per-page="10"
        density="compact"
        class="wt-table mb-4"
        @click:row="(_, { item }) => openVehicle(item)"
      >
        <template #item.Name_Display="{ item }"><span class="cell-name">{{ item.Name_Display }}</span></template>
        <template #item.FARM_SCORE="{ item }">
          <span :style="{ color: farmColor(item.FARM_SCORE) }">{{ item.FARM_SCORE?.toFixed(1) }}</span>
        </template>
        <template #item.net_sl="{ item }">
          <span style="color:#34d399;">{{ item.net_sl?.toLocaleString() }}</span>
        </template>
      </v-data-table>

      <div class="section-title" style="color:#a78bfa;">{{ t('farm_tab.gems') }}</div>
      <template v-if="result.gems.length">
        <v-data-table
          :headers="gemHeaders"
          :items="gemRows"
          :items-per-page="5"
          density="compact"
          class="wt-table"
          @click:row="(_, { item }) => openVehicle(item)"
        >
          <template #item.Name_Display="{ item }"><span class="cell-name">{{ item.Name_Display }}</span></template>
          <template #item.FARM_SCORE="{ item }">
            <span :style="{ color: farmColor(item.FARM_SCORE) }">{{ item.FARM_SCORE?.toFixed(1) }}</span>
          </template>
        </v-data-table>
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
import { vehicleDisplayName, fmtBR, fmtNation, farmColor, normRow } from '../composables/useVehicleFormatting.js'
import { TYPE_CATEGORIES } from '../composables/constants.js'

const { t }       = useI18n()
const store       = useDataStore()
const openVehicle = inject('openVehicle')

const brOptions   = WT_BR_STEPS.map(br => ({ label: br.toFixed(1), value: br }))
const targetBr    = ref(7.0)
const nation      = ref('All')
const vehicleType = ref('All')
const result      = ref(null)
const noAnchor    = ref(false)

const nationItems = computed(() =>
  (store.nations ?? []).map(n => ({
    title: n === 'All' ? t('common.all') : fmtNation(n),
    value: n,
  }))
)

const typeOptions = computed(() => {
  const cats = [t('common.all')]
  if (store.showGround)     cats.push(t('sidebar.ground'))
  if (store.showAviation)   cats.push(t('sidebar.aviation'))
  if (store.showLargeFleet) cats.push(t('sidebar.large_fleet'))
  if (store.showSmallFleet) cats.push(t('sidebar.small_fleet'))
  return cats
})

function getFarmSet(vehicles, tBr, nat, vType) {
  let df = [...vehicles]
  if (nat !== 'All') df = df.filter(v => v.Nation === nat)

  const catKeyByLabel = {
    [t('sidebar.ground')]:      'Ground',
    [t('sidebar.aviation')]:    'Aviation',
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

  return { anchor, mainSet, gems }
}

function calculate() {
  const r = getFarmSet(store.filteredVehicles, targetBr.value, nation.value, vehicleType.value)
  result.value   = r
  noAnchor.value = !r
}

function toRows(list) {
  return list.map(v => ({
    ...normRow(v),
    Name_Display: vehicleDisplayName(v),
  }))
}
const mainSetRows = computed(() => toRows(result.value?.mainSet ?? []))
const gemRows     = computed(() => toRows(result.value?.gems    ?? []))

const farmHeaders = computed(() => [
  { title: t('farm_tab.role'),        key: 'Роль',         width: 120 },
  { title: t('farm_tab.col_vehicle'), key: 'Name_Display', width: 180 },
  { title: t('common.nation'),        key: 'Nation',       width: 90  },
  { title: t('common.br'),            key: 'BR',           width: 60  },
  { title: t('common.battles'),       key: 'battles',      width: 80  },
  { title: t('common.wr'),            key: 'WR',           width: 65  },
  { title: t('common.kd'),            key: 'KD',           width: 60  },
  { title: t('farm_tab.col_farm'),    key: 'FARM_SCORE',   width: 70  },
  { title: t('farm_tab.col_net_sl'),  key: 'net_sl',       width: 110 },
])

const gemHeaders = computed(() => [
  { title: t('farm_tab.col_vehicle'), key: 'Name_Display', width: 180 },
  { title: t('common.nation'),        key: 'Nation',       width: 90  },
  { title: t('common.br'),            key: 'BR',           width: 60  },
  { title: t('common.battles'),       key: 'battles',      width: 80  },
  { title: t('farm_tab.col_farm'),    key: 'FARM_SCORE',   width: 70  },
])
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

.section-title { font-family: 'Rajdhani', sans-serif; font-size: 13px; font-weight: 700; color: #a7f3d0; letter-spacing: .08em; margin-bottom: 8px; margin-top: 4px; }
.cell-name { font-weight: 600; color: #e2e8f0; }
.text-muted-sm { font-size: 11px; color: #475569; font-style: italic; }
</style>

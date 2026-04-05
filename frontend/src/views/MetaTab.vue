<template>
  <div>
    <div class="controls-bar mb-3">
      <div class="controls-row">
        <v-select
          v-model="nation"
          :items="nationItems"
          item-title="title"
          item-value="value"
          :label="t('meta_tab.nation_label')"
          prepend-inner-icon="mdi-flag"
          density="compact"
          variant="outlined"
          hide-details
          style="max-width:220px"
        />
        <InfoTip align="right" class="ml-auto">
          <p><b>{{ filtered.length }}</b> {{ t('common.vehicle').toLowerCase() }} · BR {{ store.brRange[0].toFixed(1) }}–{{ store.brRange[1].toFixed(1) }} · {{ store.mode }}</p>
          <p>{{ t('meta_tab.tip_click') }}</p>
          <p style="margin-top:8px">
            {{ t('meta_tab.tip_colors') }}&nbsp;
            <span style="color:#34d399">■</span> ≥ 70 &nbsp;
            <span style="color:#fbbf24">■</span> 45–70 &nbsp;
            <span style="color:#f87171">■</span> &lt; 45
          </p>
        </InfoTip>
      </div>
    </div>

    <div class="table-wrap">
      <v-data-table
        :headers="headers"
        :items="tableRows"
        :items-per-page="100"
        density="compact"
        fixed-header
        height="calc(100vh - 230px)"
        :sort-by="[{ key: 'META_SCORE', order: 'desc' }]"
        class="wt-table"
        @click:row="(_, { item }) => openVehicle(item)"
      >
        <template #item.Name_Display="{ item }">
          <span class="cell-name">{{ item.Name_Display }}</span>
        </template>
        <template #item.META_SCORE="{ item }">
          <span class="cell-score" :style="{ color: metaColor(item.META_SCORE) }">{{ item.META_SCORE?.toFixed(1) }}</span>
        </template>
        <template #item.FARM_SCORE="{ item }">
          <span class="cell-score" :style="{ color: farmColor(item.FARM_SCORE) }">{{ item.FARM_SCORE?.toFixed(1) }}</span>
        </template>
        <template #item.WR="{ item }">
          <span :style="{ color: wrColor(item.WR) }">{{ item.WR?.toFixed(1) }}</span>
        </template>
        <template #item.net_sl="{ item }">
          <span style="color:#34d399;">{{ item.net_sl?.toLocaleString() }}</span>
        </template>
      </v-data-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTabFilters } from '../composables/useTabFilters.js'
import { useDataStore } from '../stores/useDataStore.js'
import {
  vehicleDisplayName, fmtType, fmtNation,
  metaColor, farmColor, wrColor, normRow,
} from '../composables/useVehicleFormatting.js'
import InfoTip from '../components/InfoTip.vue'

const { t }       = useI18n()
const store = useDataStore()
useTabFilters()
const openVehicle = inject('openVehicle')

const nation = ref('All')

const nationItems = computed(() =>
  (store.nations ?? []).map(n => ({
    title: n === 'All' ? t('common.all') : fmtNation(n),
    value: n,
  }))
)

const filtered = computed(() => {
  let rows = store.filteredVehicles
  if (nation.value !== 'All') rows = rows.filter(v => v.Nation === nation.value)
  return rows
})

const tableRows = computed(() =>
  filtered.value.map(v => ({
    ...normRow(v),
    Name_Display:   vehicleDisplayName(v),
    Type_Display:   fmtType(v.Type),
    Nation_Display: fmtNation(v.Nation),
  }))
)

const headers = computed(() => [
  { title: t('common.vehicle'), key: 'Name_Display',   sortable: true, width: 190 },
  { title: t('common.nation'),  key: 'Nation_Display', sortable: true, width: 110 },
  { title: t('common.br'),      key: 'BR',             sortable: true, width: 60  },
  { title: t('common.type'),    key: 'Type_Display',   sortable: true, width: 130 },
  { title: t('common.battles'), key: 'battles',        sortable: true, width: 80  },
  { title: t('common.wr'),      key: 'WR',             sortable: true, width: 65  },
  { title: t('common.kd'),      key: 'KD',             sortable: true, width: 60  },
  { title: t('common.meta'),    key: 'META_SCORE',     sortable: true, width: 75  },
  { title: t('common.farm'),    key: 'FARM_SCORE',     sortable: true, width: 75  },
  { title: t('common.net_sl'),  key: 'net_sl',         sortable: true, width: 110 },
])
</script>

<style scoped>
.controls-bar {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid #1e3a5f;
  border-radius: 10px;
  padding: 10px 14px;
}
.ml-auto { margin-left: auto; }
.controls-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.table-wrap {
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  overflow: hidden;
}
.cell-name  { font-weight: 600; color: #e2e8f0; }
.cell-score { font-weight: 700; font-family: 'JetBrains Mono', monospace; }
</style>
<style>
.wt-table .v-data-table__thead th {
  background: #1e293b !important; color: #a7f3d0 !important;
  font-family: 'Rajdhani', sans-serif !important; font-weight: 600 !important;
  font-size: 11px !important; letter-spacing: .1em !important; text-transform: uppercase !important;
  border-bottom: 1px solid #1e3a5f !important;
}
.wt-table .v-data-table__tbody td {
  background: #0f172a !important; color: #e2e8f0 !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 12px !important; border-bottom: 1px solid #1e293b !important; cursor: pointer;
}
.wt-table .v-data-table__tbody tr:hover td { background: #1e293b !important; }
</style>

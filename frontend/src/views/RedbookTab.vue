<template>
  <div>
    <v-alert type="info" variant="tonal" density="compact" class="mb-3" style="font-size:12px;">
      <b>{{ t('redbook_tab.title') }}</b> — {{ t('redbook_tab.description') }}
    </v-alert>

    <div class="controls-bar mb-3">
      <div class="controls-row">
        <v-select
          v-model="nation"
          :items="nationItems"
          item-title="title"
          item-value="value"
          :label="t('redbook_tab.nation_label')"
          prepend-inner-icon="mdi-flag"
          density="compact"
          variant="outlined"
          hide-details
          style="max-width:220px"
        />
        <v-select
          v-model="limit"
          :items="[25,50,100,200]"
          :label="t('redbook_tab.show_top')"
          density="compact"
          variant="outlined"
          hide-details
          style="max-width:160px"
        />
      </div>
    </div>

    <v-data-table
      :headers="headers"
      :items="tableRows"
      :items-per-page="100"
      density="compact"
      fixed-header
      height="calc(100vh - 280px)"
      :sort-by="[{ key: 'battles', order: 'asc' }]"
      class="wt-table"
      @click:row="(_, { item }) => openVehicle(item)"
    >
      <template #item.Name_Display="{ item }">
        <span class="cell-name">{{ item.Name_Display }}</span>
      </template>
      <template #item.battles="{ item }">
        <span :style="{ color: item.battles < 100 ? '#f87171' : '#e2e8f0' }">
          {{ item.battles?.toLocaleString() }}
        </span>
      </template>
      <template #item.WR="{ item }">
        <span :style="{ color: wrColor(item.WR) }">{{ item.WR?.toFixed(1) }}</span>
      </template>
    </v-data-table>
  </div>
</template>

<script setup>
import { ref, computed, inject } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDataStore } from '../stores/useDataStore.js'
import { vehicleDisplayName, fmtType, fmtNation, wrColor, normRow } from '../composables/useVehicleFormatting.js'

const { t }       = useI18n()
const store       = useDataStore()
const openVehicle = inject('openVehicle')

const nation = ref('All')
const limit  = ref(100)

const nationItems = computed(() =>
  (store.nations ?? []).map(n => ({
    title: n === 'All' ? t('common.all') : fmtNation(n),
    value: n,
  }))
)

const tableRows = computed(() => {
  let rows = store.filteredVehicles
  if (nation.value !== 'All') rows = rows.filter(v => v.Nation === nation.value)
  return rows
    .filter(v => (v['Сыграно игр'] ?? 0) > 0)
    .sort((a, b) => (a['Сыграно игр'] ?? 0) - (b['Сыграно игр'] ?? 0))
    .slice(0, limit.value)
    .map(v => ({
      ...normRow(v),
      Name_Display:   vehicleDisplayName(v),
      Type_Display:   fmtType(v.Type),
      Nation_Display: fmtNation(v.Nation),
    }))
})

const headers = computed(() => [
  { title: t('common.vehicle'), key: 'Name_Display',   sortable: true, width: 190 },
  { title: t('common.nation'),  key: 'Nation_Display', sortable: true, width: 110 },
  { title: t('common.br'),      key: 'BR',             sortable: true, width: 60  },
  { title: t('common.type'),    key: 'Type_Display',   sortable: true, width: 130 },
  { title: t('common.battles'), key: 'battles',        sortable: true, width: 90  },
  { title: t('common.wr'),      key: 'WR',             sortable: true, width: 65  },
  { title: t('common.kd'),      key: 'KD',             sortable: true, width: 60  },
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

.cell-name { font-weight: 600; color: #e2e8f0; }
</style>

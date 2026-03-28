<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="700" scrollable>
    <v-card v-if="vehicle" color="#0f172a" style="border: 1px solid #1e3a5f;">

      <v-card-title class="card-header">
        <span class="vehicle-name">{{ displayName }}</span>
        <v-spacer />
        <v-chip v-if="vehicle.VehicleClass !== 'Standard'" :color="classColor" size="x-small" class="mr-2">
          {{ t(`vehicle_classes.${vehicle.VehicleClass}`) }}
        </v-chip>
        <span class="br-badge">BR {{ fmtBR(vehicle.BR) }}</span>
        <v-btn icon="mdi-close" variant="text" size="small" :title="t('common.close')" @click="$emit('update:modelValue', false)" />
      </v-card-title>

      <v-divider color="#1e293b" />

      <v-card-text class="pa-0">
        <div class="card-grid">

          <!-- Статистика -->
          <div class="card-section">
            <div class="section-title">{{ t('vehicle_card.stats') }}</div>
            <div class="stat-row"><span class="stat-label">{{ t('vehicle_card.nation')  }}</span><span class="stat-value">{{ fmtNation(vehicle.Nation) }}</span></div>
            <div class="stat-row"><span class="stat-label">{{ t('vehicle_card.type')    }}</span><span class="stat-value">{{ fmtType(vehicle.Type) }}</span></div>
            <div class="stat-row"><span class="stat-label">{{ t('vehicle_card.battles') }}</span><span class="stat-value">{{ (vehicle['Сыграно игр'] ?? 0).toLocaleString() }}</span></div>
            <div class="stat-row"><span class="stat-label">{{ t('vehicle_card.wr')      }}</span><span class="stat-value" :style="{ color: wrColor(vehicle.WR) }">{{ vehicle.WR?.toFixed(1) }}%</span></div>
            <div class="stat-row"><span class="stat-label">{{ t('vehicle_card.kd')      }}</span><span class="stat-value">{{ vehicle.KD?.toFixed(2) }}</span></div>
          </div>

          <!-- Скоры -->
          <div class="card-section">
            <div class="section-title">{{ t('vehicle_card.scores') }}</div>
            <div class="score-row">
              <span class="score-label">{{ t('vehicle_card.meta_score') }}</span>
              <div class="score-bar-wrap">
                <div class="score-bar" :style="{ width: vehicle.META_SCORE + '%', background: metaColor(vehicle.META_SCORE) }" />
                <span class="score-val" :style="{ color: metaColor(vehicle.META_SCORE) }">{{ vehicle.META_SCORE?.toFixed(1) }}</span>
              </div>
            </div>
            <div class="score-row">
              <span class="score-label">{{ t('vehicle_card.farm_score') }}</span>
              <div class="score-bar-wrap">
                <div class="score-bar" :style="{ width: vehicle.FARM_SCORE + '%', background: farmColor(vehicle.FARM_SCORE) }" />
                <span class="score-val" :style="{ color: farmColor(vehicle.FARM_SCORE) }">{{ vehicle.FARM_SCORE?.toFixed(1) }}</span>
              </div>
            </div>
            <div class="stat-row mt-2">
              <span class="stat-label">{{ t('vehicle_card.net_sl') }}</span>
              <span class="stat-value" style="color: #34d399;">{{ fmtSL(vehicle['Net SL за игру']) }}</span>
            </div>
          </div>

          <!-- Броня -->
          <template v-if="hasVdb">
            <div class="card-section">
              <div class="section-title">{{ t('vehicle_card.armor') }}</div>
              <table class="armor-table">
                <thead>
                  <tr>
                    <th></th>
                    <th>{{ t('vehicle_card.armor_front') }}</th>
                    <th>{{ t('vehicle_card.armor_side')  }}</th>
                    <th>{{ t('vehicle_card.armor_rear')  }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td class="armor-label">{{ t('vehicle_card.armor_hull')   }}</td>
                    <td>{{ v('vdb_hull_front')  }}</td><td>{{ v('vdb_hull_side')  }}</td><td>{{ v('vdb_hull_rear')  }}</td>
                  </tr>
                  <tr>
                    <td class="armor-label">{{ t('vehicle_card.armor_turret') }}</td>
                    <td>{{ v('vdb_turret_front') }}</td><td>{{ v('vdb_turret_side') }}</td><td>{{ v('vdb_turret_rear') }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Подвижность -->
            <div class="card-section">
              <div class="section-title">{{ t('vehicle_card.mobility') }}</div>
              <div class="stat-row">
                <span class="stat-label">{{ t('vehicle_card.speed_rb')   }}</span>
                <span class="stat-value">{{ v('vdb_engine_max_speed_rb') }} {{ t('vehicle_card.speed_unit') }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">{{ t('vehicle_card.reverse_rb') }}</span>
                <span class="stat-value">{{ v('vdb_engine_reverse_rb') }} {{ t('vehicle_card.speed_unit') }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">{{ t('vehicle_card.hp_rb')      }}</span>
                <span class="stat-value">{{ v('vdb_engine_hp_rb') }} {{ t('vehicle_card.hp_unit') }}</span>
              </div>
            </div>

            <!-- Вооружение -->
            <div class="card-section">
              <div class="section-title">{{ t('vehicle_card.weapons') }}</div>
              <div class="stat-row">
                <span class="stat-label">{{ t('vehicle_card.caliber')      }}</span>
                <span class="stat-value">{{ v('vdb_main_caliber_mm') > 0 ? v('vdb_main_caliber_mm') + ' ' + t('vehicle_card.caliber_unit') : t('vehicle_card.no_vdb') }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">{{ t('vehicle_card.shell_speed')  }}</span>
                <span class="stat-value">{{ v('vdb_main_gun_speed') > 0 ? v('vdb_main_gun_speed') + ' ' + t('vehicle_card.speed_unit_ms') : t('vehicle_card.no_vdb') }}</span>
              </div>
              <div class="chips-row">
                <v-chip v-if="vehicle.vdb_has_thermal" color="info"      size="x-small">{{ t('vehicle_card.thermal') }}</v-chip>
                <v-chip v-if="vehicle.vdb_has_atgm"    color="error"     size="x-small">{{ t('vehicle_card.atgm')    }}</v-chip>
                <v-chip v-if="vehicle.vdb_has_heat"    color="warning"   size="x-small">{{ t('vehicle_card.heat')    }}</v-chip>
                <v-chip v-if="vehicle.vdb_has_aphe"    color="secondary" size="x-small">{{ t('vehicle_card.aphe')    }}</v-chip>
              </div>
            </div>

            <!-- Экономика -->
            <div class="card-section">
              <div class="section-title">{{ t('vehicle_card.economy') }}</div>
              <div class="stat-row">
                <span class="stat-label">{{ t('vehicle_card.repair_rb') }}</span>
                <span class="stat-value">{{ fmtSL(vehicle.vdb_repair_cost_realistic) }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">{{ t('vehicle_card.sl_per_game') }}</span>
                <span class="stat-value" style="color: #34d399;">{{ fmtSL(vehicle['SL за игру']) }}</span>
              </div>
              <div v-if="vehicle.vdb_era" class="stat-row">
                <span class="stat-label">{{ t('vehicle_card.era') }}</span>
                <span class="stat-value">{{ vehicle.vdb_era }}</span>
              </div>
            </div>
          </template>

        </div>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n }  from 'vue-i18n'
import {
  vehicleDisplayName, fmtType, fmtNation, fmtBR, fmtSL,
  metaColor, farmColor, wrColor,
} from '../composables/useVehicleFormatting.js'

const { t } = useI18n()

const props = defineProps({ modelValue: Boolean, vehicle: Object })
defineEmits(['update:modelValue'])

const veh      = computed(() => props.vehicle ?? {})
const hasVdb   = computed(() => (veh.value?.vdb_match_score ?? 0) > 0)
const displayName = computed(() => vehicleDisplayName(veh.value))

function v(key) {
  const val = veh.value?.[key]
  return val ?? t('vehicle_card.no_vdb')
}

const classColor = computed(() => {
  const map = { Premium: 'warning', Pack: 'success', Squadron: 'info',
                Marketplace: 'secondary', Gift: 'pink', Event: 'error' }
  return map[veh.value?.VehicleClass] ?? 'default'
})
</script>

<style scoped>
.card-header { display: flex; align-items: center; padding: 12px 16px; font-family: 'Rajdhani', sans-serif; gap: 8px; }
.vehicle-name { font-size: 18px; font-weight: 700; color: #a7f3d0; letter-spacing: .06em; }
.br-badge { font-family: 'JetBrains Mono', monospace; font-size: 14px; color: #94a3b8; white-space: nowrap; }
.card-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0; }
.card-section { padding: 14px 16px; border-right: 1px solid #1e293b; border-bottom: 1px solid #1e293b; }
.card-section:nth-child(even) { border-right: none; }
.section-title { font-family: 'Rajdhani', sans-serif; font-size: 10px; font-weight: 700; letter-spacing: .12em; color: #475569; text-transform: uppercase; margin-bottom: 10px; }
.stat-row { display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 12px; }
.stat-label { color: #64748b; }
.stat-value { color: #e2e8f0; font-weight: 600; }
.score-row { margin-bottom: 8px; }
.score-label { font-size: 10px; color: #64748b; display: block; margin-bottom: 3px; letter-spacing: .06em; }
.score-bar-wrap { display: flex; align-items: center; gap: 8px; background: #1e293b; border-radius: 4px; height: 18px; padding: 0 8px; }
.score-bar { height: 4px; border-radius: 2px; transition: width .3s; flex-shrink: 0; }
.score-val { font-size: 11px; font-weight: 700; font-family: 'JetBrains Mono', monospace; margin-left: auto; }
.armor-table { width: 100%; font-size: 11px; border-collapse: collapse; font-family: 'JetBrains Mono', monospace; }
.armor-table th { color: #475569; font-weight: 600; text-align: center; padding: 3px 6px; border-bottom: 1px solid #1e293b; }
.armor-table td { text-align: center; color: #e2e8f0; padding: 4px 6px; }
.armor-label { color: #64748b !important; text-align: left !important; }
.chips-row { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; }
</style>

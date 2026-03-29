<template>
  <div
    class="prog-card"
    :class="{ 'prog-card--grouped': grouped }"
    :style="cardStyle"
    @click="$emit('click')"
  >
    <!-- Header: icon · name · BR · verdict emoji -->
    <div class="pc-header">
      <span class="pc-type-icon" :title="vehicle._branch">{{ typeIcon }}</span>
      <span class="pc-name" :style="{ color: nameColor }">{{ displayName }}</span>
      <span class="pc-br"   :style="{ color: brColor   }">{{ brStr }}</span>
      <span class="pc-verdict">{{ vc.icon }}</span>
    </div>

    <!-- Stats row: WR · K/D · META -->
    <div class="pc-stats">
      <span class="pc-stat"><span class="pc-stat-label">WR</span>{{ wrStr }}%</span>
      <span class="pc-stat"><span class="pc-stat-label">K/D</span>{{ kdStr }}</span>
      <span class="pc-stat"><span class="pc-stat-label">META</span>{{ metaStr }}</span>
    </div>

    <!-- Hints (conditional, at most one per card) -->
    <div v-if="vehicle.Cross_Hint" class="pc-hint pc-hint--cross">
      {{ vehicle.Cross_Hint }}
    </div>

    <div
      v-if="vehicle.Verdict === 'SKIP' && vehicle.Skip_Reason"
      class="pc-hint pc-hint--skip"
    >
      {{ vehicle.Skip_Reason }}
    </div>

    <template v-if="vehicle.Verdict === 'PREM'">
      <div v-if="vehicle.Prem_Pain_Fix" class="pc-hint pc-hint--prem">
        👑 Helps bypass painful rank
      </div>
      <div
        v-if="boostLabel"
        class="pc-hint pc-hint--boost"
        :style="{ color: boostLabel.color }"
      >
        {{ boostLabel.text }}
      </div>
      <div v-if="!vehicle.Prem_Pain_Fix && !boostLabel" class="pc-hint pc-hint--prem">
        ★ Premium
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  VERDICT_COLORS,
  TYPE_ICON,
  CLASS_PREFIX,
  CLASS_BR_COLOR,
} from '../composables/constants.js'

// Props / Emits
const props = defineProps({
  vehicle: { type: Object,  required: true },
  grouped: { type: Boolean, default: false },
})
defineEmits(['click'])

// Verdict visual
const vc = computed(() => VERDICT_COLORS[props.vehicle.Verdict] ?? VERDICT_COLORS.PASS)

// Display strings
const displayName = computed(
  () => (CLASS_PREFIX[props.vehicle.VehicleClass] || '') + (props.vehicle.Name ?? '')
)
const brStr   = computed(() => parseFloat(props.vehicle.BR           || 0).toFixed(1))
const wrStr   = computed(() => parseFloat(props.vehicle.WR           || 0).toFixed(1))
const kdStr   = computed(() => parseFloat(props.vehicle.KD           || 0).toFixed(1))
const metaStr = computed(() => parseFloat(props.vehicle._localScore  || 0).toFixed(0))

// Colors
const typeIcon  = computed(() => TYPE_ICON[props.vehicle._branch] || '🔧')
const brColor   = computed(() => CLASS_BR_COLOR[props.vehicle.VehicleClass] || '#64748b')
const nameColor = computed(() => brColor.value === '#64748b' ? '#e2e8f0' : brColor.value)

// Premium boost label
const boostLabel = computed(() => {
  const b = props.vehicle.Prem_Boost
  if (!b || b < 0.01) return null
  if (b >= 1.05) return { text: `⚡ Grind ×${b.toFixed(1)} vs free`, color: '#34d399' }
  if (b >= 0.95) return { text: `≈ Parity ×${b.toFixed(1)}`,          color: '#94a3b8' }
  return               { text: `↓ Weaker ×${b.toFixed(1)}`,            color: '#f87171' }
})

// Card border / background driven by verdict
const cardStyle = computed(() => ({
  borderLeft:      `4px solid ${vc.value.border}`,
  borderTop:       `1px solid ${vc.value.border}22`,
  borderRight:     `1px solid ${vc.value.border}22`,
  borderBottom:    `1px solid ${vc.value.border}22`,
  backgroundColor: vc.value.bg,
  '--glow':        vc.value.border,
}))
</script>

<style scoped>
/* Card shell */
.prog-card {
  position: relative;
  border-radius: 0 5px 5px 0;
  padding: 7px 10px;
  margin-bottom: 4px;
  box-sizing: border-box;
  cursor: pointer;
  min-width: 0;
  transition: box-shadow 0.15s, transform 0.12s, filter 0.12s;
}
.prog-card:hover {
  transform: translateY(-1px) translateX(1px);
  box-shadow: 3px 4px 16px var(--glow, #1e3a5f66);
  filter: brightness(1.08);
}
/* When inside a .group-bracket: collapse bottom margin so cards touch */
.prog-card--grouped {
  margin-bottom: 0;
}

/* Header row */
.pc-header {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 4px;
}
.pc-type-icon {
  font-size: 12px;
  flex-shrink: 0;
  opacity: 0.75;
}
.pc-name {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 600;
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.pc-br {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
}
.pc-verdict {
  font-size: 11px;
  flex-shrink: 0;
}

/* Stats */
.pc-stats {
  display: flex;
  gap: 8px;
}
.pc-stat {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: #94a3b8;
}
.pc-stat-label {
  font-size: 10px;
  color: #475569;
  margin-right: 2px;
}

/* Hints */
.pc-hint {
  font-size: 10px;
  margin-top: 5px;
  padding-top: 5px;
  line-height: 1.4;
}
.pc-hint--cross {
  color: #7dd3fc;
  border-top: 1px solid rgba(125, 211, 252, 0.20);
}
.pc-hint--skip {
  color: #fecaca;
  border-top: 1px solid rgba(248, 113, 113, 0.25);
}
.pc-hint--prem {
  color: #c4b5fd;
  border-top: 1px solid rgba(167, 139, 250, 0.25);
}
.pc-hint--boost {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  border-top: 1px solid rgba(167, 139, 250, 0.15);
  padding-top: 3px;
  margin-top: 3px;
}
</style>

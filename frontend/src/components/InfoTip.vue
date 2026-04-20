<template>
  <div
    class="infotip"
    @mouseenter="onEnter"
    @mouseleave="onLeave"
  >
    <span class="infotip-trigger" :class="{ 'infotip-trigger--active': visible }">!</span>
    <div
      class="infotip-box"
      :class="[`infotip-box--${align}`, { 'infotip-box--visible': visible }]"
      @mouseenter="onEnter"
      @mouseleave="onLeave"
    >
      <slot />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  align: { type: String, default: 'right' }, // 'right' | 'left' | 'center'
})

const visible  = ref(false)
let closeTimer = null

function onEnter() {
  clearTimeout(closeTimer)
  visible.value = true
}

function onLeave() {
  closeTimer = setTimeout(() => {
    visible.value = false
  }, 300)
}
</script>

<style scoped>
.infotip {
  position: relative;
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
}

.infotip-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 1px solid #1e3a5f;
  background: rgba(15, 23, 42, 0.7);
  color: #475569;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 700;
  cursor: default;
  user-select: none;
  transition: border-color 0.15s, color 0.15s, background 0.15s;
  flex-shrink: 0;
}

.infotip-trigger--active {
  border-color: #38bdf8;
  color: #38bdf8;
  background: rgba(56, 189, 248, 0.08);
}

.infotip-box {
  position: absolute;
  top: calc(100% + 8px);
  z-index: 200;
  width: 280px;
  padding: 10px 13px;
  background: #0d1b2e;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.7);
  color: #94a3b8;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  line-height: 1.6;
  pointer-events: none;
  opacity: 0;
  transform: translateY(-4px);
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.infotip-box--visible {
  pointer-events: auto;
  opacity: 1;
  transform: translateY(0);
}

.infotip-box::before {
  content: '';
  position: absolute;
  top: -5px;
  width: 8px;
  height: 8px;
  background: #0d1b2e;
  border-left: 1px solid #1e3a5f;
  border-top: 1px solid #1e3a5f;
  transform: rotate(45deg);
}

.infotip-box--right         { right: 0; }
.infotip-box--right::before { right: 5px; }

.infotip-box--left          { left: 0; }
.infotip-box--left::before  { left: 5px; }

.infotip-box--center                { left: 50%; transform: translateX(-50%) translateY(-4px); }
.infotip-box--center.infotip-box--visible { transform: translateX(-50%) translateY(0); }
.infotip-box--center::before        { left: 50%; transform: translateX(-50%) rotate(45deg); }

.infotip-box :deep(b)  { color: #e2e8f0; font-weight: 700; }
.infotip-box :deep(p)  { margin: 4px 0 0; }
.infotip-box :deep(p:first-child) { margin-top: 0; }
.infotip-box :deep(.tip-row) {
  display: flex;
  gap: 6px;
  align-items: baseline;
  margin-top: 5px;
}
.infotip-box :deep(.tip-icon)  { flex-shrink: 0; }
.infotip-box :deep(.tip-label) { color: #e2e8f0; font-weight: 600; }
</style>

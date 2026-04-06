<template>
  <v-app-bar
    elevation="0"
    height="48"
    style="background: #0a1628; border-bottom: 1px solid #1e3a5f; z-index: 1000;"
  >
    <v-app-bar-title>
      <div class="logo-group">
        <span class="logo-title">{{ t('topbar.title') }}</span>
        <a
          href="https://github.com/Ultra119/wt_meta_center/issues"
          target="_blank"
          rel="noopener noreferrer"
          class="report-link"
          :title="t('topbar.report_title')"
        >
          <span class="mdi mdi-bug-outline" />
          <span class="report-text">{{ t('topbar.report') }}</span>
        </a>
      </div>
    </v-app-bar-title>

    <v-spacer />

    <div class="search-wrapper" ref="wrapperRef">

      <div class="search-field" :class="{ 'search-field--active': isOpen }">
        <span class="mdi mdi-magnify search-icon" />
        <input
          ref="inputRef"
          v-model="query"
          class="search-input"
          :placeholder="t('topbar.search_hint')"
          autocomplete="off"
          spellcheck="false"
          @input="onInput"
          @focus="onFocus"
          @keydown.escape="closeSearch"
          @keydown.down.prevent="moveDown"
          @keydown.up.prevent="moveUp"
          @keydown.enter.prevent="selectActive"
        />
        <button v-if="query" class="search-clear" tabindex="-1" @mousedown.prevent="clearQuery">
          <span class="mdi mdi-close" />
        </button>
      </div>

      <Teleport to="body">
        <Transition name="dropdown">
          <div
            v-if="isOpen"
            class="search-dropdown"
            :style="dropdownStyle"
          >
            <div class="search-header">
              {{ t('topbar.search_header') }}
              <span v-if="hits.length" class="search-count">{{ hits.length }}</span>
            </div>

            <div v-if="hits.length" class="search-list">
              <div
                v-for="(v, i) in hits"
                :key="v.Name + v.Nation"
                class="search-item"
                :class="{ 'search-item--active': i === activeIdx }"
                @mousedown.prevent="pick(v)"
                @mousemove="activeIdx = i"
              >
                <div class="item-left">
                  <v-icon class="item-type-icon" size="13">{{ typeIcon(v.Type) }}</v-icon>
                  <span class="item-name">{{ vehicleDisplayName(v) }}</span>
                </div>
                <div class="item-right">
                  <span class="item-flag" :title="v.Nation">{{ nationFlag(v.Nation) }}</span>
                  <span class="item-br">{{ fmtBR(v.BR) }}</span>
                </div>
              </div>
            </div>

            <div v-else class="search-empty">
              <span class="mdi mdi-magnify-remove-outline" style="font-size:20px; opacity:0.3" />
              {{ t('topbar.search_empty') }}
            </div>
          </div>
        </Transition>
      </Teleport>
    </div>

    <div class="lang-switcher ml-3">
      <v-btn
        v-for="loc in SUPPORTED_LOCALES"
        :key="loc.code"
        :variant="locale === loc.code ? 'tonal' : 'text'"
        size="x-small"
        class="lang-btn"
        @click="setLocale(loc.code)"
      >
        {{ loc.flag }} {{ loc.label }}
      </v-btn>
    </div>

    <div class="px-2" />
  </v-app-bar>
</template>

<script setup>
import { ref, computed, inject, onMounted, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDataStore } from '../stores/useDataStore.js'
import { setLocale, SUPPORTED_LOCALES } from '../i18n/index.js'
import { vehicleDisplayName, fmtBR, NATION_FLAG } from '../composables/useVehicleFormatting.js'
import { TYPE_ICON } from '../composables/constants.js'

const { t, locale } = useI18n()
const store       = useDataStore()
const openVehicle = inject('openVehicle')

const query      = ref('')
const isOpen     = ref(false)
const activeIdx  = ref(-1)
const inputRef   = ref(null)
const wrapperRef = ref(null)

const dropdownStyle = ref({})

function updateDropdownPos() {
  if (!wrapperRef.value) return
  const rect = wrapperRef.value.getBoundingClientRect()
  dropdownStyle.value = {
    position: 'fixed',
    top:      rect.bottom + 6 + 'px',
    right:    window.innerWidth - rect.right + 'px',
    width:    '380px',
    zIndex:   9999,
  }
}

function onDocClick(e) {
  if (!wrapperRef.value?.contains(e.target)) closeSearch()
}

onMounted(()   => document.addEventListener('mousedown', onDocClick))
onBeforeUnmount(() => document.removeEventListener('mousedown', onDocClick))

const MAX_HITS = 12

const hits = computed(() => {
  const q = query.value.trim()
  if (q.length < 2) return []
  const lower  = q.toLowerCase()
  const seen   = new Set()
  const result = []
  for (const v of (store.allVehicles ?? [])) {
    if (!v.Name?.toLowerCase().includes(lower)) continue
    const key = `${v.Name}||${v.Nation}`
    if (seen.has(key)) continue
    seen.add(key)
    result.push(v)
    if (result.length >= MAX_HITS) break
  }
  return result
})

function typeIcon(type)   { return TYPE_ICON[type] ?? 'mdi-car' }
function nationFlag(nation) { return NATION_FLAG[nation?.toLowerCase()] ?? '🏴' }

function onInput() {
  activeIdx.value = -1
  const show = query.value.trim().length >= 2
  if (show) updateDropdownPos()
  isOpen.value = show
}

function onFocus() {
  if (query.value.trim().length >= 2) {
    updateDropdownPos()
    isOpen.value = true
  }
}

function closeSearch() {
  isOpen.value    = false
  activeIdx.value = -1
}

function clearQuery() {
  query.value     = ''
  isOpen.value    = false
  activeIdx.value = -1
  inputRef.value?.focus()
}

function pick(v) {
  openVehicle?.(v)
  closeSearch()
  query.value = ''
}

function moveDown() {
  if (!hits.value.length) return
  activeIdx.value = (activeIdx.value + 1) % hits.value.length
}

function moveUp() {
  if (!hits.value.length) return
  activeIdx.value = activeIdx.value <= 0 ? hits.value.length - 1 : activeIdx.value - 1
}

function selectActive() {
  const v = hits.value[activeIdx.value]
  if (v) pick(v)
}
</script>

<style scoped>
.logo-group {
  display: inline-flex;
  align-items: baseline;
  gap: 10px;
}

.logo-title {
  font-family: 'Rajdhani', sans-serif;
  font-size: 18px;
  font-weight: 700;
  color: #a7f3d0;
  letter-spacing: 0.08em;
}

.report-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #334155;
  text-decoration: none;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.05em;
  white-space: nowrap;
  flex-shrink: 0;
  transition: color 0.15s;
}
.report-link:hover { color: #64748b; }
.report-link .mdi  { font-size: 13px; }
.report-text       { line-height: 1; }

.search-wrapper { position: relative; }

.search-field {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 380px;
  height: 36px;
  padding: 0 10px;
  background: #0f1e35;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.search-field--active,
.search-field:focus-within {
  border-color: #38bdf8;
  box-shadow: 0 0 0 2px rgba(56,189,248,0.12);
}

.search-icon { font-size: 16px; color: #475569; flex-shrink: 0; }

.search-input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  color: #e2e8f0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  caret-color: #38bdf8;
  min-width: 0;
}
.search-input::placeholder { color: #334155; }

.search-clear {
  background: none; border: none; padding: 0; cursor: pointer;
  color: #475569; display: flex; align-items: center;
  transition: color 0.12s; flex-shrink: 0;
}
.search-clear:hover { color: #94a3b8; }
.search-clear .mdi  { font-size: 15px; }

.lang-switcher { display: flex; gap: 2px; }
.lang-btn {
  font-family: 'Rajdhani', sans-serif !important;
  font-size: 11px !important;
  min-width: 44px !important;
}

.dropdown-enter-active { transition: opacity 0.12s ease, transform 0.12s ease; }
.dropdown-leave-active { transition: opacity 0.08s ease; }
.dropdown-enter-from   { opacity: 0; transform: translateY(-4px); }
.dropdown-leave-to     { opacity: 0; }
</style>

<style>
.search-dropdown {
  background: #0d1b2e;
  border: 1px solid #1e3a5f;
  border-radius: 10px;
  box-shadow: 0 12px 40px rgba(0,0,0,0.85);
  overflow: hidden;
}

.search-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 14px;
  background: #0a1628;
  border-bottom: 1px solid #1e3a5f;
  font-family: 'Rajdhani', sans-serif;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: #475569;
  text-transform: uppercase;
  user-select: none;
}

.search-count {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #334155;
  background: rgba(30,58,95,0.5);
  border-radius: 4px;
  padding: 1px 6px;
}

.search-list {
  max-height: 360px;
  overflow-y: auto;
}
.search-list::-webkit-scrollbar       { width: 4px; }
.search-list::-webkit-scrollbar-track { background: transparent; }
.search-list::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 2px; }

.search-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 14px;
  border-bottom: 1px solid rgba(30,58,95,0.5);
  cursor: pointer;
  gap: 12px;
  transition: background 0.08s;
}
.search-item:last-child { border-bottom: none; }
.search-item:hover,
.search-item--active { background: #1a2e4a; }

.item-left  { display: flex; align-items: center; gap: 7px; min-width: 0; }
.item-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }

.item-type-icon { font-size: 13px; flex-shrink: 0; line-height: 1; }

.item-name {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px; font-weight: 600; color: #e2e8f0;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

.item-flag  { font-size: 15px; line-height: 1; flex-shrink: 0; }

.item-br {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px; font-weight: 700; color: #38bdf8;
  background: rgba(56,189,248,0.08);
  border: 1px solid rgba(56,189,248,0.15);
  border-radius: 4px; padding: 1px 5px; white-space: nowrap;
}

.search-empty {
  display: flex; flex-direction: column; align-items: center;
  gap: 8px; padding: 28px 14px;
  color: #334155; font-size: 12px; font-style: italic;
}
</style>

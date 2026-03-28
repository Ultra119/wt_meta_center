<template>
  <v-app theme="wt">
    <v-overlay :model-value="store.loading" persistent class="align-center justify-center">
      <v-progress-circular indeterminate size="64" color="primary" />
      <div class="mt-4 text-caption text-medium-emphasis">{{ t('common.loading') }}</div>
    </v-overlay>

    <v-snackbar v-if="store.loadError" :model-value="true" color="error" timeout="-1" location="top">
      {{ t('common.error_load', { msg: store.loadError }) }}
    </v-snackbar>

    <TopBar />
    <SideBar />

    <v-main style="background: #020c1a; padding-left: 280px;">
      <v-tabs
        v-model="activeTab"
        bg-color="#0f172a"
        color="primary"
        density="compact"
        height="44"
        style="border-bottom: 1px solid #1e3a5f;"
      >
        <v-tab v-for="tab in tabs" :key="tab.to" :to="tab.to" :prepend-icon="tab.icon">
          {{ t(tab.labelKey) }}
        </v-tab>
      </v-tabs>

      <div class="pa-4">
        <router-view v-slot="{ Component }">
          <keep-alive>
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </div>
    </v-main>

    <VehicleCard v-model="modalOpen" :vehicle="selectedVehicle" />
  </v-app>
</template>

<script setup>
import { ref, provide, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDataStore } from './stores/useDataStore.js'
import TopBar      from './components/TopBar.vue'
import SideBar     from './components/SideBar.vue'
import VehicleCard from './components/VehicleCard.vue'

const { t } = useI18n()
const store  = useDataStore()

const activeTab = ref('/meta')

const tabs = [
  { to: '/meta',        icon: 'mdi-trophy',                  labelKey: 'tabs.meta'        },
  { to: '/redbook',     icon: 'mdi-book-open',                labelKey: 'tabs.redbook'     },
  { to: '/brackets',    icon: 'mdi-view-grid',                labelKey: 'tabs.brackets'    },
  { to: '/farm',        icon: 'mdi-wrench',                   labelKey: 'tabs.farm'        },
  { to: '/progression', icon: 'mdi-chart-timeline-variant',   labelKey: 'tabs.progression' },
]

const modalOpen       = ref(false)
const selectedVehicle = ref(null)

function openVehicle(v) {
  selectedVehicle.value = v
  modalOpen.value       = true
}

provide('openVehicle', openVehicle)

onMounted(() => {
  const base = import.meta.env.BASE_URL.replace(/\/$/, '')
  store.loadData(base)
})
</script>

<style>
:root {
  --font-mono: 'JetBrains Mono', monospace;
  --font-ui:   'Rajdhani', sans-serif;
}
.v-application { font-family: var(--font-mono) !important; }
.v-tab { font-family: var(--font-ui) !important; font-weight: 600; letter-spacing: 0.08em; }
::-webkit-scrollbar       { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0f172a; }
::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #a7f3d0; }
</style>

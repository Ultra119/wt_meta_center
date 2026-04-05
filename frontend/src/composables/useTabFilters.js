import { onMounted, onUnmounted, onActivated, onDeactivated } from 'vue'
import { useDataStore } from '../stores/useDataStore.js'


export function useTabFilters(config = {}) {
  const store = useDataStore()

  const resolved = {
    mode:       config.mode       ?? true,
    brRange:    config.brRange    ?? true,
    minBattles: config.minBattles ?? true,
    classes:    config.classes    ?? true,
    types:      config.types      ?? true,
  }

  const apply = () => store.setTabFilters(resolved)
  const reset = () => store.clearTabFilters()

  onMounted(apply)
  onUnmounted(reset)

  onActivated(apply)
  onDeactivated(reset)
}

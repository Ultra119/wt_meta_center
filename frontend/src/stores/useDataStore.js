import { defineStore } from 'pinia'
import { ref, shallowRef, computed, watch, watchEffect } from 'vue'

export const WT_BR_STEPS = [
  1.0,1.3,1.7, 2.0,2.3,2.7, 3.0,3.3,3.7, 4.0,4.3,4.7,
  5.0,5.3,5.7, 6.0,6.3,6.7, 7.0,7.3,7.7, 8.0,8.3,8.7,
  9.0,9.3,9.7, 10.0,10.3,10.7, 11.0,11.3,11.7, 12.0,12.3,12.7, 13.0,
]

const BR_MIN = Math.min(...WT_BR_STEPS)
const BR_MAX = Math.max(...WT_BR_STEPS)

const TYPE_CATEGORIES = {
  Ground:      ['medium_tank','light_tank','heavy_tank','tank_destroyer','spaa'],
  Aviation:    ['fighter','bomber','assault'],
  Helicopters: ['attack_helicopter','utility_helicopter'],
  LargeFleet:  ['destroyer','heavy_cruiser','light_cruiser','battleship','battlecruiser'],
  SmallFleet:  ['boat','heavy_boat','frigate','barge'],
}

function typeToCategory(t) {
  for (const [cat, types] of Object.entries(TYPE_CATEGORIES))
    if (types.includes(t)) return cat
  return null
}

function debounce(fn, delay) {
  let timer = null
  return (...args) => {
    if (timer !== null) clearTimeout(timer)
    timer = setTimeout(() => { timer = null; fn(...args) }, delay)
  }
}

export function formatPeriodLabel(p) {
  if (!p || p === 'All') return 'All Periods'
  const parts = p.split('-')
  if (parts.length !== 2) return p
  try {
    const d = new Date(parseInt(parts[1], 10), parseInt(parts[0], 10) - 1, 1)
    return d.toLocaleDateString(undefined, { month: 'short', year: 'numeric' })
  } catch {
    return p
  }
}

export const useDataStore = defineStore('data', () => {

  const allVehicles = ref([])
  const metaInfo    = ref(null)
  const loading     = ref(false)
  const loadError   = ref(null)

  const _basePath = ref('')

  const tabFilterConfig = ref(null)

  function setTabFilters(cfg) { tabFilterConfig.value = cfg  }
  function clearTabFilters()  { tabFilterConfig.value = null }

  const currentPeriod = ref('All')

  const periods = computed(() => metaInfo.value?.periods ?? ['All'])

  const mode       = ref('Realistic')
  const minBattles = ref(50)
  const brRange    = ref([BR_MIN, BR_MAX])
  const classes    = ref(['Standard','Premium','Pack','Squadron','Marketplace','Gift','Event'])

  const showGround      = ref(true)
  const showAviation    = ref(true)
  const showHelicopters = ref(false)
  const showLargeFleet  = ref(false)
  const showSmallFleet  = ref(false)

  const _mode            = ref('Realistic')
  const _minBattles      = ref(50)
  const _brRange         = ref([BR_MIN, BR_MAX])
  const _classes         = ref(['Standard','Premium','Pack','Squadron','Marketplace','Gift','Event'])
  const _showGround      = ref(true)
  const _showAviation    = ref(true)
  const _showHelicopters = ref(false)
  const _showLargeFleet  = ref(false)
  const _showSmallFleet  = ref(false)

  watch(mode,            v => { _mode.value           = v       })
  watch(classes,         v => { _classes.value         = [...v]  }, { deep: true })
  watch(showGround,      v => { _showGround.value      = v       })
  watch(showAviation,    v => { _showAviation.value    = v       })
  watch(showHelicopters, v => { _showHelicopters.value = v       })
  watch(showLargeFleet,  v => { _showLargeFleet.value  = v       })
  watch(showSmallFleet,  v => { _showSmallFleet.value  = v       })

  const commitRange   = debounce(v => { _brRange.value    = v }, 220)
  const commitBattles = debounce(v => { _minBattles.value = v }, 220)
  watch(brRange,    v => commitRange([...v]))
  watch(minBattles, v => commitBattles(v))

  async function _loadVehicles() {
    const hash = metaInfo.value?.dataset_hash ?? ''
    const qs   = hash ? `?v=${hash.slice(0, 8)}` : ''
    const url  = `${_basePath.value}/data/mega_db_${currentPeriod.value}.json${qs}`
    const res  = await fetch(url)
    if (!res.ok) throw new Error(`mega_db_${currentPeriod.value}.json: ${res.status}`)
    allVehicles.value = await res.json()
  }
  async function loadData(basePath = '') {
    _basePath.value  = basePath
    loading.value    = true
    loadError.value  = null
    try {
      const metaRes = await fetch(`${basePath}/meta_info.json`)
      if (!metaRes.ok) throw new Error(`meta_info.json: ${metaRes.status}`)
      metaInfo.value = await metaRes.json()

      const available = metaInfo.value?.periods ?? ['All']
      if (!available.includes(currentPeriod.value)) {
        currentPeriod.value = available[0] ?? 'All'
      }

      await _loadVehicles()
    } catch (e) {
      loadError.value = e.message
      console.error('[DataStore]', e)
    } finally {
      loading.value = false
    }
  }

  watch(currentPeriod, async () => {
    if (!metaInfo.value) return   // loadData() not yet called; ignore
    loading.value   = true
    loadError.value = null
    try {
      await _loadVehicles()
    } catch (e) {
      loadError.value = e.message
      console.error('[DataStore] period switch error:', e)
    } finally {
      loading.value = false
    }
  })

  const activeTypes = computed(() => {
    const wanted = new Set()
    if (_showGround.value)      wanted.add('Ground')
    if (_showAviation.value)    wanted.add('Aviation')
    if (_showHelicopters.value) wanted.add('Helicopters')
    if (_showLargeFleet.value)  wanted.add('LargeFleet')
    if (_showSmallFleet.value)  wanted.add('SmallFleet')
    if (wanted.size === 0) return []

    const all = metaInfo.value?.types ?? []
    return all.filter(t => {
      const cat = typeToCategory(t)
      return cat ? wanted.has(cat) : true
    })
  })

  const filteredVehicles = shallowRef([])
  const filtering = ref(false)

  let _filterVersion = 0

  watchEffect(() => {
    const vehicles = allVehicles.value
    const mode     = _mode.value
    const brMin    = _brRange.value[0]
    const brMax    = _brRange.value[1]
    const minB     = _minBattles.value
    const cls      = _classes.value
    const types    = activeTypes.value

    const version = ++_filterVersion

    filtering.value = true

    setTimeout(() => {
      if (version !== _filterVersion) return
      filteredVehicles.value = !vehicles.length ? [] : vehicles.filter(v =>
        v.Mode === mode &&
        v.BR   >= brMin &&
        v.BR   <= brMax &&
        (v['Сыграно игр'] ?? 0) >= minB &&
        cls.includes(v.VehicleClass ?? 'Standard') &&
        types.includes(v.Type)
      )
      filtering.value = false
    }, 0)
  })

  const nations = computed(() => {
    const raw = metaInfo.value?.nations ?? []
    return ['All', ...raw]
  })

  return {
    allVehicles, metaInfo, loading, loadError,
    currentPeriod, periods,
    mode, minBattles, brRange, classes,
    showGround, showAviation, showHelicopters, showLargeFleet, showSmallFleet,
    filteredVehicles, activeTypes, nations, filtering,
    loadData,
    tabFilterConfig, setTabFilters, clearTabFilters,
    BR_MIN, BR_MAX, WT_BR_STEPS,
  }
})

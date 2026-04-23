import { ref, watch } from 'vue'

const DATAMINE_OWNER = 'gszabi99'
const DATAMINE_REPO  = 'War-Thunder-Datamine'
const DATAMINE_REF   = 'refs/tags/2.55.1.80'
const DATAMINE_ROOT  = 'tex.vromfs.bin_u'

const CDN_BASE =
  `https://rawcdn.githack.com/${DATAMINE_OWNER}/${DATAMINE_REPO}/${DATAMINE_REF}/${DATAMINE_ROOT}`

const GROUND_TYPES = new Set([
  'medium_tank', 'light_tank', 'heavy_tank', 'tank_destroyer', 'spaa',
])
const AIR_TYPES = new Set([
  'fighter', 'bomber', 'assault',
  'attack_helicopter', 'utility_helicopter',
])
const SHIP_TYPES = new Set([
  'destroyer', 'heavy_cruiser', 'light_cruiser', 'battleship', 'battlecruiser',
  'boat', 'heavy_boat', 'frigate', 'barge',
])

function typeToFolder(vehicleType) {
  if (!vehicleType) return null
  const t = vehicleType.toLowerCase()
  if (GROUND_TYPES.has(t)) return 'tanks'
  if (AIR_TYPES.has(t))    return 'aircrafts'
  if (SHIP_TYPES.has(t))   return 'ships'
  return null
}


export function vehicleImageUrl(vehicleName, vehicleType) {
  if (!vehicleName || !vehicleType) return null
  const folder = typeToFolder(vehicleType)
  if (!folder) return null
  const name = vehicleName.trim()
  return `${CDN_BASE}/${folder}/${name}.png`
}

const _cache = new Map()

export function useVehicleImage(nameRef, typeRef) {
  const src    = ref(null)
  const loaded = ref(false)
  const error  = ref(false)

  function probe() {
    const name = nameRef.value
    const type = typeRef.value

    src.value    = null
    loaded.value = false
    error.value  = false

    if (!name || !type) return

    const url = vehicleImageUrl(name, type)
    if (!url) return
    src.value = url

    const cached = _cache.get(name)
    if (cached === 'ok')    { loaded.value = true;  return }
    if (cached === 'error') { error.value  = true; src.value = null; return }

    const img  = new Image()
    img.onload = () => {
      _cache.set(name, 'ok')
      if (src.value === url) loaded.value = true
    }
    img.onerror = () => {
      _cache.set(name, 'error')
      if (src.value === url) { error.value = true; src.value = null }
    }
    img.src = url
  }

  watch([nameRef, typeRef], probe, { immediate: true })

  return { src, loaded, error }
}

export function vehicleImageCached(vehicleName) {
  return vehicleName ? _cache.get(vehicleName.trim()) === 'ok' : false
}

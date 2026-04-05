<template>
  <div class="prog-root">
    <div class="controls-bar mb-3">
      <div class="controls-row">

        <!-- Nation -->
        <v-select
          v-model="nation"
          :items="nationOptions"
          item-title="title"
          item-value="value"
          :label="$t('progression_tab.nation')"
          prepend-inner-icon="mdi-flag"
          density="compact"
          variant="outlined"
          hide-details
          class="ctrl-nation"
        />

        <!-- Branch -->
        <div class="seg-ctrl branch-seg">
          <button
            v-for="opt in BRANCH_OPTIONS"
            :key="opt.value"
            class="seg-btn"
            :class="{ 'seg-btn--active': branch === opt.value }"
            @click="branch = opt.value"
          >{{ opt.icon }} {{ $t(opt.labelKey) }}</button>
        </div>

        <!-- Info badges -->
        <div class="stats-badges">
          <span v-if="progressionData.length" class="badge badge-total">
            📋 {{ progressionData.length }}
          </span>
          <span class="badge badge-must">🟢 {{ countByVerdict('MUST') }}</span>
          <span class="badge badge-fill">🔵 {{ countByVerdict('FILL') }}</span>
          <span class="badge badge-skip">🔴 {{ countByVerdict('SKIP') }}</span>
          <span class="badge badge-prem">👑 {{ countByVerdict('PREM') }}</span>
        </div>
      </div>

      <!-- Type filter chips (dynamic per branch) -->
      <div class="type-toggles mt-2">
        <button
          v-for="t in branchTypes"
          :key="t"
          class="type-btn"
          :class="{ 'type-btn--active': activeTypes.has(t) }"
          @click="toggleType(t)"
        >
          {{ TYPE_ICON[t] }} {{ $t(`vehicle_types.${t}`, TYPE_LABELS[t] || t) }}
        </button>
      </div>

      <!-- Lineup Mix -->
      <div class="lineup-mix-row mt-2">
        <span class="ctrl-label lineup-mix-label">{{ $t('progression_tab.lineup_mix') }}</span>
        <div class="lineup-mix-types">
          <div
            v-for="t in activeBranchTypes"
            :key="t"
            class="lineup-type-item"
          >
            <span class="lm-icon" :title="prefDisplay[t]?.label ?? t">{{ prefDisplay[t]?.icon ?? '?' }}</span>
            <button
              class="lm-btn"
              :disabled="(lineupPrefs[t] ?? 0) === 0"
              @click="decPref(t)"
            >−</button>
            <span
              class="lm-count"
              :class="{
                'lm-count--active': (lineupPrefs[t] ?? 0) > 0,
              }"
            >{{ lineupPrefs[t] ?? 0 }}</span>
            <button
              class="lm-btn"
              @click="incPref(t)"
            >+</button>
          </div>
        </div>
        <span class="lm-total">{{ totalPrefUsed }}</span>
        <button class="lm-reset" :title="$t('progression_tab.reset_defaults')" @click="resetLineupPrefs">↺</button>
      </div>
    </div>

    <div class="legend-row mb-3">
      <span v-for="(vc, key) in VERDICT_COLORS" :key="key" class="legend-item">
        <span class="legend-icon">{{ vc.icon }}</span>
        <span class="legend-text">{{ $t(`verdicts.${key.toLowerCase()}`, vc.label) }}</span>
      </span>
      <InfoTip align="right" class="ml-auto">
        <p><b>{{ $t('progression_tab.tip_title') }}</b></p>
        <div class="tip-row"><span class="tip-icon">🟢</span><span><b class="tip-label">{{ $t('verdicts.must') }}</b> — {{ $t('progression_tab.tip_must') }}</span></div>
        <div class="tip-row"><span class="tip-icon">🔵</span><span><b class="tip-label">{{ $t('verdicts.fill') }}</b> — {{ $t('progression_tab.tip_fill') }}</span></div>
        <div class="tip-row"><span class="tip-icon">🟡</span><span><b class="tip-label">{{ $t('verdicts.pass') }}</b> — {{ $t('progression_tab.tip_pass') }}</span></div>
        <div class="tip-row"><span class="tip-icon">🔴</span><span><b class="tip-label">{{ $t('verdicts.skip') }}</b> — {{ $t('progression_tab.tip_skip') }}</span></div>
        <div class="tip-row"><span class="tip-icon">👑</span><span><b class="tip-label">{{ $t('verdicts.prem') }}</b> — {{ $t('progression_tab.tip_prem') }}</span></div>
        <p style="margin-top:8px; color:#475569">{{ $t('progression_tab.tip_lineup') }}</p>
      </InfoTip>
    </div>

    <v-alert
      v-if="!gridData"
      type="info"
      variant="tonal"
      density="compact"
      class="mt-4"
    >
      {{ $t('progression_tab.no_data') }}
    </v-alert>

    <!-- Main Grid -->
    <div v-else class="prog-grid-wrap">
      <div
        class="prog-grid"
        :style="{
          gridTemplateColumns:
            `40px repeat(${gridData.numCols + 1}, minmax(120px, 1fr))`,
        }"
      >

        <!-- Header row  -->
        <div class="grid-hdr grid-hdr--rank">RANK</div>

        <div :style="{ gridColumn: `2 / span ${gridData.numCols}` }" />

        <div class="grid-hdr grid-hdr--prem">👑 PREMIUM</div>

        <template v-for="era in gridData.eras" :key="`era-${era}`">

          <!-- Rank label -->
          <div class="rank-cell">
            <span class="rank-roman">{{ ROMAN[era] }}</span>
          </div>

          <!-- Standard branch columns -->
          <div
            v-for="col in gridData.numCols"
            :key="`cell-${era}-${col}`"
            class="prog-cell"
          >
            <template
              v-for="item in groupedCells(gridData.getCellVehicles(era, col - 1))"
              :key="item.key"
            >
              <div v-if="item.isGroup" class="group-bracket">
                <div class="group-label">📁 {{ item.groupLabel }}</div>
                <ProgressionCard
                  v-for="v in item.vehicles"
                  :key="v._idx"
                  :vehicle="v"
                  :grouped="true"
                  @click="openVehicle?.(v)"
                />
              </div>

              <!-- Single standalone card -->
              <ProgressionCard
                v-else
                :vehicle="item.vehicle"
                @click="openVehicle?.(item.vehicle)"
              />
            </template>
          </div>

          <!-- Premium column — transparent cell, no dashed border -->
          <div class="prog-cell">
            <ProgressionCard
              v-for="v in gridData.getPremVehicles(era)"
              :key="v._idx"
              :vehicle="v"
              @click="openVehicle?.(v)"
            />
          </div>

        </template>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, inject, watch, shallowRef } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTabFilters } from '../composables/useTabFilters.js'
import { useDataStore } from '../stores/useDataStore.js'
import { fmtNation } from '../composables/useVehicleFormatting.js'
import ProgressionCard from '../components/ProgressionCard.vue'
import InfoTip from '../components/InfoTip.vue'
import {
  ROMAN, BRANCH_TYPES, TYPE_LABELS, TYPE_ICON, VERDICT_COLORS, STD_CLASS,
  RANK_PENALTY, RANK_PENALTY_PREMIUM,
  MM_WINDOW, BR_FILL_WINDOW, JUNK_FLOOR, YELLOW_FLOOR, YELLOW_PCTILE,
  VERDICT_MUST, VERDICT_PASS, VERDICT_SKIP, VERDICT_PREM, VERDICT_FILL,
  TANK_TYPES, DEFAULT_LINEUP_SLOTS, LINEUP_PRIORITY,
  BR_ERA_THRESHOLDS,
  CROSS_THRESH, CROSS_SKIP_THRESH, CROSS_BR_WINDOW, CROSS_BR_LOOKBACK,
  NO_CROSS_TYPES, FILL_MIN_SCORE,
} from '../composables/constants.js'

// Store & Inject

const store = useDataStore()
useTabFilters({ brRange: false, minBattles: false, classes: false, types: false })
const openVehicle = inject('openVehicle', null)
const { t }       = useI18n()

const BRANCH_OPTIONS = [
  { value: 'Ground',      icon: '⚙️', labelKey: 'sidebar.ground'      },
  { value: 'Aviation',    icon: '✈️', labelKey: 'sidebar.aviation'    },
  { value: 'Helicopters', icon: '🚁', labelKey: 'sidebar.helicopters' },
  { value: 'LargeFleet',  icon: '🛳️', labelKey: 'sidebar.large_fleet' },
  { value: 'SmallFleet',  icon: '⛵', labelKey: 'sidebar.small_fleet' },
]

const prefDisplay = computed(() => ({
  tank: { icon: '🛡️', label: t('vehicle_types.tank') },
  ...Object.fromEntries(
    Object.entries(TYPE_ICON).map(([k, icon]) => [
      k,
      { icon, label: t(`vehicle_types.${k}`, TYPE_LABELS[k] ?? k) },
    ])
  ),
}))

// Controls

const nation      = ref('')
const branch      = ref('Ground')
const activeTypes = shallowRef(new Set(BRANCH_TYPES.Ground))

const lineupPrefs = ref({})

const nationOptions = computed(() =>
  (store.nations ?? [])
    .filter(n => n !== 'All')
    .map(n => ({ title: fmtNation(n), value: n }))
)

// Initialise nation once the store has loaded
watch(nationOptions, (opts) => {
  if (!nation.value && opts.length) nation.value = opts[0].value
}, { immediate: true })

watch(branch, (newBranch) => {
  activeTypes.value = new Set(BRANCH_TYPES[newBranch] ?? [])
  lineupPrefs.value = defaultLineupPrefs(newBranch, DEFAULT_LINEUP_SLOTS, activeTypes.value)
})

watch(activeTypes, (newActive) => {
  const next = { ...lineupPrefs.value }
  for (const t of Object.keys(next)) {
    if (!newActive.has(t)) next[t] = 0
  }
  lineupPrefs.value = next
})

function toPrefKey(type) {
  return TANK_TYPES.has(type) ? 'tank' : type
}

function fromPrefKey(prefKey, branchName) {
  if (prefKey === 'tank') return [...TANK_TYPES]
  return [prefKey]
}

function defaultLineupPrefs(branchName, totalSlots, active = null) {
  const all = BRANCH_TYPES[branchName] ?? []

  const activeKeys = active
    ? [...new Set(all.filter(t => active.has(t)).map(toPrefKey))]
    : [...new Set(all.map(toPrefKey))]

  const allKeys = [...new Set(all.map(toPrefKey))]
  const prefs   = Object.fromEntries(allKeys.map(k => [k, 0]))

  if (!activeKeys.length || totalSlots <= 0) return prefs

  const prio  = (LINEUP_PRIORITY[branchName] ?? activeKeys).filter(k => activeKeys.includes(k))
  const order = [...prio, ...activeKeys.filter(k => !prio.includes(k))]

  for (let i = 0; i < totalSlots; i++) {
    prefs[order[i % order.length]]++
  }
  return prefs
}

const activeBranchTypes = computed(() => {
  const real = (BRANCH_TYPES[branch.value] ?? []).filter(t => activeTypes.value.has(t))
  return [...new Set(real.map(toPrefKey))]
})

const totalPrefUsed = computed(() =>
  Object.values(lineupPrefs.value).reduce((s, n) => s + n, 0)
)

function incPref(prefKey) {
  lineupPrefs.value = { ...lineupPrefs.value, [prefKey]: (lineupPrefs.value[prefKey] ?? 0) + 1 }
}

function decPref(prefKey) {
  const cur = lineupPrefs.value[prefKey] ?? 0
  if (cur <= 0) return
  lineupPrefs.value = { ...lineupPrefs.value, [prefKey]: cur - 1 }
}

function resetLineupPrefs() {
  lineupPrefs.value = defaultLineupPrefs(branch.value, DEFAULT_LINEUP_SLOTS, activeTypes.value)
}

const branchTypes = computed(() => BRANCH_TYPES[branch.value] ?? [])

function toggleType(t) {
  const next = new Set(activeTypes.value)
  if (next.has(t)) { if (next.size > 1) next.delete(t) }
  else              next.add(t)
  activeTypes.value = next
}

// Algorithm Helpers

function brToEra(br) {
  for (let i = 0; i < BR_ERA_THRESHOLDS.length; i++) {
    if (br <= BR_ERA_THRESHOLDS[i]) return i + 1
  }
  return 8
}

function brDecay(researcherBr, targetBr) {
  const gap = targetBr - researcherBr
  if (gap <= MM_WINDOW) return 1.0
  return Math.max(0.02, Math.exp(-1.1 * (gap - MM_WINDOW)))
}

function rankPenaltyStd(resEra, tgtEra) {
  const diff = tgtEra - resEra
  return RANK_PENALTY[diff] ?? (diff < 0 ? 0.05 : 0.06)
}

function rankPenaltyPrem(resEra, tgtEra) {
  const diff = tgtEra - resEra
  return RANK_PENALTY_PREMIUM[diff] ?? (diff <= 1 ? 1.0 : 0.06)
}

function combinedPenalty(resEra, resBr, tgtEra, tgtBr, isPrem = false) {
  const pen = isPrem
    ? rankPenaltyPrem(resEra, tgtEra)
    : rankPenaltyStd(resEra, tgtEra)
  return pen * brDecay(resBr, tgtBr)
}

function quantile(arr, q) {
  if (!arr.length) return 0
  const s    = [...arr].sort((a, b) => a - b)
  const pos  = (s.length - 1) * q
  const low  = Math.floor(pos)
  const high = Math.ceil(pos)
  return low === high
    ? s[low]
    : s[low] * (high - pos) + s[high] * (pos - low)
}

function computeDynamicThresholds(allMeta) {
  const valid = allMeta.filter(m => m > 1.0)
  if (!valid.length) return [JUNK_FLOOR, YELLOW_FLOOR]
  const yellow = Math.max(quantile(valid, YELLOW_PCTILE), YELLOW_FLOOR)
  return [yellow, yellow]
}

function lineupScore(eraVehicles, anchorBr, junkThresh, minLineup) {
  const cands = eraVehicles.filter(v =>
    v._localScore >= junkThresh &&
    v.BR >= anchorBr - BR_FILL_WINDOW &&
    v.BR <= anchorBr
  )
  if (!cands.length) return 0
  const avg = cands.reduce((s, v) => s + v._localScore, 0) / cands.length
  return avg * Math.min(cands.length, minLineup) / Math.max(minLineup, 1)
}

function bestAnchorForEra(eraVehicles, junkThresh, yellowThresh, minLineup) {
  const candidates = eraVehicles.filter(v => v._localScore >= yellowThresh)
  if (!candidates.length) return { idx: null, br: 0, score: -1 }
  let bestIdx = null, bestBr = 0, bestScore = -1
  for (const v of candidates) {
    const ls = lineupScore(eraVehicles, v.BR, junkThresh, minLineup)
    if (ls > bestScore) { bestScore = ls; bestBr = v.BR; bestIdx = v._idx }
  }
  return { idx: bestIdx, br: bestBr, score: bestScore }
}

function superCat(branchName) {
  if (branchName === 'spaa')                              return 'AntiAir'
  if (BRANCH_TYPES.Ground.includes(branchName))          return 'Ground'
  if (BRANCH_TYPES.Aviation.includes(branchName))        return 'Aviation'
  if (BRANCH_TYPES.Helicopters.includes(branchName))     return 'Aviation'
  if (BRANCH_TYPES.LargeFleet?.includes(branchName))     return 'LargeFleet'
  if (BRANCH_TYPES.SmallFleet?.includes(branchName))     return 'SmallFleet'
  return 'Fleet'
}

// Main Computation

const progressionData = computed(() => {
  const allVehicles = store.allVehicles ?? []
  if (!allVehicles.length || !nation.value) return []

  const selectedNation = nation.value
  const selectedMode   = store.mode
  const brTypes        = BRANCH_TYPES[branch.value] ?? []
  const active         = activeTypes.value          // shallowRef — dep registered
  const prefs          = lineupPrefs.value          // reactive dep — triggers on pref change

  // 1. Filter & deduplicate
  const raw = allVehicles.filter(v =>
    v.Nation === selectedNation &&
    v.Mode   === selectedMode  &&
    (v.vdb_shop_rank ?? 0) > 0 &&
    brTypes.includes(v.Type)   &&
    active.has(v.Type)
  )

  const seen = new Map()
  for (const v of raw) {
    const key = v.vdb_identifier || v.Name
    if (!seen.has(key) || (v.META_SCORE ?? 0) > (seen.get(key).META_SCORE ?? 0))
      seen.set(key, v)
  }

  if (!seen.size) return []

  // 2. Enrich
  const enriched = [...seen.values()].map((v, i) => {
    const br     = parseFloat(v.BR) || 0
    const rawEra = v.vdb_era ? (parseInt(v.vdb_era) || 0) : 0
    const era    = Math.max(1, Math.min(8, rawEra > 0 ? rawEra : brToEra(br)))
    return {
      ...v,
      _idx:          i,
      _era_int:      era,
      _branch:       v.Type || 'unknown',
      _localScore:   parseFloat(v.META_SCORE) || 0,
      Verdict:       VERDICT_PASS,
      Skip_Reason:   '',
      Alt_Vehicle:   '',
      Cross_Hint:    '',
      Cross_Alt:     '',
      Prem_Boost:    0,
      Prem_Pain_Fix: false,
    }
  })

  const stdVehicles  = enriched.filter(v => v.VehicleClass === STD_CLASS)
  const premVehicles = enriched.filter(v => v.VehicleClass !== STD_CLASS)

  const shopSort = v => v.vdb_shop_order != null ? v.vdb_shop_order : v.BR * 10000
  stdVehicles.sort( (a, b) => shopSort(a) - shopSort(b))
  premVehicles.sort((a, b) => shopSort(a) - shopSort(b))

  // 3. Dynamic thresholds
  const [junkThresh, yellowThresh] = computeDynamicThresholds(
    enriched.map(v => v._localScore)
  )

  // Per-era junk threshold
  const eraJunk = {}
  {
    const byEra = {}
    for (const v of stdVehicles) {
      ;(byEra[v._era_int] ??= []).push(v._localScore)
    }
    for (const [e, scores] of Object.entries(byEra)) {
      eraJunk[+e] = computeDynamicThresholds(scores)[0]
    }
  }

  const mustMinMeta = yellowThresh
  const skipMaxMeta = junkThresh

  // Pass 1: MUST / PASS / SKIP per branch
  const byBranch = {}
  for (const v of stdVehicles) {
    ;(byBranch[v._branch] ??= []).push(v)
  }

  for (const grp of Object.values(byBranch)) {
    grp.sort((a, b) => a.BR !== b.BR ? a.BR - b.BR : b._localScore - a._localScore)
    const p60 = quantile(grp.map(v => v._localScore), 0.60)

    for (let pos = 0; pos < grp.length; pos++) {
      const v      = grp[pos]
      const era    = v._era_int
      const locS   = v._localScore
      const noData = locS < 1.0
      const ourGrp = v.vdb_shop_group || ''

      let shouldSkip = false, reason = '', altName = ''

      if (pos > 0 && !noData) {
        let bestEff = 0, bestName = ''
        for (const prev of grp.slice(0, pos)) {
          if (ourGrp && prev.vdb_shop_group === ourGrp) continue
          const eff = prev._localScore *
            combinedPenalty(prev._era_int, prev.BR, era, v.BR)
          if (eff > bestEff) { bestEff = eff; bestName = prev.Name }
        }
        if (bestEff > locS * 1.05) {
          shouldSkip = true
          reason     = `Effective grind on "${bestName}" ` +
                       `(META ${bestEff.toFixed(0)} vs ${locS.toFixed(0)})`
          altName    = bestName
        }
      }

      if (shouldSkip) {
        v.Verdict = VERDICT_SKIP; v.Skip_Reason = reason; v.Alt_Vehicle = altName
      } else if (!noData && locS < (eraJunk[era] ?? skipMaxMeta)) {
        v.Verdict     = VERDICT_SKIP
        v.Skip_Reason = `Weak vehicle (META ${locS.toFixed(0)} ` +
                        `< ${(eraJunk[era] ?? skipMaxMeta).toFixed(0)})`
      } else {
        v.Verdict = (!noData && locS >= p60 && locS >= mustMinMeta)
          ? VERDICT_MUST
          : VERDICT_PASS
      }
    }
  }

  // Pass 2: Cross-branch hints
  for (const v of stdVehicles) {
    if (v.Verdict !== VERDICT_MUST && v.Verdict !== VERDICT_PASS) continue
    if (v._localScore < 1e-3 || NO_CROSS_TYPES.has(v._branch))   continue

    const ourCat = superCat(v._branch)
    let bestMeta = 0, bestName = '', bestBr = 0

    for (const other of stdVehicles) {
      if (other._branch === v._branch)                              continue
      if (superCat(other._branch) !== ourCat)                       continue
      if (other._era_int !== v._era_int)                            continue
      if (other.BR < v.BR - CROSS_BR_LOOKBACK ||
          other.BR > v.BR + CROSS_BR_WINDOW)                        continue
      if (other.Verdict === VERDICT_SKIP)                           continue
      const eff = other._localScore * brDecay(other.BR, v.BR)
      if (eff > bestMeta) { bestMeta = eff; bestName = other.Name; bestBr = other.BR }
    }

    if (bestMeta > v._localScore * CROSS_THRESH) {
      v.Cross_Alt  = bestName
      v.Cross_Hint = `Better to use "${bestName}" (${bestBr.toFixed(1)}) ` +
                     `— stronger in adjacent branch`
      if (v.Verdict === VERDICT_MUST) {
        v.Verdict = VERDICT_PASS
      } else if (bestMeta > v._localScore * CROSS_SKIP_THRESH && bestBr < v.BR) {
        v.Verdict     = VERDICT_SKIP
        v.Skip_Reason = `Better to grind "${bestName}" (${bestBr.toFixed(1)}) ` +
                        `from adjacent branch`
        v.Cross_Hint  = ''
      }
    }
  }

  // Pain eras (no MUST vehicle)
  const eraHasMust = {}
  for (const v of stdVehicles) {
    eraHasMust[v._era_int] ??= false
    if (v.Verdict === VERDICT_MUST) eraHasMust[v._era_int] = true
  }
  const painEras = new Set(
    Object.entries(eraHasMust)
      .filter(([, has]) => !has)
      .map(([e]) => +e)
  )

  // Pass 3: FILL
  for (const [prefKey, want] of Object.entries(prefs)) {
    if (!want || want <= 0) continue

    const realTypes = new Set(fromPrefKey(prefKey, branch.value)
      .filter(t => active.has(t)))
    if (!realTypes.size) continue

    const byEra = {}
    for (const v of stdVehicles) {
      if (!realTypes.has(v._branch)) continue
      ;(byEra[v._era_int] ??= []).push(v)
    }

    for (const grp of Object.values(byEra)) {
      const mustCount = grp.filter(v => v.Verdict === VERDICT_MUST).length
      if (mustCount >= want) continue
      const need = want - mustCount

      const nonSkip = grp
        .filter(v =>
          v.Verdict !== VERDICT_MUST &&
          v.Verdict !== VERDICT_SKIP &&
          v._localScore >= FILL_MIN_SCORE
        )
        .sort((a, b) => b._localScore - a._localScore)

      const skipFallback = grp
        .filter(v => v.Verdict === VERDICT_SKIP && v._localScore >= FILL_MIN_SCORE)
        .sort((a, b) => b._localScore - a._localScore)

      let filled = 0
      for (const cand of [...nonSkip, ...skipFallback]) {
        if (filled >= need) break
        cand.Verdict     = VERDICT_FILL
        cand.Skip_Reason = ''
        cand.Alt_Vehicle = ''
        filled++
      }
    }
  }

  for (const v of stdVehicles) {
    const pk   = toPrefKey(v._branch)
    const want = prefs[pk] ?? 0
    if (want === 0) {
      v.Verdict     = VERDICT_SKIP
      v.Skip_Reason = 'Not in lineup'
      v.Alt_Vehicle = ''
    }
  }

  for (const [prefKey, want] of Object.entries(prefs)) {
    if (want <= 0) continue
    const realTypes = new Set(
      fromPrefKey(prefKey, branch.value).filter(t => active.has(t))
    )
    if (!realTypes.size) continue

    const byEraP4 = {}
    for (const v of stdVehicles) {
      if (!realTypes.has(v._branch)) continue
      ;(byEraP4[v._era_int] ??= []).push(v)
    }

    for (const grp of Object.values(byEraP4)) {
      const mustVehs = grp
        .filter(v => v.Verdict === VERDICT_MUST)
        .sort((a, b) => a._localScore - b._localScore)
      const excess = mustVehs.length - want
      for (let i = 0; i < excess; i++) {
        mustVehs[i].Verdict = VERDICT_PASS
      }
    }
  }

  //Premium: PREM verdict + boost
  for (const v of premVehicles) {
    v.Verdict       = VERDICT_PREM
    v.Prem_Pain_Fix = painEras.has(v._era_int)

    const sameBranchStd = stdVehicles.filter(s => s._branch === v._branch)
    let bestFree = 0
    for (const s of sameBranchStd) {
      const eff = s._localScore *
        combinedPenalty(s._era_int, s.BR, v._era_int, v.BR)
      if (eff > bestFree) bestFree = eff
    }
    const premGrind = v._localScore *
      combinedPenalty(v._era_int, v.BR, v._era_int, v.BR, true)
    v.Prem_Boost = bestFree < 1e-3
      ? Math.round((premGrind / Math.max(v._localScore, 1e-3)) * 100) / 100
      : Math.round((premGrind / bestFree) * 100) / 100
  }

  // Clean dangling SKIP references
  const skipNames = new Set(
    stdVehicles.filter(v => v.Verdict === VERDICT_SKIP).map(v => v.Name)
  )
  for (const v of stdVehicles) {
    if (skipNames.has(v.Alt_Vehicle)) {
      v.Skip_Reason = ''; v.Alt_Vehicle = ''; v.Verdict = VERDICT_PASS
    }
    if (skipNames.has(v.Cross_Alt)) { v.Cross_Alt = ''; v.Cross_Hint = '' }
  }

  return [...stdVehicles, ...premVehicles]
})

// Grid Data

const gridData = computed(() => {
  const vehicles = progressionData.value
  if (!vehicles.length) return null

  const std  = vehicles.filter(v => v.VehicleClass === STD_CLASS)
  const prem = vehicles.filter(v => v.VehicleClass !== STD_CLASS)

  const allEras = new Set()
  for (const v of vehicles) {
    const e = v._era_int
    if (e >= 1 && e <= 8) allEras.add(e)
  }
  const eras = [...allEras].sort((a, b) => a - b)

  const hasShop = std.some(v => parseInt(v.vdb_shop_column ?? -1) >= 0)
  let colMap = null, numCols = 0, typesInDf = null

  if (hasShop) {
    const rawCols = [...new Set(
      std.map(v => parseInt(v.vdb_shop_column ?? -1)).filter(c => c >= 0)
    )].sort((a, b) => a - b)
    colMap  = Object.fromEntries(rawCols.map((old, i) => [old, i]))
    numCols = rawCols.length
  } else {
    typesInDf = [...new Set(std.map(v => v._branch))]
    numCols   = typesInDf.length
  }

  function getCellVehicles(era, colIdx) {
    let cell
    if (hasShop) {
      cell = std.filter(v => {
        const c = colMap[parseInt(v.vdb_shop_column ?? -1)]
        return v._era_int === era && c === colIdx
      })
    } else {
      const brName = typesInDf?.[colIdx]
      cell = std.filter(v => v._era_int === era && v._branch === brName)
    }
    return cell.sort((a, b) => {
      const ar = a.vdb_shop_row ?? 99999
      const br = b.vdb_shop_row ?? 99999
      if (ar !== br) return ar - br
      return (a.vdb_shop_order ?? 99999) - (b.vdb_shop_order ?? 99999)
    })
  }

  function getPremVehicles(era) {
    return prem
      .filter(v => v._era_int === era)
      .sort((a, b) =>
        (a.vdb_shop_order ?? a.BR * 10000) - (b.vdb_shop_order ?? b.BR * 10000)
      )
  }

  return { eras, numCols, typesInDf, getCellVehicles, getPremVehicles }
})

// Group bracketing

function groupedCells(cellVehicles) {
  const result  = []
  const seenGrp = new Map()

  for (const v of cellVehicles) {
    const g = (v.vdb_shop_group || '').trim()
    if (g) {
      if (seenGrp.has(g)) {
        result[seenGrp.get(g)].vehicles.push(v)
      } else {
        seenGrp.set(g, result.length)
        result.push({
          isGroup:    true,
          groupLabel: v.Name.trim(),
          vehicles:   [v],
          key:        `grp-${g}`,
        })
      }
    } else {
      result.push({ isGroup: false, vehicle: v, key: `v-${v._idx}` })
    }
  }
  return result
}

// Stats

function countByVerdict(verdict) {
  return progressionData.value.filter(v => v.Verdict === verdict).length
}
lineupPrefs.value = defaultLineupPrefs(branch.value, DEFAULT_LINEUP_SLOTS, activeTypes.value)
</script>

<style scoped>
.prog-root {
  display: flex;
  flex-direction: column;
  height: 100%;
}

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
.ctrl-nation   { max-width: 200px; flex-shrink: 0; }

.seg-ctrl {
  display: inline-flex;
  gap: 4px;
  background: rgba(10, 22, 40, 0.8);
  padding: 3px;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  flex-shrink: 0;
}
.seg-btn {
  padding: 5px 10px;
  border: 1px solid transparent;
  border-radius: 5px;
  background: transparent;
  color: #475569;
  font-family: 'Rajdhani', sans-serif;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}
.seg-btn:hover:not(.seg-btn--active) {
  color: #94a3b8;
  background: rgba(255, 255, 255, 0.04);
}
.seg-btn--active {
  background: rgba(56, 189, 248, 0.12);
  border-color: rgba(56, 189, 248, 0.5);
  color: #38bdf8;
}

.stats-badges { display: flex; gap: 4px; flex-wrap: wrap; margin-left: auto; }
.badge {
  display: inline-flex;
  align-items: center;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  border-radius: 5px;
  padding: 2px 8px;
  white-space: nowrap;
}
.badge-total { background: rgba(148,163,184,0.10); color: #94a3b8; }
.badge-must  { background: rgba(16,185,129,0.12);  color: #10b981; }
.badge-fill  { background: rgba(56,189,248,0.12);  color: #38bdf8; }
.badge-skip  { background: rgba(248,113,113,0.12); color: #f87171; }
.badge-prem  { background: rgba(167,139,250,0.12); color: #a78bfa; }

.type-toggles { display: flex; flex-wrap: wrap; gap: 4px; }

.type-btn {
  padding: 4px 10px;
  border: 1px solid #1e3a5f;
  border-radius: 5px;
  background: transparent;
  color: #475569;
  font-family: 'Rajdhani', sans-serif;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}
.type-btn:hover:not(.type-btn--active) {
  background: rgba(255, 255, 255, 0.04);
  color: #94a3b8;
  border-color: #334155;
}
.type-btn--active {
  background: rgba(56, 189, 248, 0.12);
  border-color: rgba(56, 189, 248, 0.5);
  color: #38bdf8;
}

.lineup-mix-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 6px 2px 2px;
  border-top: 1px solid rgba(30, 58, 95, 0.6);
}

.lineup-mix-label {
  flex-shrink: 0;
  margin-right: 4px;
  font-size: 12px;
  color: #94a3b8;
}

.lineup-mix-types {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  flex: 1;
}

.lineup-type-item {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid #1e3a5f;
  border-radius: 6px;
  padding: 3px 5px;
}

.lm-icon {
  font-size: 12px;
  line-height: 1;
}

.lm-btn {
  width: 18px;
  height: 18px;
  line-height: 1;
  font-size: 13px;
  font-weight: 700;
  border: 1px solid #1e3a5f;
  border-radius: 4px;
  background: rgba(30, 41, 59, 0.8);
  color: #94a3b8;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  transition: background 0.12s, color 0.12s, border-color 0.12s;
}
.lm-btn:hover:not(:disabled) {
  background: rgba(167, 243, 208, 0.12);
  border-color: #a7f3d0;
  color: #a7f3d0;
}
.lm-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.lm-count {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  color: #475569;
  min-width: 14px;
  text-align: center;
  transition: color 0.12s;
}
.lm-count--active {
  color: #38bdf8;
}

.lm-total {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 5px;
  background: rgba(30, 41, 59, 0.6);
  flex-shrink: 0;
}
.lm-total--full  { color: #10b981; background: rgba(16,185,129,0.10); }
.lm-total--over  { color: #f87171; background: rgba(248,113,113,0.12); }
.lm-total--under { color: #fbbf24; background: rgba(251,191,36,0.08); }

.lm-reset {
  font-size: 14px;
  line-height: 1;
  background: none;
  border: 1px solid #1e3a5f;
  border-radius: 5px;
  color: #475569;
  cursor: pointer;
  padding: 2px 6px;
  transition: color 0.12s, border-color 0.12s;
  flex-shrink: 0;
}
.lm-reset:hover {
  color: #a7f3d0;
  border-color: #a7f3d0;
}

.legend-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  padding: 4px 2px;
}
.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #64748b;
}
.legend-icon { font-size: 12px; }
.legend-text { white-space: nowrap; }
.ml-auto { margin-left: auto; }

.prog-grid-wrap {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  max-height: calc(100vh - 260px);
  padding-bottom: 12px;
}

.prog-grid {
  display: grid;
  gap: 4px;
  align-items: start;
  width: 100%;
}

.grid-hdr {
  background: #1e293b;
  border-radius: 4px;
  padding: 6px 4px;
  text-align: center;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  min-height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.grid-hdr--rank { color: #475569; }
.grid-hdr--prem { color: #a78bfa; }

.rank-cell {
  background: #162032;
  border-radius: 4px;
  padding: 10px 4px;
  text-align: center;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  min-height: 64px;
}
.rank-roman {
  font-family: 'Rajdhani', 'Barlow Condensed', sans-serif;
  font-size: 24px;
  font-weight: 800;
  color: #a7f3d0;
  line-height: 1;
}

.prog-cell {
  min-height: 64px;
  padding: 2px;
  min-width: 0;
}

.group-bracket {
  border-left:   2px solid #334155;
  border-top:    1px solid #1e293b;
  border-right:  1px solid #1e293b;
  border-bottom: 1px solid #1e293b;
  border-radius: 0 4px 4px 0;
  padding: 4px 0;
  margin-bottom: 4px;
  background: rgba(30, 41, 59, 0.35);
}
.group-label {
  font-size: 8px;
  color: #475569;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  padding: 0 4px 2px 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.group-bracket :deep(.prog-card:not(:last-child)) {
  border-bottom-right-radius: 0;
  margin-bottom: 1px;
}
.group-bracket :deep(.prog-card:not(:first-child)) {
  border-top-right-radius: 0;
}
</style>

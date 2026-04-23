<template>
  <div class="veh-img-wrap" :style="wrapStyle">

    <Transition name="veh-img-fade">
      <img
        v-if="src && loaded"
        :src="src"
        :alt="name"
        class="veh-img"
        draggable="false"
      />
    </Transition>

    <Transition name="veh-img-fade">
      <div v-if="!loaded && !imgError && showFallback" class="veh-img-skeleton" />
    </Transition>

    <Transition name="veh-img-fade">
      <div v-if="(imgError || !src) && showFallback" class="veh-img-placeholder">
        <v-icon :size="iconSize" style="opacity:.12;color:#a7f3d0">mdi-image-outline</v-icon>
      </div>
    </Transition>

  </div>
</template>

<script setup>
import { computed, toRef, watch } from 'vue'
import { useVehicleImage } from '../composables/useVehicleImage.js'

const props = defineProps({
  name:         { type: String,  default: null  },
  type:         { type: String,  default: null  },
  aspect:       { type: String,  default: '2/1' },
  fit:          { type: String,  default: 'cover' },
  showFallback: { type: Boolean, default: true   },
})

const emit = defineEmits(['loaded', 'error'])

const nameRef = toRef(props, 'name')
const typeRef = toRef(props, 'type')
const { src, loaded, error: imgError } = useVehicleImage(nameRef, typeRef)

watch(loaded,   v => { if (v) emit('loaded') })
watch(imgError, v => { if (v) emit('error')  })

const wrapStyle = computed(() => ({
  aspectRatio: props.aspect,
  '--veh-fit':  props.fit,
}))

const iconSize = computed(() => props.aspect === '1/1' ? 28 : 36)
</script>

<style scoped>
.veh-img-wrap {
  position: relative;
  width: 100%;
  overflow: hidden;
  background: rgba(30, 58, 95, 0.12);
}
.veh-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: var(--veh-fit, cover);
  object-position: center;
  display: block;
}
.veh-img-skeleton {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    rgba(30, 58, 95, 0.0)  0%,
    rgba(30, 58, 95, 0.25) 50%,
    rgba(30, 58, 95, 0.0)  100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.6s infinite;
}
@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
.veh-img-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.veh-img-fade-enter-active { transition: opacity 0.25s ease; }
.veh-img-fade-leave-active { transition: opacity 0.15s ease; }
.veh-img-fade-enter-from,
.veh-img-fade-leave-to     { opacity: 0; }
</style>

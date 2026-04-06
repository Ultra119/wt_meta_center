<template>
  <v-dialog
    :model-value="modelValue"
    max-width="560"
    persistent
    :close-on-back="false"
    :close-on-content-click="false"
  >
    <v-card color="#0f172a" style="border: 1px solid #1e3a5f;">

      <v-card-title class="d-flex align-center gap-2 px-5 pt-5 pb-0">
        <span class="disclaimer-icon">⚠️</span>
        <span class="disclaimer-title">{{ t('disclaimer.title') }}</span>
      </v-card-title>

      <v-divider color="#1e3a5f" class="mt-3" />

      <v-card-text class="px-5 py-4">
        <p class="disclaimer-body">{{ t('disclaimer.body_1') }}</p>
        <p class="disclaimer-body mt-3">{{ t('disclaimer.body_2') }}</p>

        <v-alert
          type="warning"
          variant="tonal"
          density="compact"
          class="mt-4"
          icon="mdi-alert-outline"
        >
          {{ t('disclaimer.legal') }}
        </v-alert>

        <p class="disclaimer-note mt-3">{{ t('disclaimer.note') }}</p>
      </v-card-text>

      <v-divider color="#1e3a5f" />

      <v-card-actions class="px-5 py-4 justify-end">
        <v-btn
          color="primary"
          variant="elevated"
          size="large"
          prepend-icon="mdi-check-circle-outline"
          @click="$emit('accept')"
        >
          {{ t('disclaimer.accept') }}
        </v-btn>
      </v-card-actions>

    </v-card>
  </v-dialog>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

defineProps({ modelValue: Boolean })
defineEmits(['update:modelValue', 'accept'])
</script>

<style scoped>
.disclaimer-icon  { font-size: 22px; line-height: 1; }
.disclaimer-title {
  font-family: 'Rajdhani', sans-serif;
  font-size: 20px;
  font-weight: 700;
  color: #fbbf24;
  letter-spacing: .06em;
}
.disclaimer-body {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: #cbd5e1;
  line-height: 1.7;
  margin: 0;
}
.disclaimer-note {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #475569;
  margin: 0;
}
</style>

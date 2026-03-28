import { defineConfig } from 'vite'
import vue     from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'
import { fileURLToPath, URL } from 'node:url'

// VITE_BASE_PATH=/wt-meta-center/ npm run build
const BASE = process.env.VITE_BASE_PATH ?? '/'

export default defineConfig({
  base: BASE,
  plugins: [
    vue(),
    vuetify({ autoImport: true }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    outDir: 'dist',
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('vuetify'))                                    return 'vuetify'
          if (id.includes('vue-router') || id.includes('vue-i18n') ||
              id.includes('pinia')      || id.includes('/vue/'))        return 'vendor'
        },
      },
    },
  },
})

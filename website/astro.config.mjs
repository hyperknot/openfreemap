import { defineConfig } from 'astro/config'

import sitemap from '@astrojs/sitemap';

// https://astro.build/config

export default defineConfig({
  site: 'https://openfreemap.org',
  vite: {
    css: {
      transformer: 'lightningcss',
    },
  },
  integrations: [sitemap()],
})

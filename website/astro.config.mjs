// @ts-check

import sitemap from '@astrojs/sitemap'
import { defineConfig } from 'astro/config'

// https://astro.build/config

export default defineConfig({
  site: 'https://openfreemap.org',
  trailingSlash: 'always',
  vite: {
    css: {
      transformer: 'lightningcss',
    },
  },
  integrations: [sitemap()],
})

// @ts-check
import { defineConfig } from 'astro/config'

import sitemap from '@astrojs/sitemap';

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

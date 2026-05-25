/** @type {import('prettier').Config & import('prettier-plugin-tailwindcss').PluginOptions} */
export default {
  printWidth: 100,
  semi: false,
  singleQuote: true,
  plugins: [
    'prettier-plugin-astro',
    '@ianvs/prettier-plugin-sort-imports',
    'prettier-plugin-tailwindcss',
  ],

  tailwindStylesheet: './packages/shared/styles/_tailwind.css',
  astroAllowShorthand: true,

  overrides: [
    {
      files: ['**/*.astro'],
      options: {
        parser: 'astro',
      },
    },
  ],
}

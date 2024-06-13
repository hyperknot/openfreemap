const config = {
  printWidth: 100,
  semi: false,
  singleQuote: true,
  arrowParens: 'avoid',

  plugins: ['prettier-plugin-astro'],
  overrides: [
    {
      files: '*.astro',
      options: {
        parser: 'astro',
      },
    },
  ],
}

module.exports = config

const map = new maplibregl.Map({
  container: 'map',
  hash: 'map',
  style: 'https://tiles.openfreemap.org/styles/liberty',
  center: [0, 0],
  zoom: 2,
})

function modifyStyle({ style, langCode }) {
  if (!langCode) {
    langCode = 'en'
  }

  for (const layer of style.layers) {
    if (layer.source !== 'openmaptiles') continue
    if (!layer.layout) continue

    const textField = layer.layout['text-field']
    if (!textField) continue

    // highway numbers, etc. - skip ref-only fields
    if (JSON.stringify(textField) === JSON.stringify(['to-string', ['get', 'ref']])) continue

    const nameUnderscore = `name_${langCode}`
    const nameColon = `name:${langCode}`

    // Always display both values
    layer.layout['text-field'] = ['concat', ['get', nameUnderscore], '\n', ['get', nameColon]]

    // Color red when they are different
    if (!layer.paint) layer.paint = {}
    layer.paint['text-color'] = [
      'case',
      ['!=', ['get', nameUnderscore], ['get', nameColon]],
      '#ff0000', // Red when different
      '#000000', // Default color when same (adjust as needed)
    ]
  }
}

function getLanguageParam() {
  const urlParams = new URLSearchParams(window.location.search)
  return urlParams.get('lang')
}

function applyLanguage() {
  const langCode = getLanguageParam() || null

  const style = map.getStyle()
  modifyStyle({ style, langCode })
  map.setStyle(style, { diff: false })
}

map.on('load', () => {
  const langCode = getLanguageParam()

  // Alert the URL param value on first load
  alert(
    `Language parameter: ${langCode || 'not set (defaulting to en)'}\n\n` +
      'To change the map language, modify the ?lang= parameter in the URL.\n' +
      'Labels will be RED when different.\n' +
      'name_xx on line 1, name:xx on line 2',
  )

  // Add default param if not present
  if (!langCode) {
    const url = new URL(window.location)
    url.searchParams.set('lang', 'en')
    window.history.replaceState({}, '', url)
  }

  applyLanguage()
})

// Listen for URL changes (e.g., browser back/forward)
window.addEventListener('popstate', () => {
  applyLanguage()
})

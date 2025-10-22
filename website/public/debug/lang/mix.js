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

function applyLanguage() {
  const hash = window.location.hash.substring(1) // Remove the '#'
  const langCode = hash || null

  const style = map.getStyle()
  modifyStyle({ style, langCode })
  map.setStyle(style, { diff: false })
}

map.on('load', () => {
  // Add default hash if not present
  if (!window.location.hash) {
    alert(
      'To change the map language, modify the language code in the URL #.\nLabels will be RED when different.\nname_xx on line 1, name:xx on line 2',
    )
    window.location.hash = '#en'
    // The hashchange event will trigger applyLanguage()
  } else {
    applyLanguage()
  }
})

// Listen for hash changes in URL
window.addEventListener('hashchange', () => {
  applyLanguage()
})

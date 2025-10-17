const map = new maplibregl.Map({
  container: 'map',
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

    const id = layer.id

    let separator
    if (id.includes('line') || id.includes('highway')) {
      separator = ' '
    } else {
      separator = '\n'
    }

    // the default is "en", not "int"
    let parts
    if (langCode === 'int') {
      parts = [['get', 'name']]
    } else {
      parts = [
        ['get', `name_${langCode}`],
        ['get', `name:${langCode}`],
        ['get', 'name'],
      ]
    }

    layer.layout['text-field'] = [
      'case',
      ['has', 'name:nonlatin'],
      ['concat', ['get', 'name:latin'], separator, ['get', 'name:nonlatin']],
      ['coalesce', ...parts],
    ]
  }
}

function applyLanguage() {
  const hash = window.location.hash.substring(1); // Remove the '#'
  const langCode = hash || null;

  const style = map.getStyle()
  modifyStyle({ style, langCode })
  map.setStyle(style, { diff: false })
}

map.on('load', () => {
  // Add default hash if not present
  if (!window.location.hash) {
    alert('To change the map language, modify the language code in the URL.\n\nExamples:\n• #en → English\n• #de → German\n• #fr → French\n• #es → Spanish\n• #int → International names\n\nDefault language set to: en (English)')
    window.location.hash = '#es'
    // The hashchange event will trigger applyLanguage()
  } else {
    applyLanguage()
  }
})

// Listen for hash changes in URL
window.addEventListener('hashchange', () => {
  applyLanguage()
})

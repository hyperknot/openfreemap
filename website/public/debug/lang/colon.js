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

    const nameUnderscore = `name_${langCode}`
    const nameColon = `name:${langCode}`

    // Construct parts with exactly name_ and name: versions only (no int special case, no 'name' fallback)
    const parts = [
      ['get', nameUnderscore],
      ['get', nameColon],
    ]

    layer.layout['text-field'] = [
      'case',
      ['has', 'name:nonlatin'],
      ['concat', ['get', 'name:latin'], separator, ['get', 'name:nonlatin']],
      ['coalesce', ...parts],
    ]

    // Set color to red if both exist and are different, black otherwise
    if (!layer.paint) layer.paint = {}

    layer.paint['text-color'] = [
      'case',
      // If both name_ and name: exist and are different, show red
      [
        'all',
        ['has', nameUnderscore],
        ['has', nameColon],
        ['!=', ['get', nameUnderscore], ['get', nameColon]]
      ],
      '#ff0000', // Red when different
      '#000000'  // Black when same or only one exists
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
    alert('To change the map language, modify the language code in the URL #.\nLabels will be RED if name_xx and name:xx differ')
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

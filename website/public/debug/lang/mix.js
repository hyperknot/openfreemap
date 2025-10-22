const map = new maplibregl.Map({
  container: 'map',
  style: 'https://tiles.openfreemap.org/styles/liberty',
  center: [0, 0],
  zoom: 2,
})

const line1Input = document.getElementById('line1')
const line2Input = document.getElementById('line2')
const langInput = document.getElementById('lang')

// Parse URL search params to get line1 and line2
function parseParams() {
  const params = new URLSearchParams(window.location.search)
  return {
    line1: params.get('line1') || 'underscore,colon,name,latin',
    line2: params.get('line2') || 'nonlatin',
    lang: params.get('lang') || 'en',
  }
}

// Update URL search params
function updateParams(line1, line2, lang) {
  const url = new URL(window.location)
  url.searchParams.set('line1', line1)
  url.searchParams.set('line2', line2)
  url.searchParams.set('lang', lang)
  window.history.replaceState({}, '', url)
}

// Build field accessor from config string
function buildFieldAccessor(config, langCode) {
  const parts = []
  const fields = config.split(',').map(f => f.trim()).filter(f => f)

  for (const field of fields) {
    if (field === 'underscore') {
      parts.push(['get', `name_${langCode}`])
    } else if (field === 'colon') {
      parts.push(['get', `name:${langCode}`])
    } else if (field === 'name') {
      parts.push(['get', 'name'])
    } else if (field === 'latin') {
      parts.push(['get', 'name:latin'])
    } else if (field === 'nonlatin') {
      parts.push(['get', 'name:nonlatin'])
    } else {
      // Custom field name
      parts.push(['get', field])
    }
  }

  return parts.length > 0 ? ['coalesce', ...parts] : ['get', 'name']
}

function modifyStyle({ style, line1Config, line2Config, langCode }) {
  for (const layer of style.layers) {
    if (layer.source !== 'openmaptiles') continue
    if (!layer.layout) continue

    const textField = layer.layout['text-field']
    if (!textField) continue

    // Skip ref-only fields
    if (JSON.stringify(textField) === JSON.stringify(['to-string', ['get', 'ref']])) continue

    const id = layer.id
    let separator = id.includes('line') || id.includes('highway') ? ' ' : '\n'

    const line1Expr = buildFieldAccessor(line1Config, langCode)
    const line2Expr = buildFieldAccessor(line2Config, langCode)

    // Combine both lines
    layer.layout['text-field'] = ['concat', line1Expr, separator, line2Expr]
  }
}

function applyConfiguration() {
  const { line1, line2, lang } = parseParams()

  if (!map.getStyle()) return

  const style = map.getStyle()
  modifyStyle({ style, line1Config: line1, line2Config: line2, langCode: lang })
  map.setStyle(style, { diff: false })
}

function syncInputsFromParams() {
  const { line1, line2, lang } = parseParams()
  line1Input.value = line1
  line2Input.value = line2
  langInput.value = lang
}

// Update params when inputs change
line1Input.addEventListener('input', () => {
  updateParams(line1Input.value, line2Input.value, langInput.value)
})

line2Input.addEventListener('input', () => {
  updateParams(line1Input.value, line2Input.value, langInput.value)
})

langInput.addEventListener('input', () => {
  updateParams(line1Input.value, line2Input.value, langInput.value)
})

// Apply configuration when Enter is pressed
line1Input.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') applyConfiguration()
})

line2Input.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') applyConfiguration()
})

langInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') applyConfiguration()
})

map.on('load', () => {
  // Initialize params if not present
  const params = new URLSearchParams(window.location.search)
  if (!params.has('line1') || !params.has('line2') || !params.has('lang')) {
    const url = new URL(window.location)
    if (!params.has('line1')) url.searchParams.set('line1', 'underscore,colon,name,latin')
    if (!params.has('line2')) url.searchParams.set('line2', 'nonlatin')
    if (!params.has('lang')) url.searchParams.set('lang', 'en')
    window.history.replaceState({}, '', url)
  }

  syncInputsFromParams()
  applyConfiguration()
})

// Listen for URL changes (e.g., browser back/forward)
window.addEventListener('popstate', () => {
  syncInputsFromParams()
  applyConfiguration()
})
// ============================================
// 1. MAIN EXECUTION (Entry Point)
// ============================================

const map = new maplibregl.Map({
  container: 'map',
  style: 'https://tiles.openfreemap.org/styles/liberty',
  center: [0, 0],
  zoom: 2,
  hash: true,
})

const line1Input = document.getElementById('line1')
const line2Input = document.getElementById('line2')
const langInput = document.getElementById('lang')
const line1ExprInput = document.getElementById('line1-expr')
const line2ExprInput = document.getElementById('line2-expr')
const showDifferencesRedCheckbox = document.getElementById('showDifferencesRed')

map.on('load', () => {
  const params = new URLSearchParams(window.location.search)

  // Set defaults if no params present
  if (!params.has('line1') && !params.has('line2') && !params.has('lang')) {
    const url = new URL(window.location)
    url.searchParams.set('line1', 'colon,underscore,latin,name')
    url.searchParams.set('line2', 'nonlatin')
    url.searchParams.set('lang', 'en')
    window.history.replaceState({}, '', url)
  }
  syncInputsFromParams()
  applyConfiguration()
  initializeInputListeners()
  initializeModal()
  initializeResetButton()
})

// ============================================
// 2. UI INITIALIZATION
// ============================================

function initializeInputListeners() {
  const debouncedApplyConfig = debounce(applyConfiguration, 500)

  const handleInput = () => {
    updateParamsFromInputs()
    updateExpressionDisplays()
    debouncedApplyConfig()
  }

  line1Input.addEventListener('input', handleInput)
  line2Input.addEventListener('input', handleInput)
  langInput.addEventListener('input', handleInput)
  showDifferencesRedCheckbox.addEventListener('change', handleInput)
}

function initializeModal() {
  const modal = document.getElementById('shareModal')

  document.getElementById('shareBtn').addEventListener('click', () => {
    modal.classList.remove('hidden')
  })

  document.getElementById('closeModalBtn').addEventListener('click', () => {
    modal.classList.add('hidden')
  })

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
      modal.classList.add('hidden')
    }
  })
}

function initializeResetButton() {
  document.getElementById('resetBtn').addEventListener('click', () => {
    const hash = window.location.hash
    window.location.href = `${window.location.pathname}${hash}`
  })
}

// ============================================
// 3. CONFIGURATION & SYNC
// ============================================

function applyConfiguration() {
  const { line1, line2, lang, showDifferencesRed } = parseParams()

  if (!map.getStyle()) return

  const style = map.getStyle()
  modifyStyle({
    style,
    line1Config: line1 ?? '',
    line2Config: line2 ?? '',
    langCode: lang,
    showDifferencesRed,
  })
  map.setStyle(style, { diff: true })
  updateExpressionDisplays()
}

function syncInputsFromParams() {
  const { line1, line2, lang, showDifferencesRed } = parseParams()
  line1Input.value = line1 ?? ''
  line2Input.value = line2 ?? ''
  langInput.value = lang ?? ''
  showDifferencesRedCheckbox.checked = showDifferencesRed
}

function updateParamsFromInputs() {
  const params = new URLSearchParams(window.location.search)
  params.set('line1', line1Input.value)
  params.set('line2', line2Input.value)
  params.set('lang', langInput.value)

  if (showDifferencesRedCheckbox.checked) {
    params.set('showDifferencesRed', '1')
  } else {
    params.delete('showDifferencesRed')
  }

  const queryString = params.toString()
  const hash = window.location.hash
  const newUrl = `${window.location.pathname}?${queryString}${hash}`

  window.history.replaceState({}, '', newUrl)
}

function updateExpressionDisplays() {
  const { line1, line2, lang } = parseParams()
  const langCode = lang

  const line1Expr = buildFieldAccessor(line1 ?? '', langCode)
  const line2Expr = buildFieldAccessor(line2 ?? '', langCode)

  line1ExprInput.value = line1Expr ? JSON.stringify(line1Expr) : ''
  line2ExprInput.value = line2Expr ? JSON.stringify(line2Expr) : ''
}

// ============================================
// 4. STYLE MODIFICATION
// ============================================

function modifyStyle({ style, line1Config, line2Config, langCode, showDifferencesRed }) {
  for (const layer of style.layers) {
    if (layer.source !== 'openmaptiles') continue
    if (!layer.layout) continue

    const textField = layer.layout['text-field']
    if (!textField) continue

    if (JSON.stringify(textField) === JSON.stringify(['to-string', ['get', 'ref']])) continue

    const id = layer.id
    const separator = id.includes('line') || id.includes('highway') ? ' ' : '\n'

    const line1Expr = buildFieldAccessor(line1Config, langCode)
    const line2Expr = buildFieldAccessor(line2Config, langCode)

    if (line1Expr && line2Expr) {
      layer.layout['text-field'] = ['concat', line1Expr, separator, line2Expr]
    } else if (line1Expr) {
      layer.layout['text-field'] = line1Expr
    } else if (line2Expr) {
      layer.layout['text-field'] = line2Expr
    } else {
      layer.layout['text-field'] = ['get', 'name']
    }

    // Apply red color when differences should be shown
    if (showDifferencesRed && line1Expr && line2Expr) {
      if (!layer.paint) layer.paint = {}
      layer.paint['text-color'] = [
        'case',
        ['!=', line1Expr, line2Expr],
        '#ff0000', // Red when different
        '#000000', // Black when same
      ]
    } else {
      // Reset to default color if checkbox is unchecked
      if (layer.paint && layer.paint['text-color']) {
        delete layer.paint['text-color']
      }
    }
  }
}

// ============================================
// 5. UTILITY FUNCTIONS
// ============================================

function debounce(func, delay) {
  let timeoutId

  return function (...args) {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => {
      func.apply(this, args)
    }, delay)
  }
}

function parseParams() {
  const params = new URLSearchParams(window.location.search)
  return {
    line1: params.get('line1'),
    line2: params.get('line2'),
    lang: params.get('lang') || 'en',
    showDifferencesRed: params.has('showDifferencesRed'),
  }
}

function buildFieldAccessor(config, langCode) {
  if (!config) return null

  const parts = []
  const fields = config
    .split(',')
    .map(f => f.trim())
    .filter(f => f)

  for (const field of fields) {
    if (field === 'underscore') {
      parts.push(['get', `name_${langCode}`])
    } else if (field === 'colon') {
      parts.push(['get', `name:${langCode}`])
    } else if (field === 'latin') {
      parts.push(['get', 'name:latin'])
    } else if (field === 'nonlatin') {
      parts.push(['get', 'name:nonlatin'])
    } else if (field === 'name') {
      parts.push(['get', 'name'])
    } else {
      parts.push(['get', field])
    }
  }

  return parts.length > 0 ? ['coalesce', ...parts] : null
}

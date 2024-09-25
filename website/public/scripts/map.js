const london3d = {
  center: [-0.114, 51.506],
  zoom: 14.2,
  bearing: 55.2,
  pitch: 60,
}

const berlin = {
  center: [13.388, 52.517],
  zoom: 9.5,
  bearing: 0,
  pitch: 0,
}

function initMap() {
  if (window.map) return

  document.getElementById('mapbg-image').style.opacity = '0.5'

  // RTL support, optional
  maplibregl.setRTLTextPlugin(
    'https://unpkg.com/@mapbox/mapbox-gl-rtl-text@0.3.0/dist/mapbox-gl-rtl-text.js',
    true, // Lazy load the plugin
  )

  const map = new maplibregl.Map({
    style: 'https://tiles.openfreemap.org/styles/liberty',
    center: berlin.center,
    zoom: berlin.zoom,
    bearing: berlin.bearing,
    pitch: berlin.pitch,
    container: mapDiv,
    boxZoom: false,
    // doubleClickZoom: false,
    // scrollZoom: false,
    attributionControl: false,
    cooperativeGestures: true,
    dragRotate: false,
  })
  window.map = map

  map.once('idle', () => {
    document.getElementById('mapbg-image').remove()
  })

  const nav = new maplibregl.NavigationControl({ showCompass: false })
  map.addControl(nav, 'top-right')

  // let scale = new maplibregl.ScaleControl()
  // map.addControl(scale)

  const attrib = new maplibregl.AttributionControl({
    compact: false,
  })
  map.addControl(attrib)

  new maplibregl.Marker().setLngLat([-0.119, 51.507]).addTo(map)
}

function selectStyle(style) {
  const styleUrl = `https://tiles.openfreemap.org/styles/${style.split('-')[0]}`
  map.setStyle(styleUrl)

  if (style === 'liberty-3d') {
    map.setCenter(london3d.center)
    map.setPitch(london3d.pitch)
    map.setBearing(london3d.bearing)
    map.setZoom(london3d.zoom)
    map.dragRotate.enable()
  } else if (map.getBearing() !== 0) {
    map.setCenter(berlin.center)
    map.setPitch(berlin.pitch)
    map.setBearing(berlin.bearing)
    map.setZoom(berlin.zoom)
    map.dragRotate.disable()
  }

  document.getElementById('style-url-code').innerText = styleUrl
}

// --- start

const mapDiv = document.getElementById('map-container')
initMap()

const buttons = document.querySelectorAll('.button-container .btn')

buttons.forEach((button) => {
  button.addEventListener('click', (event) => {
    buttons.forEach((button) => button.classList.remove('selected'))
    button.classList.add('selected')

    const style = event.target.getAttribute('data-style')
    selectStyle(style)
  })
})

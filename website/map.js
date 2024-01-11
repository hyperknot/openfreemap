const map = new maplibregl.Map({
  style: 'https://tiles.openfreemap.org/styles/liberty',
  center: [-0.114, 51.506],
  zoom: 14.2,
  bearing: 55.2,
  pitch: 60,
  container: 'map',
  boxZoom: false,
  doubleClickZoom: false,
  scrollZoom: false,
})

let nav = new maplibregl.NavigationControl({ showCompass: false })
map.addControl(nav, 'top-right')

let scale = new maplibregl.ScaleControl()
map.addControl(scale)

new maplibregl.Marker().setLngLat([-0.122, 51.503]).addTo(map)

const map = new maplibregl.Map({
  container: 'map',
  hash: 'map',
  zoom: 10.5,
  center: [9.0788, 47.1194],
  style: {
    version: 8,
    sources: {
      hillshadeSource: {
        type: 'raster-dem',
        url: 'https://tiles.mapterhorn.com/tilejson.json',
      },
    },
    layers: [
      {
        id: 'hillshade',
        type: 'hillshade',
        source: 'hillshadeSource',
      },
    ],
  },
})

map.on('load', () => {
  console.log('Terrain map loaded')
})
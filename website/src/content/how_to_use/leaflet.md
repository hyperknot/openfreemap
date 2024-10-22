## Using Leaflet

[MapLibre GL Leaflet](https://github.com/maplibre/maplibre-gl-leaflet) provides a binding for Leaflet that allows you to add vector tile sources to the Leaflet map.

Include the following links and scripts in your page:

```html
<!-- Leaflet -->
<link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>

<!-- Maplibre GL -->
<link href="https://unpkg.com/maplibre-gl/dist/maplibre-gl.css" rel='stylesheet' />
<script src="https://unpkg.com/maplibre-gl/dist/maplibre-gl.js"></script>

<!-- Maplibre GL Leaflet  -->
<script src="https://unpkg.com/@maplibre/maplibre-gl-leaflet/leaflet-maplibre-gl.js"></script>
```

Initialize it to a div like this:

```html
<div id="map" style="width: 100%; height: 500px"></div>
<script>
  const map = L.map('map')
    .setView([52.517, 13.388], 9.5)

  L.maplibreGL({
    style: 'https://tiles.openfreemap.org/styles/liberty'
  }).addTo(map)
</script>
```

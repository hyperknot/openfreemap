## How to load MapLibre?

Include <a href="https://maplibre.org/maplibre-gl-js/docs/" target="_blank">MapLibre GL JS</a> in the `<head>`. If you are using npm, you can install the `maplibre-gl` package. Make sure to import the CSS as well.

```html
<script src="https://unpkg.com/maplibre-gl/dist/maplibre-gl.js"></script>
<link href="https://unpkg.com/maplibre-gl/dist/maplibre-gl.css" rel="stylesheet" />
```

Initialize it to a div like this:

```html
<div id="map" style="width: 100%; height: 500px"></div>
<script>
  const map = new maplibregl.Map({
    style: 'https://tiles.openfreemap.org/styles/liberty',
    center: [13.388, 52.517],
    zoom: 9.5,
    container: 'map',
  })
</script>
```

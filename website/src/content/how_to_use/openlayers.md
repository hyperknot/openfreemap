## Using OpenLayers

[ol-mapbox-style](https://openlayers.org/ol-mapbox-style/) is an OpenLayers add-on that creates a layer group from a Mapbox/MapLibre style.

Include the following links and scripts in your page:

```html
<!-- OpenLayers -->
<script src="https://unpkg.com/ol/dist/ol.js"></script>
<link rel="stylesheet" href="https://unpkg.com/ol/ol.css" />

<!-- ol-mapbox-style -->
<script src="https://unpkg.com/ol-mapbox-style/dist/olms.js"></script>
```

Initialize it to a div like this:

```html
<div id="map" style="width: 100%; height: 500px"></div>
<script>
  const openfreemap = new ol.layer.Group()
  const map = new ol.Map({
    layers: [openfreemap],
    view: new ol.View({ center: ol.proj.fromLonLat([13.388, 52.517]), zoom: 9.5 }),
    target: 'map',
  })
  olms.apply(openfreemap, 'https://tiles.openfreemap.org/styles/liberty')
</script>
```

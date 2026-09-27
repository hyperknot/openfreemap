## Using OpenLayers

[ol-mapbox-style](https://openlayers.org/ol-mapbox-style/) creates OpenLayers layers from a MapLibre style.

```sh
npm install ol ol-mapbox-style
```

```js
import Map from 'ol/Map.js'
import View from 'ol/View.js'
import LayerGroup from 'ol/layer/Group.js'
import { fromLonLat } from 'ol/proj.js'
import { apply } from 'ol-mapbox-style'
import 'ol/ol.css'

const openfreemap = new LayerGroup()
apply(openfreemap, 'https://tiles.openfreemap.org/styles/liberty')

new Map({
  target: 'map',
  layers: [openfreemap],
  view: new View({ center: fromLonLat([13.388, 52.517]), zoom: 10.5 }),
})
```

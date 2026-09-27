## How to load MapLibre?

Install [MapLibre GL JS](https://maplibre.org/maplibre-gl-js/docs/):

```sh
npm install maplibre-gl
```

Add a map container to your page:

```html
<div id="map" style="height: 500px"></div>
```

Then initialize the map:

```js
import { Map, setWorkerUrl } from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import 'maplibre-gl/dist/maplibre-gl.css'

// Vite worker setup
setWorkerUrl(workerUrl)

new Map({
  container: 'map',
  style: 'https://tiles.openfreemap.org/styles/liberty',
  center: [13.388, 52.517],
  zoom: 9.5,
})
```

For other bundlers, see MapLibre's [installation guide](https://maplibre.org/maplibre-gl-js/docs/#installation).

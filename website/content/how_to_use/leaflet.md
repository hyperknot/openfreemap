## Using Leaflet

[MapLibre GL Leaflet](https://github.com/maplibre/maplibre-gl-leaflet) lets you add OpenFreeMap vector tiles to a Leaflet map.

```sh
npm install leaflet maplibre-gl @maplibre/maplibre-gl-leaflet
```

```js
import * as L from 'leaflet'
import { maplibreGL } from '@maplibre/maplibre-gl-leaflet'
import { setWorkerUrl } from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import 'leaflet/dist/leaflet.css'
import 'maplibre-gl/dist/maplibre-gl.css'

// Vite worker setup
setWorkerUrl(workerUrl)

const map = L.map('map').setView([52.517, 13.388], 10)
maplibreGL({ style: 'https://tiles.openfreemap.org/styles/liberty' }).addTo(map)
```

# Inspecting tiles

To check whether a feature or label is present in the tile data, use the Maputnik editor in Inspect mode.

1. Open one of these links:
   - [Inspect Bright](https://maputnik.github.io/editor/?style=https://tiles.openfreemap.org/styles/bright)
   - [Inspect Liberty](https://maputnik.github.io/editor/?style=https://tiles.openfreemap.org/styles/liberty)
   - [Inspect Positron](https://maputnik.github.io/editor/?style=https://tiles.openfreemap.org/styles/positron)

2. Select **View / Inspect** in the top menu.

3. Zoom into the area in question and click on the feature. The panel will show all raw data fields in the tile (e.g. `name`, `name:en`, `class`, `subclass`, etc.).

## Interpreting the results

- **Feature is visible in Inspect mode:** the data is in the tiles. Any rendering change is a style issue and belongs in the [styles repo](https://github.com/hyperknot/openfreemap-styles).

- **Feature is missing in Inspect mode:** the data is not in the tiles. This is either an OpenStreetMap data issue or an OpenMapTiles schema limitation. Schema requests are tracked under the [`openmaptiles` label](https://github.com/hyperknot/openfreemap/labels/openmaptiles).

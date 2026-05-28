# Tile generation release cadence

This document describes how full-planet tile releases are generated and deployed.

## Schedule

The tilegen cron file is `tilegen/cron.d/ofm_tilegen`.

Planet release jobs run in UTC:

| Time          | Job                             |
| ------------- | ------------------------------- |
| Sunday 08:00  | Build and upload planet tiles   |
| Tuesday 08:00 | Set the deployed planet version |

The build job runs:

```bash
cd /data/ofm/src && PYTHONUNBUFFERED=1 ./tilegen/scripts/tilegen.py make-tiles planet --upload
```

The deploy job runs:

```bash
cd /data/ofm/src && PYTHONUNBUFFERED=1 ./tilegen/scripts/tilegen.py set-version planet
```

## Upstream OSM planet timing

OpenStreetMap snapshots the full planet database on Monday. The snapshot date is encoded in the filename, for example `planet-260518.osm.pbf` is the `2026-05-18` snapshot.

The PBF files are published later at <https://planet.openstreetmap.org/pbf/>. The `.md5` checksum appears after the PBF file and marks the release as complete.

The Sunday 08:00 UTC build time is chosen to give the OSM planet release enough time to finish before Planetiler downloads the latest planet.

## Build pipeline

`make-tiles planet --upload` creates one versioned run directory under:

```text
/data/ofm/tilegen/runs/planet/{version}_pt
```

The run version is based on the run start timestamp, for example:

```text
20260526_232801_pt
```

The pipeline is:

1. Run Planetiler and create `tiles.mbtiles`.
2. Update MBTiles metadata.
3. Write SHA256 checksum for `tiles.mbtiles`.
4. Upload `tiles.mbtiles` to the Btrfs bucket.
5. Extract MBTiles into a Btrfs image.
6. Shrink the Btrfs image.
7. Write SHA256 checksum for `tiles.btrfs`.
8. Upload `tiles.btrfs`.
9. Gzip the Btrfs image to `tiles.btrfs.gz`.
10. Write SHA256 checksum for `tiles.btrfs.gz`.
11. Upload `tiles.btrfs.gz`.
12. Delete local Btrfs files to save disk space.
13. Convert `tiles.mbtiles` to `tiles.pmtiles`.
14. Verify `tiles.pmtiles`.
15. Write SHA256 checksum for `tiles.pmtiles`.
16. Upload `tiles.pmtiles`.
17. Move logs and stats into the run `logs/` directory.
18. Upload remaining small files and `SHA256SUMS`.
19. Create the remote `done` marker.
20. Rebuild the `ofm-btrfs` bucket indexes.

The remote run is uploaded under:

```text
remote:ofm-btrfs/areas/planet/{version}_pt
```

The `done` file marks a run as complete. Version discovery only considers runs that have this marker.

## Deploy pipeline

`set-version planet` deploys the latest completed planet run.

The command:

1. Reads <https://btrfs.openfreemap.com/files.txt>.
2. Finds completed planet versions by looking for:

   ```text
   areas/planet/{version}/done
   ```

3. Sorts the completed versions.
4. Selects the latest version.
5. Reads the currently deployed version from:

   ```text
   https://assets.openfreemap.com/deployed_versions/planet.txt
   ```

6. If the latest completed version is already deployed, exits without changes.
7. Otherwise writes the selected version to:

   ```text
   remote:ofm-assets/deployed_versions/planet.txt
   ```

Linux tile hosts use this deployed version file to decide which planet version to download and mount.

## Public bucket indexes

The tilegen host maintains public index files for the R2 buckets:

- <https://btrfs.openfreemap.com/files.txt>
- <https://btrfs.openfreemap.com/dirs.txt>
- <https://assets.openfreemap.com/files.txt>
- <https://assets.openfreemap.com/dirs.txt>

The hourly `make-indexes` cron refreshes indexes for both buckets. The planet build job also refreshes the `ofm-btrfs` index after a successful upload.

## Observed full-planet runtime

Latest investigated run: `20260526_232801_pt`

- Started: `2026-05-26 23:28:01 UTC`
- Finished: `2026-05-27 14:46:50 UTC`
- Total wall time: about **15h 18m 49s**

Approximate step breakdown:

| Step                                          | Approx duration |
| --------------------------------------------- | --------------: |
| Planetiler generation                         |  **5h 22m 12s** |
| MBTiles metadata/checksum/upload              |    **~20m 51s** |
| Btrfs image creation + checksum               | **~7h 04m 30s** |
| Btrfs upload                                  |    **~34m 00s** |
| Gzip Btrfs + checksum + upload                |    **~26m 19s** |
| PMTiles create/verify/checksum                | **~1h 12m 48s** |
| PMTiles upload                                |    **~18m 04s** |
| Final small-file upload / done marker / index |         **~4s** |

Planetiler internal breakdown for that run:

| Planetiler substep    |       Duration |
| --------------------- | -------------: |
| download              |    **18m 47s** |
| wikidata              |    **19m 28s** |
| osm_pass1             |    **10m 11s** |
| osm_pass2             | **2h 08m 41s** |
| sort                  |    **11m 04s** |
| archive/write MBTiles | **2h 11m 12s** |
| overall               | **5h 22m 12s** |

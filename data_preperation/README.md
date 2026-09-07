## Pipeline

Run these scripts in order from this directory. Default I/O paths are relative (`./dataset_roads`, `./data`); edit `__main__` if your data live elsewhere.

1. OSM → classed road rasters: `python main_osm2roads.py`
2. OSM → land-use rasters: `python main_osm2landuse.py`
3. Road-density heatmap: `python main_gen_road_density.py`
4. Buildings in China (local height data) → raster: `python main_buildings_cn.py`
5. Buildings outside China (Microsoft footprints) → raster: `python main_building_oversea.py`
6. Align all rasters and crop tiles: `python batch_align_crop.py`
7. Road topology per tile: `python main_gen_road_topo.py`
8. Per-tile urban metrics: `python main_cal_tile_statics.py`
9. Visualize tile channels: `python main_read_tiles.py`
10. Text prompts from metrics: `python main_gen_prompts.py`
11. Buildings inside each urban block: `python main_extract_building_per_tile.py`

See the repository root `README.md` for the full file-by-file guide, including optional scripts (`main_osm2poi.py`, `split_train_val_test.py`, evaluation, etc.).

## Scripts

Helpers used by the `main_*.py` entry points (under `scripts/`):

- Binary image → topology ([skeleton-tracing](https://github.com/LingDong-/skeleton-tracing)): `trace_skeleton.py`. Preferred over `sknw/` (better results).
- OSM parsing: `python osm_parsing.py`
  - Roads: classed GeoJSON under `osmnx_geojson_roads`
  - Building footprints: `building`
  - Land use: `landuse`
  - Road orientation entropy: `orientation`
  - Road density: `road_density`
- Vector → raster: `python vec2raster.py`
- Topology / layout graphs: `python extract_topo_layout.py` (uses a modified `sknw` package)
- Topology metrics: `python calculate_network.py`
- Visualization: `python visualization.py`

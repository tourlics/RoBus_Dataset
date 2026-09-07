This folder converts generated road topologies into formats required by **SUMO** and **CARLA** (CSV, OSM, OpenDRIVE, SUMO net/route XML).

## 1. Split topology into numbered roads (CSV)

```
python points2csv.py
```

- Mode 1: resample the topology into points, reconnect, simplify, then split into roads and write CSV.
- Mode 2: split the existing topology into roads and write CSV.
- Outputs: `{scene}_roads.csv` (vertices) and `{scene}_attributes.csv` (road attributes).

## 2. CSV → OSM

- Visualize CSVs as NetworkX: `python csv2nx.py`
- Convert the two CSVs to OSM: `python csv2osm.py`
  - Writes a `.osm` file
  - Writes a projection-string `.txt` used later as `--proj_string`

## 3. OSM → OpenDRIVE and SUMO (Ubuntu)

The CARLA Python egg is resolved via `CARLA_ROOT` (defaults to `~/carla`):

```bash
export CARLA_ROOT=/path/to/carla
```

### One-shot

From `osm2carla/`:

```
python main.py
```

This runs OSM → `.xodr` → SUMO `*.net.xml` + `*.rou.xml`.

### Step by step

- OSM → OpenDRIVE
  - Copy `c_osm_to_xodr.py` into `carla/PythonAPI/utils` if you are using CARLA's tree, then:
  - `python c_osm_to_xodr.py -i roads.osm -o roads.xodr --proj_string "+proj=tmerc +lat_0=30.5006 +lon_0=112.1"`
  - Use the projection string from `csv2osm.py`.
- OpenDRIVE → SUMO net
  - From `carla/Co-Simulation/Sumo/util` (or `osm2carla/Sumo/util`):
  - `python netconvert_carla.py roads.xodr`
  - Output: `net.net.xml`
- SUMO trips
  - `python randomTrips.py -n net.net.xml -r net.rou.xml`

### Example `custom.sumocfg`

```
<?xml version="1.0" encoding="UTF-8"?>
<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/sumoConfiguration.xsd">

  <input>
      <net-file value="net/custom.net.xml"/>
      <route-files value="carlavtypes.rou.xml,rou/custom.rou.xml"/>
  </input>

  <gui_only>
      <gui-settings-file value="viewsettings.xml"/>
  </gui_only>

</configuration>
```

## Appendix: install SUMO on Ubuntu

```
sudo add-apt-repository ppa:sumo/stable
sudo apt-get update
sudo apt-get install sumo sumo-tools sumo-doc
export SUMO_HOME=/usr/share/sumo/
```

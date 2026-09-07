from scripts.osm_parsing import OSM2POI
import os

def parse_poi_from_osm(inputosm, outjsondir):
    poi = OSM2POI()
    poi.get_bus_stops(inputosm, outjsondir)
    return

if __name__ == "__main__":
    osm_dir = r"./data/osm/osm"
    geojson_dir = r"./data/poi/geojson"
    # raster_dir = r"./data/poi/raster"
    os.makedirs(osm_dir, exist_ok=True)
    os.makedirs(geojson_dir,exist_ok=True)
    # os.makedirs(raster_dir,exist_ok=True)

    osmfiles = os.listdir(osm_dir)
    for osmfile in osmfiles:
        if not osmfile.endswith('.osm'): continue
        scene_name = osmfile.split(".")[0]
        print(f"**********processing {osmfile}*************")
        osm_path = os.path.join(osm_dir, osmfile)
        geojson_path = os.path.join(geojson_dir, scene_name)
        # raster_path = os.path.join(raster_dir, scene_name)
        os.makedirs(geojson_path, exist_ok=True)
        # os.makedirs(raster_path, exist_ok=True)
        parse_poi_from_osm(osm_path,geojson_path)

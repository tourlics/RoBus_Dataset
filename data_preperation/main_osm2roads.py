import os
from scripts.osm_parsing import OSM2Roads
from scripts.vec2raster import Vec2Raster
from scripts.tiff_operation import TIFoperation

import numpy as np

def osm2geojson_roads(osm_path, geojson_path, resolution):
    roads = OSM2Roads(resolution)
    # if os.path.exists(os.path.join(geojson_path)): 
    # if len(os.listdir(geojson_path))>0: 
    #     print(f"IGNORE: {osm_path} has been processed to geojson!")
    #     return
    roads.osmnx_geojson_roads(osm_path, geojson_path)

def geojson2raster_roads(geojson_path, raster_path, resolution):
    # if os.path.exists(os.path.join(raster_path)): 
    if len(os.listdir(raster_path)): 
        print(f"IGNORE: {geojson_path} has been processed to tif!")
        return
    
    scene_name = os.path.basename(geojson_path).split(".")[0]
    
    vec2ras = Vec2Raster(resolution)
    
    ### Rasterize p1-level road network
    roads = OSM2Roads(resolution)
    merge_items1 = roads.tag_p1
    merge_buffer_widths1 = roads.p1_pixel_buffer # Road width in pixels for each road-network level
    merge_buffer_widths1 = [item/2 for item in merge_buffer_widths1]
    inpath_vecs1 = []
    mit1 = ''
    for item in merge_items1:
        print(f'rasterizing {item}')
        if not os.path.exists( os.path.join(geojson_path, f"{item}.geojson") ): continue
        inpath_vecs1.append(os.path.join(geojson_path, f"{item}.geojson"))
        mit1 += item[0]
    vec2ras.geojson2tiff_epsg(inpath_vecs1, os.path.join(raster_path,f"{scene_name}_p1.tiff"), merge_buffer_widths1, afterCoordSystem="epsg:3857")

    ### Rasterize p2-level road network
    merge_items2 = roads.tag_p2
    merge_buffer_widths2 = roads.p2_pixel_buffer # Road width in pixels for each road-network level
    merge_buffer_widths2 = [item/2 for item in merge_buffer_widths2]
    inpath_vecs2 = []
    mit2 = ''
    for item in merge_items2:
        print(f'rasterizing {item}')
        if not os.path.exists( os.path.join(geojson_path, f"{item}.geojson") ): continue
        inpath_vecs2.append(os.path.join(geojson_path, f"{item}.geojson"))
        mit2 += item[0]
    vec2ras.geojson2tiff_epsg(inpath_vecs2, os.path.join(raster_path,f"{scene_name}_p2.tiff"), merge_buffer_widths2, afterCoordSystem="epsg:3857")


def rename_osm(origin_osm_dir, osm_dir):
    import shutil
    osmfiles = os.listdir(origin_osm_dir)
    for osmfile in osmfiles:
        scene_name = parse_osm_scene_name(osmfile)
        if os.path.exists(os.path.join(osm_dir, f"{scene_name}.osm")): continue
        shutil.copy(os.path.join(origin_osm_dir, osmfile), os.path.join(osm_dir, f"{scene_name}.osm"))

def parse_osm_scene_name(inputfile):
    filename = os.path.basename(inputfile)
    assert filename.split(".")[-1] == "osm"
    return filename.split("_")[0]

def align_union_two_tiff_roads(raster_path, raster_align_path):
    scene_name = os.path.basename(raster_path).split(".")[0]
    tiff1_path = os.path.join(raster_path, f"{scene_name}_p1.tiff")
    tiff2_path = os.path.join(raster_path, f"{scene_name}_p2.tiff")
    tifoper = TIFoperation()
    tifoper.align_two_tif(tiff1_path, tiff2_path, raster_align_path)

    tiff1_align_path = os.path.join(raster_align_path, f"{scene_name}_p1.tiff")
    tiff2_align_path = os.path.join(raster_align_path, f"{scene_name}_p2.tiff")
    union_tiff_path = os.path.join(raster_align_path, f"{scene_name}.tiff")
    tifoper.union_two_tif(tiff1_align_path, tiff2_align_path, union_tiff_path)

if __name__ == "__main__":

    resolution = 5
    dataspace = r"./dataset_roads/China_5m"

    origin_osm_dir = os.path.join(dataspace, r"osm\origin_osm")
    osm_dir = os.path.join(dataspace, r"osm\osm")
    geojson_dir = os.path.join(dataspace, r"roads\geojson")
    raster_dir = os.path.join(dataspace, r"roads\raster")
    raster_align_dir = os.path.join(dataspace, r"roads\raster_align")
    os.makedirs(osm_dir, exist_ok=True)
    os.makedirs(geojson_dir,exist_ok=True)
    os.makedirs(raster_dir,exist_ok=True)
    os.makedirs(raster_align_dir, exist_ok=True)

    # rename_osm(origin_osm_dir, osm_dir)

    osmfiles = os.listdir(osm_dir)
    for osmfile in osmfiles:
        if not osmfile.endswith('.osm'): continue
        scene_name = osmfile.split(".")[0]
        print(f"**********processing {osmfile}*************")
        osm_path = os.path.join(osm_dir, osmfile)
        geojson_path = os.path.join(geojson_dir, scene_name)
        raster_path = os.path.join(raster_dir, scene_name)
        raster_align_path = os.path.join(raster_align_dir, scene_name)
        os.makedirs(geojson_path, exist_ok=True)
        os.makedirs(raster_path, exist_ok=True)
        os.makedirs(raster_align_path, exist_ok=True)
        # osm2geojson_roads(osm_path, geojson_path, resolution)
        geojson2raster_roads(geojson_path, raster_path, resolution)
        align_union_two_tiff_roads(raster_path, raster_align_path)
    

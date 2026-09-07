from scripts.osm_parsing import OSM2Buildings
from scripts.tiff_operation import TIFoperation
import os
import rasterio
import geopandas as gpd  
import pandas as pd
from shapely.geometry import box
import numpy as np  
from shapely.geometry import Polygon, mapping  
from rasterio.features import rasterize  
from rasterio.mask import mask  
from tqdm import tqdm  
import multiprocessing
from shapely.geometry import shape
from scripts.vec2raster import Vec2Raster, CRStrans
import shutil

#################### Processing pipeline for overseas data #############################
def downloading_from_ms(ms_csv_path, location, outdir):
    print("downloading...")
    if not os.path.exists(ms_csv_path):
        ms_csv_path = "https://minedbuildings.blob.core.windows.net/global-buildings/dataset-links.csv"
    dataset_links = pd.read_csv(ms_csv_path)
    greece_links = dataset_links[dataset_links.Location == location]
    for _, row in greece_links.iterrows():
        outpath = os.path.join(outdir, f"{row.QuadKey}.geojson")
        if os.path.exists(outpath): continue
        df = pd.read_json(row.Url, lines=True)
        df['geometry'] = df['geometry'].apply(shape)
        gdf = gpd.GeoDataFrame(df, crs=4326)
        gdf.to_file(outpath, driver="GeoJSON")
    print(f"saved in {outdir}")

def rename_ms_geojson(location):
    building_ms_geojson_dir = os.path.join(r"./dataset_roads/ORG_Microsoft_building_geojson", location)
    building_ms_geojson_dir_pos = os.path.join(r"./dataset_roads/ORG_Microsoft_building_geojson", f"{location}_pos")
    os.makedirs(building_ms_geojson_dir_pos, exist_ok=True)
    files = os.listdir(building_ms_geojson_dir)
    existed_files = os.listdir(building_ms_geojson_dir_pos)
    existed_files_scenes = [scene.split("_")[0] for scene in existed_files]
    for file in tqdm(files):
        if file.split(".")[0] in existed_files_scenes: continue
        gdf = gpd.read_file(os.path.join(building_ms_geojson_dir, file))
        left, bottom, right, top = gdf.total_bounds
        newfilename = file.split(".")[0]+f"_{left}_{bottom}_{right}_{top}."+file.split(".")[1]
        shutil.copy(os.path.join(building_ms_geojson_dir, file), os.path.join(building_ms_geojson_dir_pos, newfilename))


def check_in_poly_fast(geojsonfile, crop_poly):
    file_bounds = os.path.basename(geojsonfile)[:-8].split("_")[1:]
    bounds_list = tuple(map(float, file_bounds))
    left, bottom, right, top = bounds_list
    gdf_box = box(minx=left, miny=bottom, maxx=right, maxy=top)
    if gdf_box.intersects(crop_poly):
        return True
    else:
        return False

# For overseas data, extract building polygons within the reftiff extent from Microsoft country-level GeoJSON
def get_building_from_ms(reftiff, msgeojsondir, outgeojson):
    with rasterio.open(reftiff) as ds:
        selected_polygons = []
        left, bottom, right, top = ds.bounds
        geoms = [box(minx=left, miny=bottom, maxx=right, maxy=top)]
        crstrans = CRStrans()
        crop_poly = crstrans.transhapely(geoms, src_crs=ds.crs, dst_crs="EPSG:4326")

    cur_geojsonfiles = os.listdir(msgeojsondir)
    out_geoms = {"geometry":[], "height":[]}
    for geojsonfile in tqdm(cur_geojsonfiles):
        if not check_in_poly_fast(geojsonfile, crop_poly): continue
        gdf = gpd.read_file(os.path.join(msgeojsondir, geojsonfile)) 
        cur_polygons = gdf[gdf.intersects(crop_poly)] 
        if len(cur_polygons) > 0:
            for index, row in tqdm(cur_polygons.iterrows()):
                height = row["properties"]["height"]
                if (height is None) or (float(height) <= 0): 
                    height = 24
                geo = row["geometry"]
                out_geoms["geometry"].append(geo)
                out_geoms["height"].append(height)
    gpdpolys = gpd.GeoDataFrame(out_geoms, crs="EPSG:4326")
    gpdpolys.to_file(outgeojson, driver='GeoJSON')  

def main_Europe():
    building_ms_geojson_dir = r"./dataset_roads/ORG_Microsoft_building_geojson"
    ms_csv_path = os.path.join(building_ms_geojson_dir, "dataset-links.csv")

    dataspace = r"./dataset_roads/Europe"
    building_geojson_dir = os.path.join(dataspace, r"buildings\geojson")
    building_raster_dir = os.path.join(dataspace, r"buildings\raster")
    ref_tiff_dir = os.path.join(dataspace, r"roads\raster_align")
    os.makedirs(building_geojson_dir,exist_ok=True)
    os.makedirs(building_raster_dir,exist_ok=True)

    osm_dir = os.path.join(dataspace, r"osm\origin_osm")
    osmfiles = os.listdir(osm_dir)
    for osmfile in osmfiles:
        scene_name = osmfile.split("_")[0]
        country_name = osmfile.split("_")[1]
        location = country_name
        save_path = os.path.join(building_ms_geojson_dir, f"{location}_pos")
        os.makedirs(save_path, exist_ok=True)
        os.makedirs(os.path.join(building_raster_dir, scene_name), exist_ok=True)
        os.makedirs(os.path.join(building_geojson_dir, scene_name), exist_ok=True)
        building_raster_hgt_path = os.path.join(building_raster_dir, scene_name, f"{scene_name}_building_hgt_final.tiff")
        # if os.path.exists(building_raster_hgt_path): 
        #     print("IGNORE ", scene_name)
        #     continue
        # downloading_from_ms(ms_csv_path, location=location, outdir=save_path)

        tifffile = os.path.join(ref_tiff_dir,scene_name, f"{scene_name}.tiff")
        print(f"**********processing {scene_name}*************")
        get_building_from_ms(os.path.join(ref_tiff_dir,tifffile), save_path, \
                             os.path.join(building_geojson_dir, scene_name, f"{scene_name}_building_hgt.geojson"))
        building_finaljson_path = os.path.join(building_geojson_dir, scene_name, f"{scene_name}_building_hgt.geojson")
        building_raster_hgt_path = os.path.join(building_raster_dir, scene_name, f"{scene_name}_building_hgt_final.tiff")
        resolution = 5
        vec2ras = Vec2Raster(resolution)
        vec2ras.geojson2tiff_epsg([building_finaljson_path], building_raster_hgt_path, buffer_widths=0, afterCoordSystem="epsg:3857", fill_attr="height")


def main_US_Australia(location):
    building_ms_geojson_dir = r"./dataset_roads/ORG_Microsoft_building_geojson"
    ms_csv_path = os.path.join(building_ms_geojson_dir, "dataset-links.csv")
    save_path = os.path.join(building_ms_geojson_dir, f"{location}_pos")
    os.makedirs(save_path, exist_ok=True)
    # downloading_from_ms(ms_csv_path, location=location, outdir=save_path)

    dataspace = os.path.join(r"./dataset_roads", location)
    building_geojson_dir = os.path.join(dataspace, r"buildings\geojson")
    building_raster_dir = os.path.join(dataspace, r"buildings\raster")
    ref_tiff_dir = os.path.join(dataspace, r"roads\raster_align")

    os.makedirs(building_geojson_dir,exist_ok=True)
    os.makedirs(building_raster_dir,exist_ok=True)

    tiffdirs = os.listdir(ref_tiff_dir)
    for scene_name in tiffdirs:
        print(f"**********processing {scene_name}*************")
        os.makedirs(os.path.join(building_geojson_dir, scene_name),exist_ok=True)
        os.makedirs(os.path.join(building_raster_dir, scene_name), exist_ok=True)

        building_finaljson_path = os.path.join(building_geojson_dir, scene_name, f"{scene_name}_building_hgt.geojson")
        building_raster_hgt_path = os.path.join(building_raster_dir, scene_name, f"{scene_name}_building_hgt_final.tiff")
        if not os.path.exists(building_finaljson_path): 
            get_building_from_ms(os.path.join(ref_tiff_dir,scene_name, f"{scene_name}.tiff"), save_path, \
                             os.path.join(building_geojson_dir, scene_name, f"{scene_name}_building_hgt.geojson"))
        elif not os.path.exists(building_raster_hgt_path):
            resolution = 5
            vec2ras = Vec2Raster(resolution)
            vec2ras.geojson2tiff_epsg([building_finaljson_path], building_raster_hgt_path, buffer_widths=0, afterCoordSystem="epsg:3857", fill_attr="height")
        else:
            print("IGNORE", scene_name)

if __name__ == "__main__":
    # location_list = ["UnitedKingdom", "Spain", "Belgium", "France", "Germany", "Italy", "Luxembourg", "Netherlands"]
    # for location in location_list:
    #     rename_ms_geojson(location=location) # 
    location = "Australia" # "Australia", "UnitedStates"
    main_US_Australia(location)
    # main_Europe()

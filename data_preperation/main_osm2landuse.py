from scripts.osm_parsing import OSM2Landuse
from scripts.vec2raster import Vec2Raster
from scripts.tiff_operation import TIFoperation, CRStrans
import os
import geopandas as gpd
from shapely.geometry import Polygon, mapping , box
import rasterio

def parse_landuse_from_osm(inputosm, outjsondir, outrasterdir, additional_water_file=None):
    landuse = OSM2Landuse()
    # landuse.extract_landuse_tags(inputosm, outjsondir)
    all_waters = landuse.all_waters
    all_woods = landuse.all_woods

    scene_name = os.path.basename(inputosm).split(".")[0]

    vec2ras = Vec2Raster(resolution)
    inpath_vecs1 = []
    for item in all_waters:
        print(f'rasterizing {item}')
        if not os.path.exists( os.path.join(outjsondir, f"{item}.geojson") ): continue
        inpath_vecs1.append(os.path.join(outjsondir, f"{item}.geojson"))
    
    if additional_water_file is not None:
        inpath_vecs1.append(os.path.join(outjsondir, f"additional.geojson"))

    watertif = vec2ras.geojson2tiff_epsg(inpath_vecs1, os.path.join(outrasterdir,f"{scene_name}_waters.tif"), [1]*len(inpath_vecs1), afterCoordSystem="epsg:3857")

    inpath_vecs2 = []
    for item in all_woods:
        print(f'rasterizing {item}')
        if not os.path.exists( os.path.join(outjsondir, f"{item}.geojson") ): continue
        inpath_vecs2.append(os.path.join(outjsondir, f"{item}.geojson"))
    woodtif = vec2ras.geojson2tiff_epsg(inpath_vecs2, os.path.join(outrasterdir,f"{scene_name}_woods.tif"), [1]*len(inpath_vecs2), afterCoordSystem="epsg:3857")

    return woodtif and watertif

def align_two_landuse_tiff(raster_path, raster_align_path):
    scene_name = os.path.basename(raster_path).split(".")[0]
    tiff1_path = os.path.join(raster_path, f"{scene_name}_waters.tif")
    tiff2_path = os.path.join(raster_path, f"{scene_name}_woods.tif")
    tifoper = TIFoperation()
    tifoper.align_two_tif(tiff1_path, tiff2_path, raster_align_path)


def get_waters_from_location_shp(clip_box:box, outputpath, water_shp_dir = r"./dataset_roads/ORG_waters_China"):
    data = gpd.read_file(water_shp_dir)
    # Convert the clip boundary to a GeoDataFrame  
    clip_gdf = gpd.GeoDataFrame({'geometry': [clip_box], 'crs':'EGSP:4326'})  
    # Clip using clip_gdf  
    cropped_gdf = gpd.overlay(data, clip_gdf, how='intersection') 
    cropped_gdf.to_file(outputpath, driver='GeoJSON')
    return 



if __name__ == "__main__":

    resolution = 5
    dataspace = r"./dataset_roads/Europe"

    osm_dir = os.path.join(dataspace, r"osm\osm")
    geojson_dir = os.path.join(dataspace, r"landuse\geojson")
    raster_dir =  os.path.join(dataspace, r"landuse\raster")
    raster_align_dir = os.path.join(dataspace, r"landuse\raster_align")

    ref_tif_dir = os.path.join(dataspace, r"roads\raster_align")

    os.makedirs(osm_dir, exist_ok=True)
    os.makedirs(geojson_dir,exist_ok=True)
    os.makedirs(raster_dir,exist_ok=True)
    os.makedirs(raster_align_dir, exist_ok=True)

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

        with rasterio.open(os.path.join(ref_tif_dir, scene_name, f"{scene_name}.tiff")) as ref:
            left, bottom, right, top = ref.bounds
            geoms = [box(minx=left, miny=bottom, maxx=right, maxy=top)]
            crstrans = CRStrans()
            crop_box = crstrans.transhapely(geoms, src_crs=ref.crs, dst_crs="EPSG:4326")
        # if not os.path.exists(os.path.join(geojson_path, "additional.geojson")):
        #     get_waters_from_location_shp(crop_box, os.path.join(geojson_path, "additional.geojson"))

        if parse_landuse_from_osm(osm_path, geojson_path, raster_path, additional_water_file=None):
            align_two_landuse_tiff(raster_path, raster_align_path)
    
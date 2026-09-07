from scripts.osm_parsing import OSM2Buildings
from scripts.tiff_operation import TIFoperation, CRStrans
from scripts.vec2raster import Vec2Raster
import os
import rasterio
import geopandas as gpd  
from shapely.geometry import box
import numpy as np  
from shapely.geometry import Polygon, mapping  
from rasterio.features import rasterize  
from rasterio.mask import mask  
from tqdm import tqdm  
import multiprocessing

############################ Processing pipeline for China-region data ###################################
# # For China-region data, reproject the 10m-resolution height dataset, then add height
# def transfer_crs(inputtif_dir, outputtif_dir, dstcrs):
#     tifopr = TIFoperation()
#     for inputtiff in tqdm(os.listdir(inputtif_dir)):
#         if inputtiff.endswith('.tiff') or inputtiff.endswith('.tif'): 
#             outputtiff = os.path.join(outputtif_dir, inputtiff)
#             tifopr.tiff_crs_trans(os.path.join(inputtif_dir,inputtiff), outputtiff, dst_crs=dstcrs)

# For China-region data, extract OSM attributes and fuse OSM height/levels with a 10m-resolution height dataset
def compute_avg_surrounding_pixels(polygon, src, buffer_distance):
    polygon = polygon.buffer(buffer_distance)
    try:  
        out_image, out_transform = mask(src, [polygon], crop=True)  
        data_array = out_image[0]  
        # Find indices of valid (non-zero) pixels  
        valid_pixels = data_array > 0  
        # print(len(valid_pixels))
        # Return 0 if there are no valid pixels  
        if not np.any(valid_pixels):  
            return 0  
        # Compute the mean of valid pixels  
        avg_value = np.mean(data_array[valid_pixels])  
    except:
        return 0
    return avg_value  
  
# Prefer OSM height; else TIF mean; else neighborhood mean; else assign 20m
def estimate_hgt_from_tif(outgeojson, hgttif, finaljson):  
    gdf = gpd.read_file(outgeojson)   
    print(f"total of {len(gdf)} items...")
    with rasterio.open(hgttif) as src:  
        new_rows = []
        for index, row in tqdm(gdf.iterrows()):  
            polygon = row['geometry']  
            if type(polygon) is not Polygon: continue
            # Check for height or levels fields
            if row.get('height') is not None:
                try:
                    new_height = float(row.get('height'))
                except:
                    new_height = 0
            elif row.get('building:levels') is not None:  
                try: 
                    new_height = float(row.get('building:levels')) * 3 + 2 
                except:
                    new_height = 0
            else:  
                avg_value = compute_avg_surrounding_pixels(polygon, src, buffer_distance=0)
                if avg_value <= 0:  
                    # If the mean is 0, average the surrounding 100 pixels  
                    avg_value = compute_avg_surrounding_pixels(polygon, src, buffer_distance=100) 
                    if avg_value <= 0:  
                        # If still 0, assign 24  
                        avg_value = 24  
                new_height = avg_value   
            new_row = {} 
            new_row['osmid'] = row.get('osmid')
            new_row['height'] = str(new_height) 
            new_row['geometry'] = polygon
            new_rows.append(new_row)  
        new_gdf = gpd.GeoDataFrame(new_rows)
        new_gdf.crs = gdf.crs 
        new_gdf.to_file(finaljson, driver='GeoJSON')  

# def worker_hgt(row, hgttif):
#     polygon = row['geometry']  
#     # Check for height or levels fields
#     if row.get('height') is not None:
#         new_height = float(row.get('height'))
#     elif row.get('building:levels') is not None:   
#         new_height = float(row.get('building:levels')) * 3 + 2 
#     else:  
#         with rasterio.open(hgttif) as src:
#             avg_value = compute_avg_surrounding_pixels(polygon, src, buffer_distance=0)
#             if avg_value == 0:  
#                 # If the mean is 0, average the surrounding 30 pixels  
#                 avg_value = compute_avg_surrounding_pixels(polygon, src, buffer_distance=30) 
#                 if avg_value == 0:  
#                     # If still 0, assign 24  
#                     avg_value = 24  
#             new_height = avg_value   
#     new_row = {} 
#     new_row['osmid'] = row.get('osmid')
#     new_row['height'] = str(new_height) 
#     new_row['geometry'] = polygon
#     return new_row

# def estimate_hgt_from_tif_multiprocess(outgeojson, hgttif, finaljson):  
#     gdf = gpd.read_file(outgeojson)
#     print(f"total {len(gdf)} items...")
#     with multiprocessing.Pool(processes=16) as pool:  
#         new_rows = pool.starmap(worker_hgt, [(row, hgttif) for index, row in gdf.iterrows()])
#     new_gdf = gpd.GeoDataFrame(crs=gdf.crs)
#     new_gdf.append(new_rows, ignore_index=True)    
#     new_gdf.to_file(finaljson, driver='GeoJSON') 

# # Prefer OSM height; else TIF mean; else neighborhood mean; else assign 20m
# def estimate_hgt_from_tif(outgeojson, hgttif, finaljson):
#     gdf = gpd.read_file(outgeojson)
#     geometry = gdf['geometry']
#     for geo in geometry:

#     with rasterio.open(hgttif) as src:  
#         data = src.read(1) 

def get_crop_boundary_from_tiff(reftiff):
    with rasterio.open(reftiff) as ds:
        left, bottom, right, top = ds.bounds
        geoms = [Polygon(((left, top), (right, top), (right, bottom), (left, bottom)))]
    crstrans = CRStrans()
    crop_poly = crstrans.transhapely(geoms, src_crs=ds.crs, dst_crs="EPSG:4326")
    return crop_poly

def select_tiff_items(CN10_building_dir, crop_poly):    
    crop_poly = Polygon(crop_poly)
    # Collect filenames contained by the polygon  
    included_files = []  
    # Iterate over all files in the folder  
    for filename in os.listdir(CN10_building_dir):  
        if filename.startswith("CNBH") and (filename.endswith('.tiff') or filename.endswith('.tif')):   
            xy_str = filename.split('.')[0].split('_')[1] 
            x = float(xy_str.split("Y")[0][1:])  
            y = float(xy_str.split("Y")[1][0:]) 
            
            tifpoly = Polygon([(x-1,y-1), (x+1,y-1),(x+1,y+1), (x-1,y+1)])
            # Check whether the lon/lat in the filename lies inside the polygon  
            if tifpoly.intersection(crop_poly):
                included_files.append(os.path.join(CN10_building_dir, filename)) 
    return included_files

def crop_and_trans_hgt_tiff(tiff_files, crop_poly, hgtrawtiff_path, hgttiff_path):
    print(tiff_files, crop_poly)
    tiff_file = tiff_files[0]

    tifopr = TIFoperation()

    if len(tiff_files) > 1:
        output_file = tiff_files[0].replace(os.path.basename(tiff_files[0]), f"concated_{os.path.basename(tiff_files[0])}")
        tifopr.concate_tiffs(tiff_files, output_file)
        tiff_file = output_file
        
    tifopr.crop_tiff_from_boundary(tiff_file, [crop_poly], hgtrawtiff_path)
    tifopr.tiff_crs_trans(hgtrawtiff_path, hgttiff_path, dst_crs="EPSG:4326")


if __name__ == "__main__":
    dataspace = r"./dataset_roads/China_5m"
    osm_dir = os.path.join(dataspace, r"osm\osm")
    building_geojson_dir = os.path.join(dataspace, r"buildings\geojson")
    building_raster_dir = os.path.join(dataspace, r"buildings\raster")

    CN10_building_dir = r"./data/ORG_China_building_hgt_10m"
    
    ## Too large and too slow; discarded
    # CN10_building_dir = r"./data/China_building_hgt_e4326"
    ## os.makedirs(CN10_building_dir, exist_ok=True)
    ## transfer_crs_dir(CN10_building_dir_org, CN10_building_dir, dstcrs="EPSG:4326")

    ref_tiff_dir = os.path.join(dataspace, r"roads\raster_align")

    os.makedirs(building_geojson_dir,exist_ok=True)
    os.makedirs(building_raster_dir,exist_ok=True)

    osmfiles = os.listdir(osm_dir)
    for osmfile in osmfiles:
        ### Extract OSM buildings as GeoJSON
        if not osmfile.endswith('.osm'): continue
        scene_name = osmfile.split(".")[0]
        print(f"**********processing {osmfile}*************")
        osm_path = os.path.join(osm_dir, osmfile)
        building_geojson_path = os.path.join(building_geojson_dir, scene_name, f"{scene_name}_building.geojson")
        os.makedirs(os.path.join(building_geojson_dir, scene_name), exist_ok=True)
        building_raster_path = os.path.join(building_raster_dir, scene_name)

        # Skip if all tasks are already done
        building_raster_hgt_path = os.path.join(building_raster_dir, scene_name, f"{scene_name}_building_hgt_final.tiff")
        if os.path.exists(building_raster_hgt_path):
            continue
        os.makedirs(os.path.join(building_raster_dir, scene_name), exist_ok=True)
        # buildings = OSM2Buildings()
        # buildings.extract_contours(osm_path, building_geojson_path)
        # print("building contours extracted from osm") 

        # # Get bounds from the road-network TIFF
        # ref_tiff_path = os.path.join(ref_tiff_dir, scene_name, f"{scene_name}.tiff")
        # crop_poly_judge = get_crop_boundary_from_tiff(ref_tiff_path)
        # # print(crop_poly_judge)
        # # Select matching tiles from the open-source dataset
        # slt_paths = select_tiff_items(CN10_building_dir, crop_poly_judge)

        # with rasterio.open(slt_paths[0]) as ref:
        #     dstcrs = ref.crs
        # crstrans = CRStrans()
        # crop_poly = crstrans.transhapely(crop_poly_judge, src_crs="EPSG:4326", dst_crs=dstcrs)
        # hgtrawtiff_path = os.path.join(building_raster_dir, scene_name, f"{scene_name}_hgtraw.tiff")
        # hgttiff_path = os.path.join(building_raster_dir, scene_name, f"{scene_name}_hgt.tiff")
        # # Mosaic and crop the corresponding height map
        # crop_and_trans_hgt_tiff(slt_paths, crop_poly, hgtrawtiff_path, hgttiff_path)
        # print("hgt tiff cropped and transferred to rpsg 4326") 
        # # Estimate height of each building footprint and write to GeoJSON
        building_finaljson_path = os.path.join(building_geojson_dir, scene_name, f"{scene_name}_building_hgt.geojson")
        # estimate_hgt_from_tif(building_geojson_path, hgttif=hgttiff_path, finaljson=building_finaljson_path)
        # print("hgt geojson saved")

        building_raster_hgt_path = os.path.join(building_raster_dir, scene_name, f"{scene_name}_building_hgt_final.tiff")
        resolution = 5
        vec2ras = Vec2Raster(resolution)
        vec2ras.geojson2tiff_epsg([building_finaljson_path], building_raster_hgt_path, buffer_widths=0, afterCoordSystem="epsg:3857", fill_attr="height")



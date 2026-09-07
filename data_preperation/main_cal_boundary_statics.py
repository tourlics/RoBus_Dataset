import rasterio
import numpy as np
import os
import json
from tqdm import tqdm
from shapely.geometry import Polygon
from scripts.vec2raster import CRStrans
import geopandas as gpd
import glob  
from scripts.visualization import vis_pie_from_npy_for_cls, vis_stacked_bins_from_npy_clamp

# Compute boundary area and per-boundary building count
def cal_block_buildings_boundary(jsonpath, outjsonpath):
    # Boundary count, size, building count, mean building height, and building coverage
    boundary_size_list = [] # Boundary size
    boundary_building_cnt_list = [] # Building count inside the boundary
    boundary_building_hgt_list = [] # Mean building height inside the boundary
    boundary_building_area_list = [] # Total building area inside the boundary
    with open(jsonpath) as f:
        json_data_list = json.load(f)
    for boundary in tqdm(json_data_list):
        boundary_coordinates = boundary["boundary_coordinates"]  
        boundary_size = Polygon(boundary_coordinates).area
        boundary_size_list.append(boundary_size)

        buildings_list = boundary["buildings"]
        boundary_building_cnt_list.append(len(buildings_list))

        b_hgt_in_boundary = []
        b_area_in_boundary = []
        for building in buildings_list:
            building_coordinates = building["coordinates"]
            b_area_in_boundary.append(Polygon(building_coordinates).area)
            b_hgt_in_boundary.append(float(building["height"]))
        boundary_building_hgt_list.append(np.mean(b_hgt_in_boundary))
        boundary_building_area_list.append(np.sum(b_area_in_boundary))

    assert len(boundary_size_list) == len(boundary_building_cnt_list) == len(boundary_building_hgt_list) == len(boundary_building_area_list)

    outjson_list = []
    for idx in range(len(boundary_size_list)):
        cur_json = {
            "boundary_size": boundary_size_list[idx],
            "building_cnt": boundary_building_cnt_list[idx],
            "avg_hgt": boundary_building_hgt_list[idx],
            "bouilding_area": boundary_building_area_list[idx]
        }
        outjson_list.append(cur_json)
    with open(outjsonpath, "w") as fo:
        json.dump(outjson_list, fo)

def cal_block_buildings_boundary_multi_files(jsondir, outjsonpath):
    # Boundary count, size, building count, mean building height, and building coverage
    boundary_size_list = [] # Boundary size
    boundary_building_cnt_list = [] # Building count inside the boundary
    boundary_building_hgt_list = [] # Mean building height inside the boundary
    boundary_building_area_list = [] # Total building area inside the boundary
    for jsonpath in os.listdir(jsondir):
        with open(os.path.join(jsondir,jsonpath)) as f:
            json_data_list = json.load(f)
        for boundary in tqdm(json_data_list):
            boundary_coordinates = boundary["boundary_coordinates"]  
            boundary_size = Polygon(boundary_coordinates).area
            boundary_size_list.append(boundary_size)

            buildings_list = boundary["buildings"]
            boundary_building_cnt_list.append(len(buildings_list))

            b_hgt_in_boundary = []
            b_area_in_boundary = []
            for building in buildings_list:
                building_coordinates = building["coordinates"]
                b_area_in_boundary.append(Polygon(building_coordinates).area)
                b_hgt_in_boundary.append(float(building["height"]))
            boundary_building_hgt_list.append(np.mean(b_hgt_in_boundary))
            boundary_building_area_list.append(np.sum(b_area_in_boundary))

        assert len(boundary_size_list) == len(boundary_building_cnt_list) == len(boundary_building_hgt_list) == len(boundary_building_area_list)

        outjson_list = []
        for idx in range(len(boundary_size_list)):
            cur_json = {
                "boundary_size": boundary_size_list[idx],
                "building_cnt": boundary_building_cnt_list[idx],
                "avg_hgt": boundary_building_hgt_list[idx],
                "bouilding_area": boundary_building_area_list[idx]
            }
            outjson_list.append(cur_json)
    with open(outjsonpath, "w") as fo:
        json.dump(outjson_list, fo)


def trans_json2npy_boundary(json_path, npy_path):
    with open(json_path,'r') as file:
        data_list = json.load(file)
    
    boundary_size_list = []
    building_cnt_list = []
    avg_height_list = []
    building_area_list = []
    building_density_list = []

    for data in data_list:
        
        boundary_size_list.append(data["boundary_size"])
        building_cnt_list.append(data["building_cnt"])
        avg_height_list.append(data["avg_hgt"])
        building_area_list.append(data["bouilding_area"])
        building_density_list.append(data["bouilding_area"]/data["boundary_size"])
    
    dict_npy = {"boundary_size": np.asarray(boundary_size_list),
                "building_cnt": np.asarray(building_cnt_list),
                "building_height": np.asarray(avg_height_list),
                "b_area": np.asarray(building_area_list),
                "building_density": np.asarray(building_density_list)}
    np.save(npy_path, dict_npy)

def merge_json_files(json_dir):
    json_files = glob.glob(os.path.join(json_dir, '*.json'))   
    merged_list = []   
    for json_file in json_files:  
        with open(json_file, 'r') as file:  
            file_list = json.load(file)   
            merged_list.extend(file_list)   
    output_file = os.path.join(json_dir, 'block_total.json')
    with open(output_file, 'w') as file:  
        json.dump(merged_list, file, indent=4)  # indent=4 formats the output for readability  
    
if __name__ == "__main__":
    # dataspace = r"./dataset_roads/UnitedStates"
    # boundary_building_json_dir = os.path.join(dataspace, r"urban_block_building\geojson")
    # merged_json_path = os.path.join(boundary_building_json_dir, r"block_total.json")
    # boundary_statics_path = os.path.join(dataspace, r"urban_block_building\boundary_statics.json")
    # # merge_json_files(boundary_building_json_dir)
    # # cal_block_buildings_boundary(merged_json_path, boundary_statics_path)
    # cal_block_buildings_boundary_multi_files(boundary_building_json_dir, boundary_statics_path)
    
    dataspace1 = r"./dataset_roads"
    dataspace2 = r"./dataset_roads"
    tile_statics_save_path1 = os.path.join(dataspace1, "UnitedStates","urban_block_building","boundary_statics.json")
    tile_statics_save_path2 = os.path.join(dataspace1, "China_5m" ,"urban_block_building", "boundary_statics.json")
    tile_statics_save_path3 = os.path.join(dataspace2, "Australia","urban_block_building", "boundary_statics.json")
    tile_statics_save_path4 = os.path.join(dataspace2, "Europe", "urban_block_building","boundary_statics.json")
    
    npy_path1 = os.path.join(dataspace1, "UnitedStates","urban_block_building","boundary_statics.npy")
    npy_path2 = os.path.join(dataspace1,"China_5m" ,"urban_block_building","boundary_statics.npy")
    npy_path3 = os.path.join(dataspace2, "Australia","urban_block_building","boundary_statics.npy")
    npy_path4 = os.path.join(dataspace2, "Europe","urban_block_building","boundary_statics.npy")
    
    trans_json2npy_boundary(tile_statics_save_path1, npy_path1)
    trans_json2npy_boundary(tile_statics_save_path2, npy_path2)
    trans_json2npy_boundary(tile_statics_save_path3, npy_path3)
    trans_json2npy_boundary(tile_statics_save_path4, npy_path4)
    
    # vis_stacked_bins_from_npy_clamp([npy_path1, npy_path2, npy_path3, npy_path4], "building_density", "Building Density", distance=0.02, clamp_range=[0, 0.5])
    # vis_stacked_bins_from_npy_clamp([npy_path1, npy_path2, npy_path3, npy_path4], "building_height", "Building Height", distance=3, clamp_range=[0, 120])
    vis_stacked_bins_from_npy_clamp([npy_path1, npy_path2, npy_path3, npy_path4], "building_cnt", "boundary_size", distance=2, clamp_range=[6, 100])
    # vis_pie_from_npy_for_cls([npy_path1, npy_path2, npy_path3, npy_path4])

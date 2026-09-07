from scripts.osm_parsing import OSM2density
from scripts.tiff_operation import TIFoperation
import os
import numpy as np
from tqdm import tqdm
import rasterio
from scipy.ndimage import gaussian_filter

# def generate_road_density_from_large():
#     geojson_dir = r"./dataset_roads/demo/roads/geojson"
#     raster_dir = r"./dataset_roads/demo/roads/raster_align"
#     density_dir = r"./dataset_roads/demo/roads/density"

#     geofiles = os.listdir(geojson_dir)
#     for scene_name in geofiles:
#         print(f"**********processing {scene_name}*************")
#         geojson_path = os.path.join(geojson_dir, scene_name)
#         raster_path = os.path.join(raster_dir, scene_name)
#         density_path = os.path.join(density_dir, scene_name)
#         os.makedirs(density_path, exist_ok=True)
#         geojsonfiles = os.listdir(geojson_path)
#         geojsonlist = [os.path.join(geojson_path, geojsonfile) for geojsonfile in geojsonfiles]

#         tifopr = TIFoperation()
#         tifopr.resize_tiff(os.path.join(raster_path, f"{scene_name}.tiff"), \
#                            os.path.join(density_path, f"{scene_name}_ref.tiff"), scale_factor=4)

#         reftiff = os.path.join(density_path, f"{scene_name}_ref.tiff")
#         densityfile = os.path.join(density_path, f"{scene_name}_density.tiff")
#         density = OSM2density()
#         heatmap = density.cal_geojson_to_density_map(geojsonlist, reftiff, densityfile, sigma=50)

def generate_road_density_from_small():
    dataspace = r"./dataset_roads/China"

    geojson_dir = os.path.join(dataspace, r"roads\geojson")
    image_dir = os.path.join(dataspace, "cropped_images")
    image_files = os.listdir(image_dir)
    for image_file in tqdm(image_files):
        if not image_file.endswith(".tif"): continue
        print(image_file)
        scene_name = image_file.split("_")[0]

        geojson_path = os.path.join(geojson_dir, scene_name)
        geojsonfiles = os.listdir(geojson_path)
        geojsonlist = [os.path.join(geojson_path, geojsonfile) for geojsonfile in geojsonfiles]
        density = OSM2density()
        # Strict road-network density formula is still too slow
        # heatmap = density.cal_geojson_to_density_map(geojsonlist, os.path.join(image_dir,image_file), outputfile=None, sigma=100, issave=False)
        heatmap = density.estimate_density_map(os.path.join(image_dir,image_file), sigma=300)
        heatmap = heatmap.reshape(1, heatmap.shape[0], heatmap.shape[1]).astype('float32')
        with rasterio.open(os.path.join(image_dir,image_file)) as src:  
            meta = src.meta  
            data = src.read().astype('float32')
            src.close()
        new_channel = np.random.rand(meta['height'], meta['width'])  
        data_with_new_channel = np.vstack((data, heatmap))  
        meta.update(count=meta['count'] + 1)  # Assume meta['count'] is the original channel count  
        # Rewrite with w+
        with rasterio.open(os.path.join(image_dir,image_file), 'w+', **meta) as dst:  
            dst.write(data_with_new_channel) 
        break # TODO

if __name__ == "__main__":
    dataspace = r"./dataset_roads/China_5m"
    geojson_dir = os.path.join(dataspace,r"roads\geojson")
    raster_dir = os.path.join(dataspace,r"roads\raster_align")
    # density_dir = os.path.join(dataspace,r"roads\density")

    geofiles = os.listdir(geojson_dir)
    for scene_name in geofiles:
        print(f"**********processing {scene_name}*************")
        geojson_path = os.path.join(geojson_dir, scene_name)
        raster_path = os.path.join(raster_dir, scene_name)
        # density_path = os.path.join(density_dir, scene_name)
        # os.makedirs(density_path, exist_ok=True)
        geojsonfiles = os.listdir(geojson_path)
        geojsonlist = [os.path.join(geojson_path, geojsonfile) for geojsonfile in geojsonfiles]

        tifopr = TIFoperation()

        # reftiff = os.path.join(density_path, f"{scene_name}.tiff")
        # density_scale_file = os.path.join(density_path, f"{scene_name}_density_scale.tiff")
        reftiff = os.path.join(raster_path, f"{scene_name}.tiff")
        with rasterio.open(reftiff) as dm:
            density_map = dm.read(1)
            width, hgt = (dm.width,dm.height)
        
        # density = OSM2density()
        # heatmap = density.cal_geojson_to_density_map_large_multiprocess(geojsonlist, reftiff, densityfile, sigma=50)
        # heatmap = density.generate_gaussian_heatmap_small(density_map=density_map, sigma=50)
        heatmap = gaussian_filter(density_map, sigma=100)

        density_path = os.path.join(raster_path, f"{scene_name}_density.tiff")
        with rasterio.open(density_path, 'w', driver='GTiff', height=hgt, width=width, count=1, dtype=heatmap.dtype,
                        crs=dm.crs, transform=dm.transform) as dst:
            dst.write(heatmap, 1)
        # density_file = os.path.join(density_path, f"{scene_name}_density.tiff")
        # tifopr.resize_tiff(density_scale_file, density_file, scale_factor=1)

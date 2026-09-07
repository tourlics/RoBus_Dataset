import os
from scripts.tiff_operation import TIFoperation
from PIL import Image
import rasterio

# def filter_raster(tile):
#     img = np.array(tile).astype(np.float32)
#     # print(len(img[img==1]))
#     if len(img[img==1])>10000:
#         return True
#     else:
#         return False
# def crop_raster_png(scene, raster_path, image_dir):
#     overlap = 0.25
#     target_size = 512#256

#     image = Image.open(os.path.join(raster_path, f"{scene}.tif"))
#     image_width, image_height = image.size   
#     step = int(overlap*target_size)
#     for i in range(0, image_width-target_size, step):
#         for j in range(0, image_height-target_size, step):
#             tile = image.crop((i, j, i+target_size, j+target_size)) # top-left, bottom-right
#             if not filter_raster(tile): continue
#             outputfile = os.path.join(image_dir, f"{scene}_tile_{i}_{j}.png")
#             tile.save(outputfile)
#     # Close the image
#     image.close()
#     return

def crop_raster_tiff_slow(inputpath, image_dir):
    overlap = 0.3
    non_overlap = 1- overlap
    target_size = 512
    ## Not applicable to multi-channel TIF
    # image = Image.open(os.path.join(inputpath))
    # image_width, image_height = image.size
    with rasterio.open(inputpath) as src:
        image_width = src.width
        image_height = src.height
    step = int(non_overlap*target_size)
    scene_name = os.path.basename(inputpath).split(".")[0]
    tifopr = TIFoperation()
    for i in range(0, image_width-target_size, step):
        print(f"cropping {scene_name}: {i}th of total {image_width-target_size}...")
        for j in range(0, image_height-target_size, step):
            tile = [(i, j), (i+target_size, j+target_size)] # top-left, bottom-right
            outputfile = os.path.join(image_dir, f"{scene_name}_tile_{i}_{j}.tif")
            tifopr.crop_tiff_from_pixel_multichannels(inputpath, tile, outputfile)

def crop_raster_tiff(inputpath, image_dir):
    overlap = 0.2
    non_overlap = 1- overlap
    target_size = 256
    # tifopr.crop_tiff_from_pixel_multichannels(inputpath, non_overlap, target_size, image_dir)
    # Random crop
    num_crops = 50
    target_size = 512 # 10000m, 10km
    tifopr.crop_tiff_randomly(inputpath, target_size, num_crops, image_dir)

if __name__ == "__main__":
    dataspace = r"./dataset_roads/UnitedStates"
    # dataspace = r"./dataset_roads/Europe"

    roads_raster_align_dir = os.path.join(dataspace, r"roads\raster_align")
    landuse_raster_align_dir = os.path.join(dataspace, r"landuse\raster_align")
    building_hgt_raster_dir = os.path.join(dataspace, r"buildings\raster")

    all_align_dir = os.path.join(dataspace, "aligned_tiffs")
    cropped_image_dir = os.path.join(dataspace, "cropped_images_random")

    os.makedirs(all_align_dir,exist_ok=True)
    os.makedirs(cropped_image_dir, exist_ok=True)

    for scene_name in os.listdir(roads_raster_align_dir):
        # if scene_name != "Boston": continue
        if scene_name == "Gadsden": continue
        # road_p1_tiff_path = os.path.join(roads_raster_align_dir, scene_name, f"{scene_name}_p1.tiff")
        # road_p2_tiff_path = os.path.join(roads_raster_align_dir, scene_name, f"{scene_name}_p2.tiff")
        # waters_tiff_path = os.path.join(landuse_raster_align_dir, scene_name, f"{scene_name}_waters.tif")
        # woods_tiff_path = os.path.join(landuse_raster_align_dir, scene_name, f"{scene_name}_woods.tif")
        # building_hgt_tiff_path = os.path.join(building_hgt_raster_dir, scene_name, f"{scene_name}_building_hgt_final.tiff")
        # density_tiff_path = os.path.join(roads_raster_align_dir, scene_name, f"{scene_name}_density.tiff")

        merge_tiff_path = os.path.join(all_align_dir, f"{scene_name}.tiff")
        tifopr = TIFoperation()
        # if not os.path.exists(merge_tiff_path):
        #     tifopr.merge_multiple_tif_channel(inputfiles=[road_p1_tiff_path, road_p2_tiff_path, waters_tiff_path, \
        #                                                 woods_tiff_path, building_hgt_tiff_path, density_tiff_path], \
        #                                                     outputfile=merge_tiff_path)
        crop_raster_tiff(merge_tiff_path, cropped_image_dir)

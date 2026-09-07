import rasterio
from PIL import Image
import numpy as np
from webcolors import name_to_rgb
from matplotlib import cm 
import os 
from tqdm import tqdm

road_p1_color = name_to_rgb("Gold")
road_p2_color = name_to_rgb("Silver")
waters_color = name_to_rgb("LightSkyBlue")
woods_color = name_to_rgb("PaleGreen")
bg_color = name_to_rgb("Linen")
color_list = [None, road_p1_color, road_p2_color, waters_color, woods_color, bg_color]

def vis_single_channel(inputtiffpath, outputdir, channel_num, cur_color):
    with rasterio.open(inputtiffpath) as src:
        cur = src.read(channel_num) * (-1)
        fused_array = cur

    red_channel = np.zeros_like(fused_array)
    green_channel = np.zeros_like(fused_array)
    blue_channel = np.zeros_like(fused_array)
    red_channel[fused_array==0] = bg_color[0]
    green_channel[fused_array==0] = bg_color[1]
    blue_channel[fused_array==0] = bg_color[2]

    red_channel[fused_array==-1] = cur_color[0]
    green_channel[fused_array==-1] = cur_color[1]
    blue_channel[fused_array==-1] = cur_color[2]

    image_array = np.dstack((red_channel, green_channel, blue_channel)) 
    # print(image_array.shape) 
    img = Image.fromarray(image_array.astype('uint8'), mode='RGB')  
    filename = os.path.basename(inputtiffpath).split(".")[0]
    img.save(os.path.join(outputdir, f"{filename}_{channel_num}.png"))

def vis_density_channel(inputtiffpath, outputdir):
    density_color_map = "Reds"
    with rasterio.open(inputtiffpath) as ref:
        density = ref.read(6)
    normalized_array = density.copy()
    # normalized_array -= np.min(density)  
    # normalized_array /= np.max(density)  
    colormap = cm.get_cmap(density_color_map)  
    # Convert the normalized array to RGB via colormap  
    rgb_array = colormap(normalized_array) #[:, :, :3]  # Keep RGB channels; drop alpha  
    red_channel = rgb_array[:,:,0]*255
    green_channel = rgb_array[:,:,1] *255 
    blue_channel = rgb_array[:,:,2]*255

    image_array = np.dstack((red_channel, green_channel, blue_channel)) 
    # print(image_array.shape) 
    img = Image.fromarray(image_array.astype('uint8'), mode='RGB')  
    filename = os.path.basename(inputtiffpath).split(".")[0]
    img.save(os.path.join(outputdir, f"{filename}_density.png"))

def vis_landuse_channels(inputtiffpath, outputdir):
    with rasterio.open(inputtiffpath) as src:
        waters = src.read(3) * (-2)
        fused_array = waters
        woods = src.read(4) * (-1)
        fused_array = np.minimum(fused_array, woods)

    red_channel = np.zeros_like(fused_array)
    green_channel = np.zeros_like(fused_array)
    blue_channel = np.zeros_like(fused_array)
    red_channel[fused_array==0] = bg_color[0]
    green_channel[fused_array==0] = bg_color[1]
    blue_channel[fused_array==0] = bg_color[2]

    red_channel[fused_array==-2] = waters_color[0]
    red_channel[fused_array==-1] = woods_color[0]

    green_channel[fused_array==-2] = waters_color[1]
    green_channel[fused_array==-1] = woods_color[1]

    blue_channel[fused_array==-2] = waters_color[2]
    blue_channel[fused_array==-1] = woods_color[2]

    image_array = np.dstack((red_channel, green_channel, blue_channel)) 
    # print(image_array.shape) 
    img = Image.fromarray(image_array.astype('uint8'), mode='RGB')  
    filename = os.path.basename(inputtiffpath).split(".")[0]
    img.save(os.path.join(outputdir, f"{filename}.png"))

def vis_landuse_density_map(inputtiffpath, outputdir):
    with rasterio.open(inputtiffpath) as src:
        waters = src.read(3) * (-2)
        fused_array = waters
        woods = src.read(4) * (-1)
        fused_array = np.minimum(fused_array, woods)
        density = src.read(6)
        

    density_color_map = "Reds"#"magma"

    red_channel = np.zeros_like(fused_array)
    green_channel = np.zeros_like(fused_array)
    blue_channel = np.zeros_like(fused_array)
    red_channel[fused_array==0] = bg_color[0]
    green_channel[fused_array==0] = bg_color[1]
    blue_channel[fused_array==0] = bg_color[2]

    # First, map the values to the range 0-1  
    if np.max(density) > 0:
        normalized_array = density.copy()
        # normalized_array -= np.min(density)  
        # normalized_array /= np.max(density)  
        colormap = cm.get_cmap(density_color_map)  
        # Convert the normalized array to RGB via colormap  
        rgb_array = colormap(normalized_array) #[:, :, :3]  # Keep RGB channels; drop alpha  
        red_channel = rgb_array[:,:,0]*255
        green_channel = rgb_array[:,:,1] *255 
        blue_channel = rgb_array[:,:,2]*255


    red_channel[fused_array==-2] = waters_color[0]
    red_channel[fused_array==-1] = woods_color[0]

    green_channel[fused_array==-2] = waters_color[1]
    green_channel[fused_array==-1] = woods_color[1]

    blue_channel[fused_array==-2] = waters_color[2]
    blue_channel[fused_array==-1] = woods_color[2]

    image_array = np.dstack((red_channel, green_channel, blue_channel)) 
    # print(image_array.shape) 
    img = Image.fromarray(image_array.astype('uint8'), mode='RGB')  
    filename = os.path.basename(inputtiffpath).split(".")[0]
    img.save(os.path.join(outputdir, f"{filename}.png"))


def vis_roadp1_channel(inputtiffpath, outputdir):
    with rasterio.open(inputtiffpath) as src:
        road_p1 = src.read(1) * (-4)
        fused_array = road_p1

    red_channel = np.zeros_like(fused_array)
    green_channel = np.zeros_like(fused_array)
    blue_channel = np.zeros_like(fused_array)
    red_channel[fused_array==0] = bg_color[0]
    green_channel[fused_array==0] = bg_color[1]
    blue_channel[fused_array==0] = bg_color[2]

    red_channel[fused_array==-4] = road_p1_color[0]
    green_channel[fused_array==-4] = road_p1_color[1]
    blue_channel[fused_array==-4] = road_p1_color[2]

    image_array = np.dstack((red_channel, green_channel, blue_channel)) 
    # print(image_array.shape) 
    img = Image.fromarray(image_array.astype('uint8'), mode='RGB')  
    filename = os.path.basename(inputtiffpath).split(".")[0]
    img.save(os.path.join(outputdir, f"{filename}.png"))

def vis_roads_channels(inputtiffpath, outputdir):
    with rasterio.open(inputtiffpath) as src:
        road_p1 = src.read(1) * (-4)
        fused_array = road_p1
        road_p2 = src.read(2) * (-3)
        fused_array = np.minimum(fused_array, road_p2)

    red_channel = np.zeros_like(fused_array)
    green_channel = np.zeros_like(fused_array)
    blue_channel = np.zeros_like(fused_array)
    red_channel[fused_array==0] = bg_color[0]
    green_channel[fused_array==0] = bg_color[1]
    blue_channel[fused_array==0] = bg_color[2]

    red_channel[fused_array==-4] = road_p1_color[0]
    red_channel[fused_array==-3] = road_p2_color[0]

    green_channel[fused_array==-4] = road_p1_color[1]
    green_channel[fused_array==-3] = road_p2_color[1]

    blue_channel[fused_array==-4] = road_p1_color[2]
    blue_channel[fused_array==-3] = road_p2_color[2]

    image_array = np.dstack((red_channel, green_channel, blue_channel)) 
    # print(image_array.shape) 
    img = Image.fromarray(image_array.astype('uint8'), mode='RGB')  
    filename = os.path.basename(inputtiffpath).split(".")[0]
    img.save(os.path.join(outputdir, f"{filename}.png"))

def vis_building_channel(inputtiffpath, outputdir):
    with rasterio.open(inputtiffpath) as src:
        buildings = src.read(5)
    
    building_color_map = "Reds"#"magma"

    red_channel = np.zeros_like(buildings)
    green_channel = np.zeros_like(buildings)
    blue_channel = np.zeros_like(buildings)
    red_channel[buildings==0] = bg_color[0]
    green_channel[buildings==0] = bg_color[1]
    blue_channel[buildings==0] = bg_color[2]

    # First, map the values to the range 0-1  
    if np.max(buildings) > 0:
        buildings[buildings<0]=24
        buildings[buildings>120]=120
        normalized_array = buildings.copy()
        normalized_array -= np.min(buildings)  
        normalized_array /= np.max(buildings)  
        colormap = cm.get_cmap(building_color_map)  
        # Convert the normalized array to RGB via colormap  
        rgb_array = colormap(normalized_array) #[:, :, :3]  # Keep RGB channels; drop alpha  
        red_channel = rgb_array[:,:,0]*255
        green_channel = rgb_array[:,:,1] *255 
        blue_channel = rgb_array[:,:,2]*255

    image_array = np.dstack((red_channel, green_channel, blue_channel)) 
    # print(image_array.shape) 
    img = Image.fromarray(image_array.astype('uint8'), mode='RGB')  
    filename = os.path.basename(inputtiffpath).split(".")[0]
    img.save(os.path.join(outputdir, f"{filename}_building.png"))

def vis_landuse_roads_channel(inputtiffpath, outputdir):
    with rasterio.open(inputtiffpath) as src:
        road_p1 = src.read(1) * (-4)
        fused_array = road_p1
        road_p2 = src.read(2) * (-3)
        fused_array = np.minimum(fused_array, road_p2)
        waters = src.read(3) * (-2)
        fused_array = np.minimum(fused_array, waters)
        woods = src.read(4) * (-1)
        fused_array = np.minimum(fused_array, woods)
    
    red_channel = np.zeros_like(fused_array)
    green_channel = np.zeros_like(fused_array)
    blue_channel = np.zeros_like(fused_array)
    red_channel[fused_array==0] = bg_color[0]
    green_channel[fused_array==0] = bg_color[1]
    blue_channel[fused_array==0] = bg_color[2]


    red_channel[fused_array==-4] = road_p1_color[0]
    red_channel[fused_array==-3] = road_p2_color[0]
    red_channel[fused_array==-2] = waters_color[0]
    red_channel[fused_array==-1] = woods_color[0]

    green_channel[fused_array==-4] = road_p1_color[1]
    green_channel[fused_array==-3] = road_p2_color[1]
    green_channel[fused_array==-2] = waters_color[1]
    green_channel[fused_array==-1] = woods_color[1]

    blue_channel[fused_array==-4] = road_p1_color[2]
    blue_channel[fused_array==-3] = road_p2_color[2]
    blue_channel[fused_array==-2] = waters_color[2]
    blue_channel[fused_array==-1] = woods_color[2]

    image_array = np.dstack((red_channel, green_channel, blue_channel)) 
    # print(image_array.shape) 
    img = Image.fromarray(image_array.astype('uint8'), mode='RGB')  
    filename = os.path.basename(inputtiffpath).split(".")[0]
    img.save(os.path.join(outputdir, f"{filename}.png"))


def vis_landuse_roads_black_channel(inputtiffpath, outputdir):
    with rasterio.open(inputtiffpath) as src:
        road_p1 = src.read(1) * (-4)
        fused_array = road_p1
        road_p2 = src.read(2) * (-3)
        fused_array = np.minimum(fused_array, road_p2)
        waters = src.read(3) * (-2)
        fused_array = np.minimum(fused_array, waters)
        woods = src.read(4) * (-1)
        fused_array = np.minimum(fused_array, woods)
    
    red_channel = np.zeros_like(fused_array)
    green_channel = np.zeros_like(fused_array)
    blue_channel = np.zeros_like(fused_array)
    red_channel[fused_array==0] = bg_color[0]
    green_channel[fused_array==0] = bg_color[1]
    blue_channel[fused_array==0] = bg_color[2]


    red_channel[fused_array==-4] = road_p2_color[0]
    red_channel[fused_array==-3] = road_p2_color[0]
    red_channel[fused_array==-2] = waters_color[0]
    red_channel[fused_array==-1] = woods_color[0]

    green_channel[fused_array==-4] = road_p2_color[1]
    green_channel[fused_array==-3] = road_p2_color[1]
    green_channel[fused_array==-2] = waters_color[1]
    green_channel[fused_array==-1] = woods_color[1]

    blue_channel[fused_array==-4] = road_p2_color[2]
    blue_channel[fused_array==-3] = road_p2_color[2]
    blue_channel[fused_array==-2] = waters_color[2]
    blue_channel[fused_array==-1] = woods_color[2]

    image_array = np.dstack((red_channel, green_channel, blue_channel)) 
    # print(image_array.shape) 
    img = Image.fromarray(image_array.astype('uint8'), mode='RGB')  
    filename = os.path.basename(inputtiffpath).split(".")[0]
    img.save(os.path.join(outputdir, f"{filename}.png"))

def vis_multiple_channel(inputtiffpath, outputdir):
    with rasterio.open(inputtiffpath) as src:
        road_p1 = src.read(1) * (-4)
        fused_array = road_p1
        road_p2 = src.read(2) * (-3)
        fused_array = np.minimum(fused_array, road_p2)
        waters = src.read(3) * (-2)
        fused_array = np.minimum(fused_array, waters)
        woods = src.read(4) * (-1)
        fused_array = np.minimum(fused_array, woods)
        buildings = src.read(5)
    
    building_color_map = "Reds"#"magma"

    red_channel = np.zeros_like(fused_array)
    green_channel = np.zeros_like(fused_array)
    blue_channel = np.zeros_like(fused_array)
    red_channel[fused_array==0] = bg_color[0]
    green_channel[fused_array==0] = bg_color[1]
    blue_channel[fused_array==0] = bg_color[2]

    # First, map the values to the range 0-1  
    if np.max(buildings) > 0:
        buildings[buildings<0]=24
        buildings[buildings>120]=120
        normalized_array = buildings.copy()
        normalized_array -= np.min(buildings)  
        normalized_array /= np.max(buildings)  
        colormap = cm.get_cmap(building_color_map)  
        # Convert the normalized array to RGB via colormap  
        rgb_array = colormap(normalized_array) #[:, :, :3]  # Keep RGB channels; drop alpha  
        red_channel = rgb_array[:,:,0]*255
        green_channel = rgb_array[:,:,1] *255 
        blue_channel = rgb_array[:,:,2]*255

    red_channel[fused_array==-4] = road_p1_color[0]
    red_channel[fused_array==-3] = road_p2_color[0]
    red_channel[fused_array==-2] = waters_color[0]
    red_channel[fused_array==-1] = woods_color[0]

    green_channel[fused_array==-4] = road_p1_color[1]
    green_channel[fused_array==-3] = road_p2_color[1]
    green_channel[fused_array==-2] = waters_color[1]
    green_channel[fused_array==-1] = woods_color[1]

    blue_channel[fused_array==-4] = road_p1_color[2]
    blue_channel[fused_array==-3] = road_p2_color[2]
    blue_channel[fused_array==-2] = waters_color[2]
    blue_channel[fused_array==-1] = woods_color[2]

    image_array = np.dstack((red_channel, green_channel, blue_channel)) 
    # print(image_array.shape) 
    img = Image.fromarray(image_array.astype('uint8'), mode='RGB')  
    filename = os.path.basename(inputtiffpath).split(".")[0]
    img.save(os.path.join(outputdir, f"{filename}.png"))

def vis_multiple_channel_sbuild(inputtiffpath, outputdir):
    with rasterio.open(inputtiffpath) as src:
        road_p1 = src.read(1) * (-4)
        fused_array = road_p1
        road_p2 = src.read(2) * (-3)
        fused_array = np.minimum(fused_array, road_p2)
        waters = src.read(3) * (-2)
        fused_array = np.minimum(fused_array, waters)
        woods = src.read(4) * (-1)
        fused_array = np.minimum(fused_array, woods)
        buildings = src.read(5) 
        fused_array[buildings > 0 ] =5
    
    red_channel = np.zeros_like(fused_array)
    green_channel = np.zeros_like(fused_array)
    blue_channel = np.zeros_like(fused_array)
    red_channel[fused_array==0] = bg_color[0]
    green_channel[fused_array==0] = bg_color[1]
    blue_channel[fused_array==0] = bg_color[2]


    red_channel[fused_array==-4] = road_p1_color[0]
    red_channel[fused_array==-3] = road_p2_color[0]
    red_channel[fused_array==-2] = waters_color[0]
    red_channel[fused_array==-1] = woods_color[0]
    red_channel[fused_array==5] = 255

    green_channel[fused_array==-4] = road_p1_color[1]
    green_channel[fused_array==-3] = road_p2_color[1]
    green_channel[fused_array==-2] = waters_color[1]
    green_channel[fused_array==-1] = woods_color[1]
    green_channel[fused_array==5] = 69

    blue_channel[fused_array==-4] = road_p1_color[2]
    blue_channel[fused_array==-3] = road_p2_color[2]
    blue_channel[fused_array==-2] = waters_color[2]
    blue_channel[fused_array==-1] = woods_color[2]
    blue_channel[fused_array==5] = 0

    image_array = np.dstack((red_channel, green_channel, blue_channel)) 
    # print(image_array.shape) 
    img = Image.fromarray(image_array.astype('uint8'), mode='RGB')  
    filename = os.path.basename(inputtiffpath).split(".")[0]
    img.save(os.path.join(outputdir, f"{filename}.png"))

def get_gray_density_binary_road_map(inputtiffpath, outputdir_density, outputdir_road):
    with rasterio.open(inputtiffpath) as src:
        density = src.read(6)
        road_p1 = src.read(1)
        road_p2 = src.read(2)
        fused_array = np.maximum(road_p1, road_p2)
        
    normalized_array = density.copy()
    normalized_array -= np.min(density)  
    normalized_array /= np.max(density)

    gray_image = normalized_array * 255
    image = Image.fromarray(gray_image.astype(np.uint8))

    filename = os.path.basename(inputtiffpath).split(".")[0]
    image.save(os.path.join(outputdir_density, f"{filename}_density.png"))
    

    binary_image = (fused_array == 1) * 255

    # Convert the numpy array to a PIL image
    image = Image.fromarray(binary_image.astype(np.uint8))

    filename = os.path.basename(inputtiffpath).split(".")[0]
    image.save(os.path.join(outputdir_road, f"{filename}_roads.png"))

if __name__ == "__main__":
    root_dir = r"./dataset_roads/UnitedStates"
    image_dir = os.path.join(root_dir, "cropped_images_random")
    # vis_all_dir = os.path.join(root_dir, "vis_cropped_images")
    # vis_landuse_dir = os.path.join(root_dir, "vis_landuse_images")
    # vis_roads_landuse_dir = os.path.join(root_dir, "vis_roads_landuse_images")
    # vis_filter_dir = os.path.join(root_dir, "vis_roads_filter_images")
    # vis_density_dir = os.path.join(root_dir, "vis_roads_density_images")
    
    vis_landuse_density_dir = os.path.join(root_dir, "vis_landuse_density_images")
    vis_filter_sbuild_dir = os.path.join(root_dir, "vis_filter_sbuild_images")
    os.makedirs(vis_landuse_density_dir, exist_ok=True)
    os.makedirs(vis_filter_sbuild_dir, exist_ok=True)
    
    vis_roads_landuse_black_dir = os.path.join(root_dir, "vis_roads_landuse_black_images")
    os.makedirs(vis_roads_landuse_black_dir, exist_ok=True)
    # os.makedirs(vis_all_dir, exist_ok=True)
    # os.makedirs(vis_landuse_dir, exist_ok=True)
    # os.makedirs(vis_roads_landuse_dir, exist_ok=True)
    # os.makedirs(vis_filter_dir, exist_ok=True)
    # os.makedirs(vis_density_dir, exist_ok=True)
    ############## vis multiple channels ######################
    images = os.listdir(image_dir)
    vis_road_dir = os.path.join(root_dir, "vis_road_dir")
    os.makedirs(vis_road_dir, exist_ok=True)
    for image in tqdm(images):
        if not image.endswith(".tif"): continue
        # vis_multiple_channel(os.path.join(image_dir, image), vis_all_dir)
        vis_roads_channels(os.path.join(image_dir, image), vis_road_dir)
    
    # txt_dir = os.path.join(root_dir, "filter_txt")
    # with open(os.path.join(txt_dir, "task_road_build_gen.txt"), 'r') as file:
    #     road_images = file.readlines()
    # for road_image in tqdm(road_images):
    #     road_image = road_image.replace("\n","")
    #     vis_multiple_channel_sbuild(os.path.join(image_dir, road_image), vis_filter_sbuild_dir)
    #     # vis_landuse_channels(os.path.join(image_dir, road_image), vis_landuse_dir)
    #     # vis_landuse_roads_channel(os.path.join(image_dir, road_image), vis_roads_landuse_dir)
    #     # vis_density_channel(os.path.join(image_dir, road_image), vis_density_dir)
    #     vis_landuse_density_map(os.path.join(image_dir, road_image), vis_landuse_density_dir)
    #     vis_landuse_roads_black_channel(os.path.join(image_dir, road_image), vis_roads_landuse_black_dir)
    
    ##################### vis single examples ##################
    # # sample_name = "Philadelphia_tile_5916_2856"
    # # inputtiffpath = os.path.join(image_dir, f"{sample_name}.tif") # BeiJing_tile_2148_4654, BeiJing_tile_0_3938
    # inputtiffpath = os.path.join(root_dir, "aligned_tiffs", "Philadelphia.tiff")
    # visualization_select_dir = os.path.join(root_dir, "visualization")
    # os.makedirs(visualization_select_dir, exist_ok=True)
    # # for i in range(1,5): # Buildings and density carry continuous values; visualize separately
    # #     vis_single_channel(inputtiffpath, visualization_select_dir, channel_num=i, cur_color=color_list[i])
    # # vis_building_channel(inputtiffpath, visualization_select_dir)
    # # vis_density_channel(inputtiffpath, visualization_select_dir)
    # vis_multiple_channel(inputtiffpath, visualization_select_dir)
    
    ###################### vis topos ####################
    # from scripts.visualization import vis_single_gpickle
    # simtopodir = os.path.join(root_dir, "topo_simplify")
    # vis_single_gpickle(os.path.join(simtopodir, f"{sample_name}.gpickle"))
    # from main_gen_road_topo import raster2topo_multichannel
    # import shutil
    # shutil.copy(inputtiffpath, visualization_select_dir)
    # raster2topo_multichannel(visualization_select_dir, visualization_select_dir, del_dir=None, overwrite=True, simplify=False)
    # vis_single_gpickle(os.path.join(visualization_select_dir, f"{sample_name}.gpickle"))
    
    # ################### get binary roads ############
    # image_train_txt = os.path.join(root_dir, "filter_txt", "US_1w_split", "train.txt")
    # image_test_txt = os.path.join(root_dir, "filter_txt", "US_1w_split", "test.txt")
    # image_val_txt = os.path.join(root_dir, "filter_txt", "US_1w_split", "val.txt")

    # out_density_dir_train = os.path.join(root_dir, "filter_txt", "US_1w_split","road_density_gray", "train")
    # out_density_dir_test = os.path.join(root_dir, "filter_txt", "US_1w_split", "road_density_gray","test")
    # out_density_dir_val = os.path.join(root_dir, "filter_txt", "US_1w_split", "road_density_gray","val")
    # os.makedirs(out_density_dir_test, exist_ok=True)
    # os.makedirs(out_density_dir_train, exist_ok=True)
    # os.makedirs(out_density_dir_val, exist_ok=True)

    # out_road_dir_train = os.path.join(root_dir, "filter_txt", "US_1w_split","road_gray", "train")
    # out_road_dir_test = os.path.join(root_dir, "filter_txt", "US_1w_split", "road_gray","test")
    # out_road_dir_val = os.path.join(root_dir, "filter_txt", "US_1w_split", "road_gray","val")
    # os.makedirs(out_road_dir_test, exist_ok=True)
    # os.makedirs(out_road_dir_train, exist_ok=True)
    # os.makedirs(out_road_dir_val, exist_ok=True)

    # with open(os.path.join(image_train_txt), 'r', encoding='utf-8') as file:  
    #     for line in tqdm(file):  
    #         line = line.replace("\n", "")
    #         get_gray_density_binary_road_map(os.path.join(image_dir, line[:-3]+"tif"), out_density_dir_train, out_road_dir_train)
            
    # with open(os.path.join(image_test_txt), 'r', encoding='utf-8') as file:  
    #     for line in tqdm(file):  
    #         line = line.replace("\n", "")
    #         get_gray_density_binary_road_map(os.path.join(image_dir, line[:-3]+"tif"), out_density_dir_test, out_road_dir_test)
            
    # with open(os.path.join(image_val_txt), 'r', encoding='utf-8') as file:  
    #     for line in tqdm(file):  
    #         line = line.replace("\n", "")
    #         get_gray_density_binary_road_map(os.path.join(image_dir, line[:-3]+"tif"), out_density_dir_val, out_road_dir_val)
            

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
    rgb_array = colormap(normalized_array) #[:, :, :3]  
    red_channel = rgb_array[:,:,0]*255
    green_channel = rgb_array[:,:,1] *255 
    blue_channel = rgb_array[:,:,2]*255

    image_array = np.dstack((red_channel, green_channel, blue_channel)) 
    # print(image_array.shape) 
    img = Image.fromarray(image_array.astype('uint8'), mode='RGB')  
    filename = os.path.basename(inputtiffpath).split(".")[0]
    img.save(os.path.join(outputdir, f"{filename}_density.png"))

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

    if np.max(buildings) > 0:
        buildings[buildings<0]=24
        buildings[buildings>120]=120
        normalized_array = buildings.copy()
        normalized_array -= np.min(buildings)  
        normalized_array /= np.max(buildings)  
        colormap = cm.get_cmap(building_color_map)  

        rgb_array = colormap(normalized_array) #[:, :, :3]   
        red_channel = rgb_array[:,:,0]*255
        green_channel = rgb_array[:,:,1] *255 
        blue_channel = rgb_array[:,:,2]*255

    image_array = np.dstack((red_channel, green_channel, blue_channel)) 
    # print(image_array.shape) 
    img = Image.fromarray(image_array.astype('uint8'), mode='RGB')  
    filename = os.path.basename(inputtiffpath).split(".")[0]
    img.save(os.path.join(outputdir, f"{filename}_building.png"))

if __name__ == "__main__":
    root_dir = r"./samples"
    image_dir = os.path.join(root_dir, "tif_images")
    out_dir = os.path.join(root_dir, "vis")
    os.makedirs(out_dir, exist_ok=True)
    
    ##################### vis single examples ##################
    sample_name = "Philadelphia_tile_5916_5100"
    inputtiffpath = os.path.join(image_dir, f"{sample_name}.tif") 
    for i in range(1,5): 
        vis_single_channel(inputtiffpath, out_dir, channel_num=i, cur_color=color_list[i])
    vis_building_channel(inputtiffpath, out_dir)
    vis_density_channel(inputtiffpath, out_dir)
    
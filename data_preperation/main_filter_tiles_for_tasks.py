import os
import rasterio
import numpy as np
from tqdm import tqdm

def filter_per_tile(inputtiffpath):
    roads_task = False
    road_build_task = False
    with rasterio.open(inputtiffpath) as src:
        road_p1 = src.read(1)
        road_p2 = src.read(2)
        roads = np.maximum(road_p1, road_p2)
        # waters = src.read(3)
        # woods = src.read(4)
        buildings = src.read(5)
    if len(roads[roads>0]) > 256*10:
        roads_task = True
        if len(buildings[buildings>0]) > 800:
            road_build_task = True

    return  roads_task, road_build_task

if __name__ == "__main__":
    root_dir = r"./dataset_roads/China_10m"
    image_dir = os.path.join(root_dir, "cropped_images")
    out_txt_dir = os.path.join(root_dir, "filter_txt")
    os.makedirs(out_txt_dir, exist_ok=True)
    images = os.listdir(image_dir)
    # roads_txt = []
    road_build_txt = []
    # with open(os.path.join(out_txt_dir, "task_road_build_gen.txt"), "w") as rbg:
    #     for image in tqdm(images):
    #         roads_task, road_build_task = filter_per_tile(os.path.join(image_dir, image))
    #         # if roads_task: roads_txt.append(image)
    #         if road_build_task: 
    #             rbg.write(image + "\n")
    with open(os.path.join(out_txt_dir, "task_road_gen.txt"), "w") as rbg:
        for image in tqdm(images):
            roads_task, road_build_task = filter_per_tile(os.path.join(image_dir, image))
            # if roads_task: roads_txt.append(image)
            if roads_task: 
                rbg.write(image + "\n")
                # road_build_txt.append(image)
    # with open(os.path.join(out_txt_dir, "task_road_gen.txt"), "w") as rg:
    #     for item in roads_txt:
    #         rg.write(image + "\n")

            
    # with open(os.path.join(out_txt_dir, "graded_road_gen.txt"), "w") as fgrg:
    #     with open(os.path.join(out_txt_dir, "roads_gen.txt"), "w") as frgs:
    #         with open(os.path.join(out_txt_dir, "building_gen.txt"), "w") as bg:
    #             for image in tqdm(images):
    #                 if not image.endswith(".tif"): continue
    #                 graded_roads_gen, roads_gen, building_gen = filter_per_tile(os.path.join(image_dir, image))
    #                 if graded_roads_gen:
    #                     fgrg.write(image + "\n")
    #                 if roads_gen:
    #                     frgs.write(image + "\n")
    #                 if building_gen:
    #                     bg.write(image + "\n")

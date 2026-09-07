from skimage.morphology import skeletonize
# from sknw.sknw import build_sknw
import cv2
import networkx as nx
import os
import numpy as np
from scripts.extract_topo_layout import extract_topo_graph, \
    merge_nodes, simplify_graph_from_sknw, build_graph_from_ske, simplify_graph, \
    merge_two_close_nodes, relabel_graphs
from scripts.visualization import vis_dir_gpickle, vis_single_gpickle
import shutil
from tqdm import tqdm
import pickle
from scripts.trace_skeleton import traceSkeleton, thinning # slow
# from scripts.skeleton_tracing import trace_skeleton # fast
import rasterio

def is_reserve_topo(graph):
    sub_graphs = [graph.subgraph(c).copy() for c in nx.connected_components(graph)]
    num_compo = len(sub_graphs)
    if num_compo > 1:
        largest = max(sub_graphs, key=len)
        num_nodes = len([node for node in largest.nodes() if largest.degree()[node] > 2]) # Number of nodes with degree > 2
        if num_nodes > 3:
            return True
        else:
            return False
    else:
        return True

def raster2topo_depracated(image_dir, del_dir, topo_dir, overwrite=True):
    # Skeleton + sknw topology extraction; poor quality, deprecated
    files = [file for file in os.listdir(image_dir) if file.endswith(('.tif', '.png'))] 
    for file in tqdm(files):
        # print(file)
        scene = file.split(".")[0]
        ftype = file.split(".")[1]
        if (not overwrite) and os.path.exists(os.path.join(topo_dir, f"{scene}.gpickle")):
            print("Skipping: ", os.path.join(topo_dir, f"{scene}.gpickle"), "EXISTS!")
            continue
        # print("Extracting topo of ", os.path.join(image_dir, f"{scene}.{ftype}"))
        img = cv2.imread(os.path.join(image_dir, f"{scene}.{ftype}"), 2) 
        if ftype == "png":
            _, img = cv2.threshold(img, 127, 1, 0) # Convert to grayscale and binarize
        # img = cv2.resize(img, dsize=(512,512))
        ske = skeletonize(img).astype(np.uint16)
        # import matplotlib.pyplot as plt
        # fig, axes = plt.subplots(1, 2, figsize=(8, 4), sharex=True, sharey=True)
        # ax = axes.ravel()
        # ax[0].imshow(img, cmap=plt.cm.gray)
        # ax[0].set_title('original')
        # ax[0].axis('off')
        # ax[1].imshow(ske, cmap=plt.cm.gray)
        # ax[1].set_title('skeletonize')
        # ax[1].axis('off')
        # fig.tight_layout()
        # plt.show()


        ograph = build_sknw(ske, iso=False, ring=False, full=True)
        
        # # Ignore degree-2 nodes entirely
        # graph = ograph
        # topo_graph = extract_topo_graph(graph)
        # topo_graph = merge_nodes(topo_graph)
        # # nx.write_gpickle(topo_graph, os.path.join(topo_dir, f"{scene}_ignore2.gpickle"))
        # pos = nx.get_node_attributes(topo_graph, 'pos')
        # plt.title(f"Topology Graph (vis) {scene}")
        # nx.draw(topo_graph, pos, with_labels=False, node_size=40)
        # plt.show()
        # break
        
        # Keep shape turns
        graph = ograph
        tolerance = 7 # 2 pixels, for 512x512 input images
        reduced_graph = simplify_graph_from_sknw(graph, tolerance)
        layout_graph = merge_nodes(reduced_graph) # Merge disconnected nodes

        with open(os.path.join(topo_dir, f"{scene}.gpickle"), 'wb') as f:
            pickle.dump(layout_graph, f, pickle.HIGHEST_PROTOCOL)
        # nx.write_gpickle(layout_graph, os.path.join(topo_dir, f"{scene}.gpickle")) # networkx < 3.0
        # if is_reserve_topo(layout_graph):
        #     nx.write_gpickle(layout_graph, os.path.join(topo_dir, f"{scene}.gpickle"))
        # else :
        #     shutil.move(os.path.join(image_dir, file), del_dir)


def raster2topo(image_dir, topo_dir, del_dir=None, overwrite=True, simplify=True):
    # Skeleton + sknw topology extraction; poor quality, deprecated
    files = [file for file in os.listdir(image_dir) if file.endswith(('.tif', '.png'))] 
    for file in tqdm(files):
        # print(file)
        scene = file.split(".")[0]
        ftype = file.split(".")[1]
        if (not overwrite) and os.path.exists(os.path.join(topo_dir, f"{scene}.gpickle")):
            print("Skipping: ", os.path.join(topo_dir, f"{scene}.gpickle"), "EXISTS!")
            continue
        # print("Extracting topo of ", os.path.join(image_dir, f"{scene}.{ftype}"))
        img = cv2.imread(os.path.join(image_dir, f"{scene}.{ftype}"), 2) 
        if ftype == "png":
            _, img = cv2.threshold(img, 127, 1, 0) # Convert to grayscale and binarize
        # img = cv2.resize(img, dsize=(512,512))

        im = thinning(img)
        rects = []
        polys = traceSkeleton(im,0,0,im.shape[1],im.shape[0],10,999,rects)

        ograph = build_graph_from_ske(polys)
        if simplify:
            # Keep shape turns and simplify the graph
            # vis_single_gpickle(ograph)
            graph = merge_two_close_nodes(ograph, tolerance=1.5) # Nodes only 1 pixel apart
            # vis_single_gpickle(graph)
            graph = simplify_graph(graph, angle_threshold=160) # Angle 160
            # vis_single_gpickle(graph)
            graph = merge_two_close_nodes(graph, tolerance=10) 
            # vis_single_gpickle(graph)
            graph = simplify_graph(graph, angle_threshold=160) # Angle 160
            # vis_single_gpickle(graph)
        else:
            graph = ograph

        with open(os.path.join(topo_dir, f"{scene}.gpickle"), 'wb') as f:
            pickle.dump(graph, f, pickle.HIGHEST_PROTOCOL)
        # nx.write_gpickle(layout_graph, os.path.join(topo_dir, f"{scene}.gpickle")) # networkx < 3.0
        # if is_reserve_topo(layout_graph):
        #     nx.write_gpickle(layout_graph, os.path.join(topo_dir, f"{scene}.gpickle"))
        # else :
        #     shutil.move(os.path.join(image_dir, file), del_dir)

def raster2topo_multichannel(image_dir, topo_dir, del_dir=None, overwrite=True, simplify=True):
    files = [file for file in os.listdir(image_dir) if file.endswith('.tif')] 
    for file in tqdm(files):
        # print(file)
        scene = file.split(".")[0]
        ftype = file.split(".")[1]
        if (not overwrite) and os.path.exists(os.path.join(topo_dir, f"{scene}.gpickle")):
            print("Skipping: ", os.path.join(topo_dir, f"{scene}.gpickle"), "EXISTS!")
            continue
        # print("Extracting topo of ", os.path.join(image_dir, f"{scene}.{ftype}"))
        with rasterio.open(os.path.join(image_dir, f"{scene}.tif")) as src:    
            data_p1 = src.read(1) 
            data_p2 = src.read(2)
        img = np.maximum(data_p1, data_p2)
        # slow
        im = thinning(img)
        rects = []
        polys = traceSkeleton(im,0,0,im.shape[1],im.shape[0],10,999,rects)
        ograph = build_graph_from_ske(polys)
        if simplify:
            # Keep shape turns and simplify the graph
            # vis_single_gpickle(ograph)
            graph = merge_two_close_nodes(ograph, tolerance=1.5) # Nodes only 1 pixel apart
            # vis_single_gpickle(graph)
            graph = simplify_graph(graph, angle_threshold=160) # Angle 160
            # vis_single_gpickle(graph)
            graph = merge_two_close_nodes(graph, tolerance=10) 
            # vis_single_gpickle(graph)
            graph = simplify_graph(graph, angle_threshold=160) # Angle 160
            # vis_single_gpickle(graph)
        else:
            graph = relabel_graphs(ograph)
        with open(os.path.join(topo_dir, f"{scene}.gpickle"), 'wb') as f:
            pickle.dump(graph, f, pickle.HIGHEST_PROTOCOL)

def raster2topo_multichannel_cpython(image_dir, topo_dir, del_dir, overwrite=True, simplify=True):
    files = [file for file in os.listdir(image_dir) if file.endswith('.tif')] 
    for file in tqdm(files):
        # print(file)
        scene = file.split(".")[0]
        ftype = file.split(".")[1]
        if (not overwrite) and os.path.exists(os.path.join(topo_dir, f"{scene}.gpickle")):
            print("Skipping: ", os.path.join(topo_dir, f"{scene}.gpickle"), "EXISTS!")
            continue
        # print("Extracting topo of ", os.path.join(image_dir, f"{scene}.{ftype}"))
        with rasterio.open(os.path.join(image_dir, f"{scene}.tif")) as src:    
            data_p1 = src.read(1) 
            data_p2 = src.read(2)
        # imgcv = cv2.imread(os.path.join(image_dir, f"{scene}.tif"),cv2.IMREAD_UNCHANGED)
        # print(imgcv.shape)
        # data_p1 = imgcv[:,:,0]
        # data_p2 = imgcv[:,:,1]
        img = np.maximum(data_p1, data_p2).astype('uint8')
        # cv2.imshow(f"{scene}", img*255)
        polys = trace_skeleton.from_numpy(img) # fast
        ograph = build_graph_from_ske(polys)
        if simplify:
            # Keep shape turns and simplify the graph
            # vis_single_gpickle(ograph)
            graph = merge_two_close_nodes(ograph, tolerance=1.5) # Nodes only 1 pixel apart
            # vis_single_gpickle(graph)
            graph = simplify_graph(graph, angle_threshold=160) # Angle 160
            # vis_single_gpickle(graph)
            graph = merge_two_close_nodes(graph, tolerance=10) 
            # vis_single_gpickle(graph)
            graph = simplify_graph(graph, angle_threshold=160) # Angle 160
            # vis_single_gpickle(graph)
            
        else:
            graph = relabel_graphs(ograph)
        with open(os.path.join(topo_dir, f"{scene}.gpickle"), 'wb') as f:
            pickle.dump(graph, f, pickle.HIGHEST_PROTOCOL)

def gen_single_topo_from_png(scene_name):
    # image_path = r"./data/samples/res/4.png"
    # scene_name = "NewYork13_tile_816_0"
    image_path = rf"./data/results/pix2pix_for_topo/{scene_name}.png"
    # topo_path = r"./data/samples/topo/Atlanta_tile_2856_1632.png"
    topo_path = rf"./data/results/topo_pix/{scene_name}.gpickle"
    im_white = cv2.imread(image_path,0)

    im = 255 - im_white
    # print(im)
    _,im = cv2.threshold(im,40,100,cv2.THRESH_BINARY)
    im[im==100]=1
    print(np.max(im))
    # cv2.imshow("",im*255);cv2.waitKey(0)
    rects = []
    polys = traceSkeleton(im,0,0,im.shape[1],im.shape[0],10,999,rects)
    ograph = build_graph_from_ske(polys)
    # Keep shape turns and simplify the graph
    # vis_single_gpickle(ograph)
    graph = merge_two_close_nodes(ograph, tolerance=1.5) # Nodes only 1 pixel apart
    # vis_single_gpickle(graph)
    graph = simplify_graph(graph, angle_threshold=160) # Angle 160
    # vis_single_gpickle(graph)
    graph = merge_two_close_nodes(graph, tolerance=10) 
    # vis_single_gpickle(graph)
    graph = simplify_graph(graph, angle_threshold=160) # Angle 160
    for node in list(graph.nodes()):  
        if graph.degree(node) == 0:  
            graph.remove_node(node)
    graph = relabel_graphs(graph)
    vis_single_gpickle(graph)
    
    with open(topo_path, 'wb') as f:
        pickle.dump(graph, f, pickle.HIGHEST_PROTOCOL)

if __name__ == "__main__":
    # root_dir = r"./dataset_roads/Europe"
    # image_dir = os.path.join(root_dir, "cropped_images")
    # topo_dir = os.path.join(root_dir, "topo_simplify")
    # # del_dir = os.path.join(root_dir, "del_images")
    # # topo_vis_dir = os.path.join(root_dir, "topo_vis_png")
    # os.makedirs(topo_dir, exist_ok=True)
    # # os.makedirs(del_dir, exist_ok=True)
    # # os.makedirs(topo_vis_dir, exist_ok=True)
    # raster2topo_multichannel_cpython(image_dir, topo_dir, del_dir=None, overwrite=False, simplify=True)
    # # vis_dir_gpickle(topo_dir, topo_vis_dir)
    # gen_single_topo_from_png()

    image_dir = r'./data/results/pix2pix_for_topo'
    for scene in os.listdir(image_dir):
        gen_single_topo_from_png(scene.split(".")[0])
    
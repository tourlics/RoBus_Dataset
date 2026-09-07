from matplotlib import pyplot as plt
import os
import networkx as nx
import numpy as np
import random
from tqdm import tqdm
import pickle

def vis_topo(topo_dir, topo_dir_vis):
    files = [file for file in os.listdir(topo_dir) if file.endswith(('.gpickle'))] 
    for file in files:
        scene = file.split(".")[0]
        print("Visualizing topo of", os.path.join(topo_dir, f"{scene}.gpickle"))
        graph = nx.read_gpickle(os.path.join(topo_dir,file))
        pos = nx.get_node_attributes(graph, 'pos')
        plt.title(f"Layout Graph {scene}")
        nx.draw(graph, pos, with_labels=False, node_size=6, width = 2, edge_color = 'lightblue', node_color = 'red')
        plt.savefig(os.path.join(topo_dir_vis, scene+"_topo.png"))
        plt.cla()

def gpickle2npy(topo_dir, npy_path):
    files = [file for file in os.listdir(topo_dir) if file.endswith(('.gpickle'))] 
    if len(files) < 5000:
        print("file num must be greater than 5000 !!!")
        raise ValueError
    files_sampled = random.sample(files, 5000)
    acb_list = []
    ort_list = []
    con_list = []
    insec_list = []
    for file in files_sampled:
        graph = nx.read_gpickle(os.path.join(topo_dir,file))
        acb_list.append(graph.graph["acb"])
        ort_list.append(graph.graph["ort"])
        con_list.append(graph.graph["con"])
        insec_list.append(graph.graph["insec"])
    acb_np = np.asarray(acb_list)
    ort_np = np.asarray(ort_list)
    con_np = np.asarray(con_list)
    insec_np = np.asarray(insec_list)
    out_dict = {"length": len(files),"acb_np": acb_np, "ort_np": ort_np, "con_np":con_np, "insec_np":insec_np}
    np.save(npy_path, out_dict)

def vis_metric_bins_from_npy(npy_path_list, metric, strxlabel, distance):
    data_list = []
    min_data = 99999
    max_data = 0
    for npy_path in npy_path_list:
        metrics_dict = np.load(npy_path, allow_pickle=True)
        data = metrics_dict.item()[metric]
        print(len(data[data<=0.5]), len(data[data<= 3]), len(data[data>3]))
        data_list.append(data)
        if max(data) > max_data: max_data = max(data)
        if min(data) < min_data: min_data = min(data)
    
    colorbar = ["lightskyblue", "wheat"]
    plt.figure(figsize=(20,8),dpi=100)
    groups_num = int((max_data - min_data)/distance) # bin width is distance; compute bin count
    for idx, data in enumerate(data_list):
        plt.hist(data,bins=groups_num, color=colorbar[idx])
    plt.xticks(np.arange(min_data, max_data, step=distance))
    plt.grid(linestyle='--',alpha=0.5)
    plt.xlabel(strxlabel)
    plt.ylabel('Density')
    plt.savefig(npy_path.replace(".npy", f"_{metric}.png"))
    plt.show()

def vis_stacked_bins_from_npy(npy_path_list, metric, strxlabel, distance):
    data_list = []
    min_data = 99999
    max_data = 0
    for npy_path in npy_path_list:
        metrics_dict = np.load(npy_path, allow_pickle=True)
        data = metrics_dict.item()[metric]
        data_list.append(data)
        if max(data) > max_data: max_data = max(data)
        if min(data) < min_data: min_data = min(data)
    # colorbar = ["#4c9be6", "#98a9d0", "#ffe2ce", "#bee8e8"]
    colorbar = ["#e3c6e0", "#f7c4c1", "#c3e2ec", "#dbedc5"] # light colors
    # colorbar = ["#cac0e1", "#f6c0cc", "#abdaec", "#97d1a0"]
    plt.figure(figsize=(20,8), dpi=100)
    bins = np.arange(min_data, max_data+distance, distance)
    if len(bins) < 2: 
        bins = [min_data, min_data + distance, max_data]
    n, bins, patches = plt.hist(data_list, bins=bins, color=colorbar, stacked=True, rwidth=0.8)
    plt.xticks(bins)
    plt.xlabel(strxlabel)
    plt.ylabel('Density')
    plt.show()

def vis_stacked_bins_from_npy_clamp(npy_path_list, metric, strxlabel, distance, clamp_range):
    data_list = []
    min_data = clamp_range[0]
    max_data = clamp_range[1]

    for npy_path in npy_path_list:
        metrics_dict = np.load(npy_path, allow_pickle=True)
        data = metrics_dict.item()[metric]
        # data_clamp = np.clip(data, clamp_range[0], clamp_range[1])
        data_clamp = data[(data>clamp_range[0]) & (data<clamp_range[1])]
        data_list.append(data_clamp)
        # if max(data) > max_data: max_data = max(data)
        # if min(data) < min_data: min_data = min(data)
    # colorbar = ["#4c9be6", "#98a9d0", "#ffe2ce", "#bee8e8"]
    colorbar = ["#e3c6e0", "#f7c4c1", "#c3e2ec", "#dbedc5"] # light colors
    # colorbar = ["#d3b6d0", "#e7b4b1", "#b3d2dc", "#cbedb5"] # dark colors
    # colorbar = ["#cac0e1", "#f6c0cc", "#abdaec", "#97d1a0"]
    plt.figure(figsize=(20,8), dpi=100)
    bins = np.arange(min_data, max_data+distance, distance)
    if len(bins) < 2: 
        bins = [min_data, min_data + distance, max_data]
    n, bins, patches = plt.hist(data_list, bins=bins, color=colorbar, stacked=True, rwidth=0.8)
    plt.xticks(bins, size=7)
    # plt.xlabel(strxlabel)
    # plt.ylabel('Density')
    plt.show()

def vis_pie_from_npy_for_cls(npy_path_list):
    for npy_path in npy_path_list:
        # load data
        metrics_dict = np.load(npy_path, allow_pickle=True).item()
        data_density = metrics_dict["building_density"]
        data_height = metrics_dict["building_height"]
        
        # split samples by metric thresholds
        categories = {'Sparse, Low': 0, 'Sparse, Tall': 0, 'Dense, Low': 0, "Dense, Tall":0}
        for den, hgt in zip(data_density, data_height):
            if den > 0.2 and hgt > 10:
                categories["Dense, Tall"] += 1
            elif den <= 0.2 and hgt > 10:
                categories['Sparse, Tall'] += 1
            elif den <= 0.2 and hgt <= 10:
                categories['Sparse, Low'] += 1
            elif den>0.2 and hgt <=10:
                categories['Dense, Low'] += 1
            else:
                continue
    colors = ['#b6e7ca', "#fcd4d1", '#b1cce6', '#fee99c']
    sizes = list(categories.values())
    labels = list(categories.keys())
    fig, ax = plt.subplots()
    ax.pie(sizes, colors=colors, autopct='%1.1f%%', startangle=90, textprops={"fontsize":14})
    ax.axis('equal')
    # plt.legend(labels)
    # plt.title(f'Building Types in City Block')
    plt.show()


def vis_metric_bins_from_npy_clamp(npy_path_list, metric, strxlabel, distance, clamp_range):
    data_list = []

    clamp_range[0] = round(clamp_range[0]/8, 2)
    clamp_range[1] = round(clamp_range[1]/8, 2)
    distance = round(distance/8, 2)
    
    min_data = clamp_range[0]
    max_data = clamp_range[1]
    for npy_path in npy_path_list:
        metrics_dict = np.load(npy_path, allow_pickle=True)
        data = metrics_dict.item()[metric]
        data_clamp = np.clip(data, clamp_range[0], clamp_range[1])
        print(npy_path, f"{strxlabel}",np.mean(data_clamp))
        data_list.append(data_clamp)
    colorbar = ["deepskyblue", "orange", "limegreen"]
    plt.figure(figsize=(40,8),dpi=100)
    groups_num = int((max_data - min_data)/distance) # bin width is distance; compute bin count
    # for idx, cdata in enumerate(data_list):
    plt.hist(data_list, bins=groups_num, color=colorbar, histtype="bar", rwidth=0.9, alpha=0.5)
    
    plt.xticks(np.arange(min_data, max_data, step=distance), fontsize=24)
    # plt.grid(linestyle='--',alpha=0.5)
    plt.xlabel(strxlabel, fontsize=32)
    plt.ylabel('Density', fontsize=32)
    # plt.legend(["Observed", "Synthesized (w/o R)", "Synthesized ( w/  R)"], loc="upper left", fontsize=32)
    # plt.savefig(npy_path.replace(".npy", f"_{metric}.png"))
    plt.show()

def vis_single_gpickle(gpickle_path):
    if type(gpickle_path) is str:
        with open(gpickle_path, 'rb') as f:
            graph = pickle.load(f)
    else:
        graph = gpickle_path
    # graph = nx.read_gpickle(gpickle_path)
    pos = nx.get_node_attributes(graph, 'pos')
    # plt.title(f"Topology Graph (vis) {gpickle_path}")
    nx.draw(graph, pos, with_labels=False, node_size=40)
    plt.show()

def vis_single_gpickle_posxy(gpickle_path):
    if type(gpickle_path) is str:
        with open(gpickle_path, 'rb') as f:
            graph = pickle.load(f)
    else:
        graph = gpickle_path
    # graph = nx.read_gpickle(gpickle_path)
    posx = nx.get_node_attributes(graph, 'posx')
    posy = nx.get_node_attributes(graph, 'posy')
    pos = {}
    print(posx, posy)
    for px, py in zip(posx, posy):
        pos[px] = (posx[px], posy[px])
    # plt.title(f"Topology Graph (vis) {gpickle_path}")
    # nodes_remove = [node for node in graph.nodes() if "posx" not in graph.nodes[node]]
    nodes_remove = [node for node in graph.nodes() if graph.nodes[node]["posx"]==0]
    graph.remove_nodes_from(nodes_remove)
    graph.add_edges_from([(7,19),(19,24),(33,40),(40,49),(49,52),(52,54), (65,74),(74,79),(79,85), (104,109)])
    
    nx.draw(graph, pos=pos, with_labels=False, node_size=400, width=8, node_color="orange", edge_color="lightblue")
    plt.show()

def vis_dir_gpickle(gpickle_dir, out_dir):
    gpts = os.listdir(gpickle_dir)
    for gpickle_path in tqdm(gpts):
        # graph = nx.read_gpickle(os.path.join(gpickle_dir,gpickle_path)) # networkx < 3.0
        with open(os.path.join(gpickle_dir,gpickle_path), 'rb') as f:
            graph = pickle.load(f)
        pos = nx.get_node_attributes(graph, 'pos')
        # plt.title(f"Topology Graph (vis) {gpickle_path}")
        nx.draw(graph, pos, with_labels=False, node_size=40)
        # plt.show()
        plt.savefig(os.path.join(out_dir,f"{gpickle_path.split('.')[0]}.png"))
        plt.cla()


if __name__ == "__main__":
    topo_dir1 = r"./data/dataset_road_generation/data_road_generation_metrics/topo"
    topo_dir2 = r"./data/dataset_road_generation/data_road_generation_metrics/topo2"
    topo_dir3 = r"./data/dataset_road_generation/data_road_generation_metrics/topo3"
    topo_dir_vis = r"./data/dataset_road_generation/data_road_generation_metrics"
    os.makedirs(topo_dir_vis, exist_ok=True)
    # vis_topo(topo_dir, topo_dir_vis)
    npy_path1 = r"./data/dataset_road_generation/data_road_generation_metrics/metrics1.npy"
    npy_path2 = r"./data/dataset_road_generation/data_road_generation_metrics/metrics2.npy"
    npy_path3 = r"./data/dataset_road_generation/data_road_generation_metrics/metrics3.npy"
    # gpickle2npy(topo_dir1, npy_path1)
    # gpickle2npy(topo_dir2, npy_path2)
    # gpickle2npy(topo_dir3, npy_path3)
    npy_path_list = [npy_path2, npy_path3]
    vis_metric_bins_from_npy_clamp(npy_path_list, metric="acb_np", strxlabel='Traffic Conveniency', distance=0.02, clamp_range=[0.6,1])
    # vis_metric_bins_from_npy_clamp(npy_path_list, metric="ort_np", strxlabel="Orientation Entropy", distance=0.1, clamp_range=[1.9,3.8])
    # vis_metric_bins_from_npy_clamp(npy_path_list, metric="ort_np", strxlabel="Orientation Order", distance=0.1, clamp_range=[1.9,3.8])

    # vis_metric_bins_from_npy_clamp(npy_path_list, metric="con_np", strxlabel="Road Connectivity", distance=0.1, clamp_range=[1.9,4.0])
    # vis_metric_bins_from_npy_clamp(npy_path_list, metric="insec_np", strxlabel="Intersection Density", distance=0.05, clamp_range=[0,0.8])
    # vis_single_gpickle(gpickle_path=r"./data/data_road_generation/pics_vis/topo/113_tile_832_1408.gpickle")
    # vis_dir_gpickle(gpickle_dir=r"./data/data_road_generation/pics_vis/topo", out_dir=r"./data/data_road_generation/pics_vis/visualization")
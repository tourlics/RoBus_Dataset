import os
import networkx as nx
import numpy as np

from tqdm import tqdm
import pickle
# from scripts.trace_skeleton import traceSkeleton, thinning # slow
from scripts.skeleton_tracing import trace_skeleton # fast
import rasterio
# import cv2
from scripts.visualization import vis_single_gpickle

from rdp import rdp

def relabel_graphs(graph):
    mapping = dict(zip(graph, range(0, graph.number_of_nodes())))
    graph = nx.relabel_nodes(graph, mapping) 
    return graph

def merge_two_close_nodes(graph, tolerance):
    while True :
        short_edges = [edge for edge in graph.edges() if graph.edges[edge]["length"] < tolerance]
        if len(short_edges) == 0: break
        edge = short_edges[0]
        seed_node = edge[0]
        # print(edge)
        # print(seed_node)
        node_to_remove = edge[1]
        # print(node_to_remove)
        neighbors = list(graph.neighbors(node_to_remove))
        # print(neighbors)
        if seed_node in neighbors: neighbors.remove(seed_node)
        for i in neighbors:
            seed_node_pos = graph.nodes[seed_node]["pos"]
            i_pos = graph.nodes[i]["pos"]
            graph.add_edge(seed_node,i, length=get_distance(seed_node_pos, i_pos))
            graph.remove_edge(node_to_remove,i)
        graph.remove_node(node_to_remove)
        graph = relabel_graphs(graph)
    return graph

def angle_between_vectors(v1, v2):  
    # Angle between two vectors in radians  
    dot_product = np.dot(v1, v2)  
    norm_v1 = np.linalg.norm(v1)  
    norm_v2 = np.linalg.norm(v2)  
    cos_theta = dot_product / (norm_v1 * norm_v2)  
    theta = np.arccos(cos_theta)  
    return theta  

def simplify_graph(graph, angle_threshold):  
    # Convert the angle threshold from degrees to radians  
    angle_threshold_rad = np.deg2rad(angle_threshold)  
      
    # Keep simplifying until no more nodes can be removed  
    simplified = True  
    while simplified:  
        simplified = False  
        nodes_to_remove = []  
          
        # Iterate over all degree-2 nodes  
        for node in list(graph.nodes()):  
            if graph.degree(node) == 2:  
                # Get the two neighbors of this node  
                neighbors = list(graph.neighbors(node))  
                # Coordinate-difference vectors to the two neighbors  
                v1 = np.array(graph.nodes[neighbors[0]]['pos']) - np.array(graph.nodes[node]['pos'])  
                v2 = np.array(graph.nodes[neighbors[1]]['pos']) - np.array(graph.nodes[node]['pos'])  
                  
                # Compute the included angle  
                angle = angle_between_vectors(v1, v2)  
                  
                # Remove the node if the angle exceeds the threshold  
                if angle > angle_threshold_rad:  
                    nodes_to_remove.append(node)  
                    # Add an edge that directly connects the two neighbors  
                    graph.add_edge(neighbors[0], neighbors[1], \
                                   length = get_distance(graph.nodes[neighbors[0]]["pos"], graph.nodes[neighbors[1]]["pos"]))  
          
        # If any nodes should be deleted, remove them and set simplified=True  
        if nodes_to_remove:  
            graph.remove_nodes_from(nodes_to_remove)  
            simplified = True 
    
    graph = relabel_graphs(graph)
      
    return graph

def get_distance(n1, n2):
    return ((n1[0]-n2[0])**2 + (n1[1]-n2[1])**2)**0.5

def build_graph_from_ske(polys, epsilon=1.5):
    node_num = 0
    ograph = nx.Graph()
    for ol in polys:
        # l = rdp(ol, epsilon)
        l = ol
        ograph.add_node(node_num, pos=(l[0][0],l[0][1]))
        for i in range(0,len(l)-1):
            ograph.add_node(node_num+1, pos=(l[i+1][0],l[i+1][1]))
            ograph.add_edge(node_num, node_num+1, length = get_distance((l[i][0],l[i][1]), (l[i+1][0],l[i+1][1])))
            node_num += 1
        node_num += 1
             
    from collections import defaultdict
    # Remove nodes that share a duplicate pos  
    pos_to_nodes = defaultdict(list)  
    for node, data in ograph.nodes(data=True):  
        pos = data.get('pos')  
        if pos is not None:  
            pos_to_nodes[tuple(pos)].append(node)  
      
    # For each pos group, pick one representative node  
    for pos, nodes in pos_to_nodes.items():  
        if len(nodes) > 1:  # Multiple nodes share the same pos  
            representative = nodes[0]  # Use the first node as the representative  
            for node in nodes[1:]:  # Process the remaining nodes  
                # Connect their neighbors to the representative  
                for neighbor in ograph.neighbors(node):  
                    if neighbor not in nodes:  # Avoid self-loops  
                        ograph.add_edge(representative, neighbor, \
                                        length = get_distance(ograph.nodes[representative]["pos"], ograph.nodes[neighbor]["pos"]))  
                # Remove the other nodes  
                ograph.remove_node(node)  
    return ograph

def raster2topo_multichannel(image_dir, topo_dir, del_dir, overwrite=True, simplify=True):
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
            data_p2 = src.read(1)
        # imgcv = cv2.imread(os.path.join(image_dir, f"{scene}.tif"),cv2.IMREAD_UNCHANGED)
        # print(imgcv.shape)
        # data_p1 = imgcv[:,:,0]
        # data_p2 = imgcv[:,:,1]
        img = np.maximum(data_p1, data_p2).astype('uint8')
        polys = trace_skeleton.from_numpy(img) # fast
        # import cv2
        # for l in polys:
        #     for i in range(0,len(l)-1): 
        #         cv2.line(img,(l[i][0],l[i][1]),(l[i+1][0],l[i+1][1]),color=(255,0,0)) 
        # cv2.imwrite("./t.png",img)
        ograph = build_graph_from_ske(polys, epsilon=1.5)
        if simplify:
            # Keep shape turns and simplify the graph
            # vis_single_gpickle(ograph)
            graph = merge_two_close_nodes(ograph, tolerance=1.5) # Nodes only 1 pixel apart
            # # vis_single_gpickle(graph)
            graph = simplify_graph(graph, angle_threshold=160) # Angle 160
            # vis_single_gpickle(graph)
            graph = merge_two_close_nodes(graph, tolerance=10) 
            # vis_single_gpickle(graph)
            graph = simplify_graph(graph, angle_threshold=160) # Angle 160
            vis_single_gpickle(graph)
        else:
            graph = relabel_graphs(ograph)
        with open(os.path.join(topo_dir, f"{scene}.gpickle"), 'wb') as f:
            pickle.dump(graph, f, pickle.HIGHEST_PROTOCOL)

if __name__ == "__main__":
    # root_dir = r"./dataset_roads/China_5m"
    root_dir = r"./data"
    image_dir = os.path.join(root_dir, "cropped_images")
    topo_dir = os.path.join(root_dir, "topo_simplify")
    # del_dir = os.path.join(root_dir, "del_images")
    topo_vis_dir = os.path.join(root_dir, "topo_vis_png")
    os.makedirs(topo_dir, exist_ok=True)
    # os.makedirs(del_dir, exist_ok=True)
    os.makedirs(topo_vis_dir, exist_ok=True)
    raster2topo_multichannel(image_dir, topo_dir, del_dir=None, overwrite=True, simplify=True)
    # vis_dir_gpickle(topo_dir, topo_vis_dir)
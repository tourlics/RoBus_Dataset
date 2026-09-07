from skimage.morphology import skeletonize
from skimage import data
# from sknw.sknw import build_sknw
import numpy as np
from matplotlib import pyplot as plt
import cv2
import scipy.io
import networkx as nx
from shapely.geometry import LineString, Point
import os

def merge_nodes(graph):
    while True :
        short_edges = []
        cand_edges = [edge for edge in graph.edges() if graph.edges[edge]["length"] < 20]
        for edge in cand_edges:
            if graph.degree[edge[0]] == 3 and graph.degree[edge[1]] == 3: 
                short_edges.append(edge)
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

def merge_nodes_bug(graph):
    short_edges = []
    cand_edges = [edge for edge in graph.edges() if graph.edges[edge]["length"] < 20]
    for edge in cand_edges:
        if graph.degree[edge[0]] == 3 and graph.degree[edge[1]] == 3: 
            short_edges.append(edge)
    for edge in short_edges:
        seed_node = edge[0]
        print(edge)
        print(seed_node)
        node_to_remove = edge[1]
        print(node_to_remove)
        neighbors = list(graph.neighbors(node_to_remove))
        # print(neighbors)
        if seed_node in neighbors: neighbors.remove(seed_node)
        for i in neighbors:
            graph.add_edge(seed_node,i)
            graph.remove_edge(node_to_remove,i)
        graph.remove_node(node_to_remove)
    
    graph = relabel_graphs(graph)
        
    return graph


def simplify_lines(line, tolerance):
    # Simplify the line string with a tolerance of 2 (2 pixels)
    simplified_line = line.simplify(tolerance=tolerance, preserve_topology=True)

    # Print the original and simplified line strings
    # print("Original line: ", line)
    # print("Simplified line: ", simplified_line)
    sim_x, sim_y = simplified_line.xy
    return sim_x, sim_y

def get_distance(n1, n2):
    return ((n1[0]-n2[0])**2 + (n1[1]-n2[1])**2)**0.5

def simplify_graph_from_sknw(graph, tolerance):
    new_graph = nx.Graph()
    pos_list = []
    # draw edges by pts
    for (s,e) in graph.edges():
        ps = graph[s][e]['pts']
        line = LineString(ps)
        sim_x, sim_y = simplify_lines(line, tolerance)

        len_sim_x = len(sim_x)
        for i in range(len_sim_x-1):
            # first vertex of the polyline
            node_pos1 = (sim_y[i], sim_x[i])
            if node_pos1 not in pos_list:
                pos_list.append(node_pos1)
            node_num1 = pos_list.index(node_pos1)
            new_graph.add_node(node_num1, pos = node_pos1)
            # second vertex of the polyline
            node_pos2 = (sim_y[i+1], sim_x[i+1])
            if node_pos2 not in pos_list:
                pos_list.append(node_pos2)
            node_num2 = pos_list.index(node_pos2)
            new_graph.add_node(node_num2, pos = node_pos2)
            new_graph.add_edge(node_num1, node_num2, length = get_distance(node_pos1, node_pos2))
    return new_graph


def angle_between_vectors(v1, v2):  
    # angle between two vectors (radians)
    dot_product = np.dot(v1, v2)  
    norm_v1 = np.linalg.norm(v1)  
    norm_v2 = np.linalg.norm(v2)  
    cos_theta = dot_product / (norm_v1 * norm_v2)  
    theta = np.arccos(cos_theta)  
    return theta  

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

def simplify_graph(graph, angle_threshold):  
    # convert angle threshold from degrees to radians
    angle_threshold_rad = np.deg2rad(angle_threshold)  
      
    # keep simplifying until no more nodes can be removed
    simplified = True  
    while simplified:  
        simplified = False  
        nodes_to_remove = []  
          
        # iterate degree-2 nodes
        for node in list(graph.nodes()):  
            if graph.degree(node) == 2:  
                # the two neighbors of this node
                neighbors = list(graph.neighbors(node))  
                # coordinate-difference vectors to the neighbors
                v1 = np.array(graph.nodes[neighbors[0]]['pos']) - np.array(graph.nodes[node]['pos'])  
                v2 = np.array(graph.nodes[neighbors[1]]['pos']) - np.array(graph.nodes[node]['pos'])  
                  
                # included angle
                angle = angle_between_vectors(v1, v2)  
                  
                # drop the node if the angle exceeds the threshold
                if angle > angle_threshold_rad:  
                    nodes_to_remove.append(node)  
                    # add an edge that directly connects the two neighbors
                    graph.add_edge(neighbors[0], neighbors[1], \
                                   length = get_distance(graph.nodes[neighbors[0]]["pos"], graph.nodes[neighbors[1]]["pos"]))  
          
        # if nodes were marked, remove them and keep iterating
        if nodes_to_remove:  
            graph.remove_nodes_from(nodes_to_remove)  
            simplified = True 
    
    graph = relabel_graphs(graph)
      
    return graph


def extract_topo_graph(graph):
    topo_graph = nx.Graph()
    for node in graph.nodes():
        topo_graph.add_node(node, pos = (graph.nodes[node]["o"][1],graph.nodes[node]["o"][0]))
    for edge in graph.edges():
        topo_graph.add_edge(edge[0], edge[1], length = graph.edges[edge]["length"])
    return topo_graph

def build_graph_from_ske(polys):
    node_num = 0
    ograph = nx.Graph()
    for l in polys:
        ograph.add_node(node_num, pos=(l[0][0],l[0][1]))
        for i in range(0,len(l)-1):
            ograph.add_node(node_num+1, pos=(l[i+1][0],l[i+1][1]))
            ograph.add_edge(node_num, node_num+1, length = get_distance((l[i][0],l[i][1]), (l[i+1][0],l[i+1][1])))
            node_num += 1
        node_num += 1
        #     cv2.line(img2,(l[i][0],l[i][1]),(l[i+1][0],l[i+1][1]),color=(255,0,0))  
    from collections import defaultdict
    # remove nodes that share the same pos
    pos_to_nodes = defaultdict(list)  
    for node, data in ograph.nodes(data=True):  
        pos = data.get('pos')  
        if pos is not None:  
            pos_to_nodes[tuple(pos)].append(node)  
      
    # for each pos group, keep one representative node
    for pos, nodes in pos_to_nodes.items():  
        if len(nodes) > 1:  # multiple nodes share this pos
            representative = nodes[0]  # keep the first as representative
            for node in nodes[1:]:  # remaining nodes
                # reconnect their neighbors to the representative
                for neighbor in ograph.neighbors(node):  
                    if neighbor not in nodes:  # avoid self-loops
                        ograph.add_edge(representative, neighbor, \
                                        length = get_distance(ograph.nodes[representative]["pos"], ograph.nodes[neighbor]["pos"]))  
                # drop the duplicate node
                ograph.remove_node(node)  
    

    return ograph

if __name__ == "__main__":
    inputdir = "./demo_input/zones_png"
    outputdir = "./demo_output/topo_nx"
    for filename in os.listdir(inputdir):
        scene_name = filename.split("/")[-1].split(".")[-2]
        if scene_name not in ["012", "013", "014", "015"]: continue
        if not scene_name.isdigit() : continue
        print(f"********processing {scene_name}...**************")

        img = cv2.imread(os.path.join(inputdir, scene_name+".png"))
        
        # plt.imshow(img, cmap='gray')
        # print(img.shape)

        ske = skeletonize(img).astype(np.uint16) 
        # cv2.imshow("ske",ske* 255)
        # cv2.waitKey(0)
        
        ograph = build_sknw(ske, iso=False, ring=False, full=True)
        largest = max(nx.connected_components(ograph))
        graph = ograph.subgraph(largest)


        nx.write_gpickle(graph, os.path.join(outputdir, f"{scene_name}_graph.gpickle"))

        topo_graph = extract_topo_graph(graph)
        topo_graph = merge_nodes(topo_graph)
        nx.write_gpickle(topo_graph, os.path.join(outputdir, f"{scene_name}_topograph.gpickle"))
        pos = nx.get_node_attributes(topo_graph, 'pos')
        plt.title(f"Topology Graph (vis) {scene_name}")
        nx.draw(topo_graph, pos, with_labels=False, node_size=40)
        # plt.show()
        plt.savefig(os.path.join(inputdir, scene_name+"_topoviz.png"))
        plt.cla()

        plt.title(f"Topology Graph {scene_name}")
        pos = nx.kamada_kawai_layout(topo_graph,scale=2)
        nx.draw(topo_graph, pos, with_labels=False, node_size=80)#, node_size=6, width = 2, edge_color = 'lightblue', node_color = 'red')
        #plt.show()
        plt.savefig(os.path.join(inputdir, scene_name+"_topo.png"))
        plt.cla()
        
        # extract road-layout graph
        # reduce intermediate nodes on edges
        reduced_graph = simplify_graph(graph)
        # merge disconnected nodes
        layout_graph = merge_nodes(reduced_graph)
        nx.write_gpickle(layout_graph, os.path.join(outputdir, f"{scene_name}_layout.gpickle"))
        pos = nx.get_node_attributes(layout_graph, 'pos')
        plt.title(f"Layout Graph {scene_name}")
        nx.draw(layout_graph, pos, with_labels=False, node_size=6, width = 2, edge_color = 'lightblue', node_color = 'red')
        #plt.show()
        plt.savefig(os.path.join(inputdir, scene_name+"_layout.png"))
        plt.cla()

    



import networkx as nx
import matplotlib.pyplot as plt
import random
from edge_construction import *
import pandas as pd
import os
import pyproj

def generate_s_graph(deltaxy = 0.0002, board_size = 8):
    graph = nx.Graph()
    # Define origin coordinates
    origin_x = 120.12205
    origin_y = 30.27306

    numi = 0
    # Create board nodes (S-shaped numbering)
    for i in range(board_size):
        if i%2 == 0 : j_list = range(0,board_size,1)
        else: j_list = range(board_size-1,-1,-1)
        for j in j_list:
            # Compute node coordinates
            x = origin_x + i*deltaxy
            y = origin_y + j*deltaxy
            # Add node to graph
            graph.add_node(numi, pos = (x,y))
            numi += 1
    for i in range(numi-1):
        graph.add_edge(i,i+1)
    # Add extra edges
    graph.add_edges_from([(3,12),(12,19),(27,36),(44,51),(51,60)])
    return graph

def generate_c0812_graph(deltaxy = 0.0002, board_size = 6):
    graph = nx.Graph()
    # Define origin coordinates
    origin_x = 120.12205
    origin_y = 30.27306

    numi = 0
    # Create board nodes (bottom-to-top sequential numbering)
    for i in range(board_size):
        for j in range(board_size):
            # Compute node coordinates
            x = origin_x + i*deltaxy
            y = origin_y + j*deltaxy
            # Add node to graph
            graph.add_node(numi, pos = (x,y))
            numi += 1
    # Connect nodes into a grid
    nodes_list1 = [(0,1),(1,2),(2,9),(9,16),(16,15),(15,14),(14,7),(7,0),(1,8),(8,15),(9,8),(8,7)]
    nodes_list2 = []
    for node in nodes_list1:
        nodes_list2.append((node[0]+32, node[1]+32))
    graph.add_edges_from(nodes_list1)
    graph.add_edges_from(nodes_list2)
    nodes_list3 = []
    for i in range(3,45,7):
        nodes_list3.append((i,i+7))
    graph.add_edges_from(nodes_list3)
    graph.add_edges_from([(2,3),(45,46)])
    nodes_list4 = []
    for i in range(21,27):
        nodes_list4.append((i,i+1))
    graph.add_edges_from(nodes_list4)
    graph.add_edges_from([(27,34),(14,21)])
    # Remove isolated (degree-0) nodes
    degrees = graph.degree()
    nodes_to_remove = [node for node, degree in degrees if degree == 0]
    graph.remove_nodes_from(nodes_to_remove)
    return graph

def generate_X_graph(deltaxy = 0.0002, board_size = 6):
    graph = nx.Graph()
    # Define origin coordinates
    origin_x = 120.12205
    origin_y = 30.27306

    numi = 0
    # Create board nodes (bottom-to-top sequential numbering)
    for i in range(board_size+2):
        for j in range(board_size):
            # Compute node coordinates
            x = origin_x + i*deltaxy
            y = origin_y + j*deltaxy
            # Add node to graph
            graph.add_node(numi, pos = (x,y))
            numi += 1
    # Connect nodes into a grid
    nodelist = []
    for i in range(0,5):
        nodelist.append((i,i+1))
    for i in range(5,47,6):
        nodelist.append((i,i+6))
    for i in range(42,47):
        nodelist.append((i,i+1))
    for i in range(0,42,6):
        nodelist.append((i,i+6))
    # for i in range(18,23):
    #     nodelist.append((i,i+1))
    for i in range(7,10):
        nodelist.append((i,i+1))
    for i in range(38,41):
        nodelist.append((i,i+1))
    for i in range(31,34):
        nodelist.append((i,i+1))
    graph.add_edges_from(nodelist)
    nodelist2 = [(1,7),(7,13),(13,14),(14,20),(20,26),(26,25),(25,31),(34,40),(38,44),(10,16),(16,22),(22,23),(24,25)]
    graph.add_edges_from(nodelist2)
    # Remove isolated (degree-0) nodes
    degrees = graph.degree()
    nodes_to_remove = [node for node, degree in degrees if degree == 0]
    graph.remove_nodes_from(nodes_to_remove)
    return graph

def random_generate_graph(remove_ratio, deltaxy = 0.0002 ,board_size = 8):
    graph = nx.Graph()
    # Define origin coordinates
    origin_x = 120.12205
    origin_y = 30.27306

    numi = 0
    # Create board nodes (bottom-to-top sequential numbering)
    for i in range(board_size):
        for j in range(board_size):
            # Compute node coordinates
            x = origin_x + i*deltaxy
            y = origin_y + j*deltaxy
            # Add node to graph
            graph.add_node(numi, pos = (x,y))
            numi += 1
    # Connect nodes into a grid
    for i in range(8):
        for j in range(8):
            if j != 7: graph.add_edge(i+j*8,i+(j+1)*8) # connect right
            if i != 7 : graph.add_edge(i+j*8,i+j*8 + 1) # connect up

    # Randomly remove some edges
    edges = list(graph.edges())
    random.shuffle(edges)
    num_edges_to_remove = int(len(edges) * remove_ratio)
    edges_to_remove = edges[:num_edges_to_remove]
    graph.remove_edges_from(edges_to_remove)

    # # Remove isolated (degree-0) nodes
    # degrees = graph.degree()
    # nodes_to_remove = [node for node, degree in degrees if degree == 0]
    # graph.remove_nodes_from(nodes_to_remove)
    
    # Keep the largest connected component
    components = nx.connected_components(graph)
    max_graph = graph.subgraph(max(components, key=len))

    max_graph = nx.minimum_spanning_tree(max_graph)
    return max_graph


def sample_from_edges(G, sample_dis):
    # Sample points along each edge
    sampled_points = set()
    for u, v in G.edges():
        edge_points = []
        # Get node coordinates
        pos_u = G.nodes[u]['pos']
        pos_v = G.nodes[v]['pos']
        # Compute edge length
        edge_length = ((pos_u[0] - pos_v[0])**2 + (pos_u[1] - pos_v[1])**2)**0.5
        # Compute number of sample points
        num_samples = int(edge_length / sample_dis)
        for i in range(num_samples + 1):
            # Compute sample point position
            t = i / num_samples
            x = [pos_u[dim] * (1 - t) + pos_v[dim] * t for dim in range(len(pos_u))]
            # Add sample point on the edge
            sampled_points.add(tuple(x))
    return list(sampled_points)

def remove_edges(graph, edges):
    for edge in edges:
        graph.remove_edge(*edge)

def remove_sharp_neighbors(graph, path, unvisited_neighbors):
    if len(path) == 1: return unvisited_neighbors
    p1 = graph.nodes[path[len(path)-2]]["pos"]
    p2 = graph.nodes[path[len(path)-1]]["pos"]
    candidate_neighbors = []
    for node in unvisited_neighbors:
        angle = calculate_angle(p1,p2,graph.nodes[node]["pos"])
        if angle > 120:
            candidate_neighbors.append(node)
    return candidate_neighbors

def random_walk(graph):
    path_list = []
    edge_list = []

    edges = []
    while len(graph.edges) > 0:
        degree_nodes = [node for node in graph.nodes if graph.degree[node] == 1]
        if len(degree_nodes) == 0: 
            degree_nodes = [node for node in graph.nodes if graph.degree[node] == 2]
        if len(degree_nodes)== 0:
            break
        start_node = random.choice(degree_nodes)
        path = [start_node]
        visited_nodes = set()
        visited_nodes.add(start_node)
        while True:
            neighbors = list(graph.neighbors(start_node))
            unvisited_neighbors = [neighbor for neighbor in neighbors if neighbor not in visited_nodes]
            candicate_neighbors = remove_sharp_neighbors(graph, path, unvisited_neighbors)
            if len(candicate_neighbors) == 0:
                break
            next_node = random.choice(candicate_neighbors)
            edges.append((start_node, next_node))
            path.append(next_node)
            visited_nodes.add(next_node)
            start_node = next_node
        remove_edges(graph, edges)
        path_list.append(path)
        edge_list.append(edges)

        edges = []
    return path_list, edge_list

def main_generate_topo_graph(deltaxy, board_size, outputdir,cur_scene_name, mode = "random", remove_ratio = 0.4):
    ##################### Build topology graph #################################
    if mode == "random":
        graph = random_generate_graph(remove_ratio, deltaxy, board_size)
    elif mode == "S":
        graph = generate_s_graph(deltaxy, board_size) # regular grid
    elif mode == "X":
        graph = generate_X_graph(deltaxy, board_size)
    else:
        print("mode is illegal")
        raise NotImplementedError
    
    # Compute node degrees
    degrees = graph.degree()
    deg4 = [node for node, degree in degrees if degree == 4]
    deg3 = [node for node, degree in degrees if degree == 3]
    plt.title(f"{cur_scene_name} #deg(4)={len(deg4)} #deg(3) = {len(deg3)}")
    # Visualize
    pos = nx.get_node_attributes(graph, 'pos')
    nx.draw(graph,pos,with_labels=False, node_size=20)
    plt.savefig(os.path.join(outputdir,"midimg",f"0_{cur_scene_name}_original_topo.png"), dpi=300)
    plt.show()
    plt.cla()
    return graph

def main_keypoints2graph(points,outputdir,cur_scene_name):
    # Visualize original nodes
    G = nx.Graph()
    for i, (x, y) in enumerate(points):
        G.add_node(i,pos=(x,y))
    pos = nx.get_node_attributes(G, 'pos')
    nx.draw(G, pos, with_labels=False, node_size=6, width = 2, edge_color = 'green', node_color = 'red')
    plt.savefig(os.path.join(outputdir,"midimg",f"1_{cur_scene_name}_keypoints.png"), dpi=300)
    plt.show()
    
    ####################### Connect keypoints into a graph #################################
    MST = connect_graph_nodes(points)
    print("*******MST constructed********")
    MST = connect_degree_1(MST, 1.2*sample_dis) # search neighbors for degree-1 nodes
    print("*******Edge added********")
    MST = remove_long_edges(MST, 1.2*sample_dis)
    print("*******long edge removed********")
    # Visualize result
    pos = nx.get_node_attributes(MST, 'pos')
    nx.draw(MST, pos, with_labels=False, node_size=6, width = 2, edge_color = 'green', node_color = 'red')
    plt.savefig(os.path.join(outputdir,"midimg",f"2_{cur_scene_name}_reconnected.png"), dpi=300)
    plt.show()
    ####################### Simplify the reconnection graph #################################
    sim_graph = simplify_graph(MST)
    print("*******graph simplified********")
    pos = nx.get_node_attributes(sim_graph, 'pos')
    nx.draw(sim_graph, pos, with_labels=False, node_size=6, width = 2, edge_color = 'green', node_color = 'red')
    plt.savefig(os.path.join(outputdir,"midimg",f"3_{cur_scene_name}_simplified.png"), dpi=300)
    plt.show()
    return MST, sim_graph # return graphs before and after simplification


def main_partition2csv(sim_graph,outputdir,cur_scene_name):
    ####################### Partition topology into numbered roads #################################
    # Relabel nodes
    nodelist = sim_graph.nodes()
    mapping = {old_label:new_label for new_label, old_label in enumerate(nodelist)}
    labeled_graph = nx.relabel_nodes(sim_graph, mapping)
    # Random-walk partition and visualize edges visited in each round
    path_list, edge_list = random_walk(labeled_graph)
    pos = nx.get_node_attributes(labeled_graph, 'pos')
    nx.draw(labeled_graph, pos, with_labels=False, node_color='lightblue', node_size=20)
    for i,edges in enumerate(edge_list):
        print(i,edges)
        nx.draw_networkx_edges(labeled_graph, pos ,edgelist=edges, edge_color=f'C{i}', width=2)
    plt.axis('off')
    os.makedirs(os.path.join(outputdir,"midimg"),exist_ok=True)
    plt.savefig(os.path.join(outputdir,"midimg",f"4_{cur_scene_name}_partition.png"), dpi=300)
    plt.show()
    plt.cla()
    ####################### Write CSV files #################################
    roadlist = []
    attrlist = []
    for i,nodes in enumerate(path_list):
        attrlist.append([i,i,"tertiary"])
        for node in nodes:
            lon, lat = labeled_graph.nodes()[node]["pos"][0], labeled_graph.nodes()[node]["pos"][1]
            roadlist.append([node, lon, lat, i])
    roads = pd.DataFrame(roadlist, columns=["id","lon","lat","group_id"])
    os.makedirs(os.path.join(outputdir,"csv"), exist_ok=True)
    roads.to_csv(os.path.join(outputdir,"csv",f'{cur_scene_name}_roads.csv'), index=False)
    attributes = pd.DataFrame(attrlist, columns=["id","group_id","attribute"])
    attributes.to_csv(os.path.join(outputdir,"csv",f'{cur_scene_name}_attributes.csv'), index=False)
    print(f'{cur_scene_name} csv written')
    return labeled_graph

def convert_to_120_30(graph):
    origin_x = 120.12205
    origin_y = 30.27306
    for node in graph.nodes:
        cur_pos_x = graph.nodes[node]["pos"][0]
        cur_pos_y = graph.nodes[node]["pos"][1]
        graph.nodes[node]["pos"] = (cur_pos_x/100000 + origin_x, cur_pos_y/100000 + origin_y)
    return graph

if __name__ == "__main__":
    # # Output path
    # outputdir = "./demo"
    # filetype = ["midimg", "csv", "osm", "xodr", "proj"]
    # for ft in filetype:
    #     _cur_path = os.path.join(outputdir, ft)
    #     if os.path.exists(_cur_path): continue
    #     os.makedirs(_cur_path)
    
    # # num_samples = 30
    # # for i in range(num_samples): # multiple scenes
    # #     if i < num_samples/3 : remove_ratio = 0.2
    # #     elif i < num_samples*2/3 : remove_ratio = 0.3
    # #     else : remove_ratio = 0.4
    # #     cur_scene_name = f"custom{i}"
    # #     deltaxy = 200/100000 # ~200 m per node
    # #     board_size = 8 # 8 nodes, 7 cells; extent is 200*7 m, i.e. 1.4*1.4 km2
    # #     graph = main_generate_topo_graph(deltaxy, board_size, outputdir,cur_scene_name, mode = "random", remove_ratio = remove_ratio )


    # #     # ########################## From keypoints to final CSV ######################
    # #     # # Sample topology graph into keypoints
    # #     # sample_dis = deltaxy/10
    # #     # points = sample_from_edges(graph, sample_dis)
    # #     # if len(points) > 5000: continue
    # #     # MST, sim_graph = main_keypoints2graph(points,outputdir,cur_scene_name)
    # #     # labeled_graph =  main_partition2csv(sim_graph,outputdir,cur_scene_name)
    # #     ########################## From a random topology graph to final CSV ######################
    # #     labeled_graph =  main_partition2csv(graph,outputdir,cur_scene_name)
    
    
    
    # # # Option 2: compute MST first to reduce intersections
    # # remove_ratio = 0.2
    # # for i in range(30,40): # multiple scenes
    # #     cur_scene_name = f"custom{i}"
    # #     deltaxy = 200/100000 # ~200 m per node
    # #     board_size = 8 # 8 nodes, 7 cells; extent is 200*7 m, i.e. 1.4*1.4 km2
    # #     graph = main_generate_topo_graph(deltaxy, board_size, outputdir,cur_scene_name, mode = "random", remove_ratio = remove_ratio )
    # #     labeled_graph =  main_partition2csv(graph,outputdir,cur_scene_name)
    # cur_scene_name = f"customX"
    # deltaxy = 200/100000 # ~200 m per node
    # board_size = 6 # 4 nodes, 3 cells; extent is 200*3 m, i.e. 0.6*0.6 km2
    # graph = main_generate_topo_graph(deltaxy, board_size, outputdir,cur_scene_name, mode = "X")
    # sim_graph = simplify_graph(graph)
    # labeled_graph =  main_partition2csv(sim_graph,outputdir,cur_scene_name)
    
    # ### 20231017
    # inputgraph = "./../data_preperation/demo_output/topo_nx/002_layout.gpickle"
    # cur_scene_name = "002"
    # outputdir = "./../data_preperation/demo_output/topo_csv/"
    # graph = nx.read_gpickle(inputgraph)
    # graph = convert_to_120_30(graph)  # Shift by origin. Watch pixel-to-metric scale. TODO
    # labeled_graph =  main_partition2csv(graph,outputdir,cur_scene_name)

    ### 20240123
    # graph_dir = r"./data/data_road_generation/pics_vis/visualization/select"
    # outputdir = r"./data/data_road_generation/pics_vis/visualization/select/out"
    graph_dir = r"./data/samples/topo"
    outputdir = r"./data/samples/topo_vis"
    graphs = os.listdir(graph_dir)
    
    for idx, inputgraph in enumerate(graphs):
        # if not inputgraph.endswith("5.gpickle"): continue
        if inputgraph.endswith(".gpickle"):
            cur_scene_name = str(idx)
            import pickle
            with open(os.path.join(graph_dir,inputgraph),'rb') as f:
                graph = pickle.load(f)
            # graph = nx.read_gpickle(os.path.join(graph_dir,inputgraph))
            graph = convert_to_120_30(graph)  # Shift by origin. Watch pixel-to-metric scale. TODO
            labeled_graph =  main_partition2csv(graph,outputdir,cur_scene_name)



        






import networkx as nx
import numpy as np
import os
from matplotlib import pyplot as plt
import cv2

class Orgraph:
    def __init__(self, graph):
        self.graph = graph
        self.num_edges = self.graph.number_of_edges()
        self.num_nodes = self.graph.number_of_nodes()
        
    def cal_road_density(self, img_path):
        img = cv2.imread(img_path)
        area = img.shape[0] * img.shape[1]
        length_list = []
        for edge in self.graph.edges:
            length_list.append(self.graph.edges[edge]["weight"])
        road_length = sum(length_list)
        return road_length/area
    def cal_accessibility(self):
        length_list = []
        for idx1 in range(self.num_nodes-1):
            cur_node_length = []
            for idx2 in range(idx1+1, self.num_nodes):
                path_length = nx.shortest_path_length(self.graph, list(self.graph.nodes)[idx1], list(self.graph.nodes)[idx2], weight="weight")
                #print(path_length)
                cur_node_length.append(path_length)
            length_list.append(np.mean(cur_node_length))
        avg_length = np.mean(length_list)
        return 100/avg_length
    
class Topograph:
    def __init__(self, graph):
        self.graph = graph
        self.num_edges = self.graph.number_of_edges()
        self.num_nodes = self.graph.number_of_nodes()
    def cal_degree(self):
        degree_list = []
        for node in self.graph.nodes:
            degree_list.append(self.graph.degree(node))
        avg_degree = np.mean(degree_list)
        return degree_list, avg_degree
    def cal_net_density(self):
        return 2*self.num_edges / (self.num_nodes * (self.num_nodes - 1) )
    def cal_cluster_factor(self):
        cluster_list = []
        for node in self.graph.nodes:
            cluster_list.append(nx.clustering(self.graph, node))
        avg_cluster = nx.average_clustering(self.graph)
        return cluster_list, avg_cluster
    def cal_topo_depth(self):
        depth_list = []
        for idx1 in range(self.num_nodes-1):
            cur_node_depth = []
            for idx2 in range(idx1+1, self.num_nodes):
                # if not nx.has_path(self.graph, list(self.graph.nodes)[idx1], list(self.graph.nodes)[idx2]): 
                #     cur_node_depth.append(0)
                #     continue
                short_path_length = nx.shortest_path_length(self.graph, list(self.graph.nodes)[idx1], list(self.graph.nodes)[idx2])
                cur_node_depth.append(short_path_length)
            depth_list.append(np.mean(cur_node_depth))
        avg_depth = np.mean(depth_list)
        return depth_list, avg_depth

if __name__ == "__main__":
    inputdir = "./demo_output/topo_nx"
    scene_name = "015"
    graph = nx.read_gpickle(os.path.join(inputdir,f"{scene_name}_graph.gpickle"))
    cal_orgraph = Orgraph(graph)
    road_density = cal_orgraph.cal_road_density(os.path.join("./demo_input/zones_png",f"{scene_name}.png"))
    print("road density", road_density*1000)

    accesibility = cal_orgraph.cal_accessibility()
    print("accesibility", accesibility)

    topo_graph = nx.read_gpickle(os.path.join(inputdir,f"{scene_name}_topograph.gpickle"))
    # topo_graph.remove_nodes_from([node for node in topo_graph.nodes if topo_graph.degree(node) == 1])
    pos = nx.get_node_attributes(topo_graph, 'pos')
    plt.title(f"Topology Graph (vis) {scene_name}")
    nx.draw(topo_graph, pos, with_labels=False, node_size=40)
    # plt.show()

    cal_topograph = Topograph(topo_graph)
    degree_list, avg_degree = cal_topograph.cal_degree()
    print("degree", degree_list, avg_degree)
    # plt.hist(degree_list)
    # plt.title("node degree")
    # plt.xlabel("degree")
    # plt.ylabel("frequency")
    # plt.show()



    net_density = cal_topograph.cal_net_density()


    print("net density", net_density)
    # cluster_list, avg_cluster = cal_topograph.cal_cluster_factor()
    # print("cluster", cluster_list, avg_cluster)
    depth_list, avg_depth = cal_topograph.cal_topo_depth()
    print("avg_depth", avg_depth)




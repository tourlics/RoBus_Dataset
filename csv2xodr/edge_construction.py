import geopandas as gpd
import networkx as nx
import momepy
import matplotlib.pyplot as plt
from shapely.geometry import LineString
from scipy import spatial
import math
import numpy as np

def trans_momepy(inputfile):
    # Only endpoints of a road are keypoints
    roads = gpd.read_file(inputfile)
    G = momepy.gdf_to_nx(roads, approach="primal")
    pos = {n: [n[0], n[1]] for n in list(G.nodes)}
    # plt.title("Topo Graph")
    # nx.draw(G, pos, with_labels=False, node_size=6, width = 2, edge_color = 'green', node_color = 'red')
    # plt.show()

def trans_custom(inputfile):
    # Every vertex in a LineString is a keypoint
    gdf = gpd.read_file(inputfile)
    geolines = []

    for j in range(0, len(gdf) ):
        geo = gdf.geometry[j] # get geometry (GeoSeries)
        geolines.append(geo)

    # Create an empty NetworkX graph
    graph = nx.Graph()

    points = []
    # Iterate over each LineString
    for geo in geolines:
        # Iterate over each point in the LineString
        for i, point in enumerate(geo.coords):
            # Add node to the graph
            graph.add_node(point)
            points.append(point)

            # Add edge to the previous point in the LineString (if it exists)
            if i > 0:
                previous_point = geo.coords[i - 1]
                graph.add_edge(previous_point, point)
    return graph, points


def sample_points(line, distance):
    sampled_points = []
    total_length = line.length

    distance_along_line = 0.0
    while distance_along_line < total_length:
        point = line.interpolate(distance_along_line)
        sampled_points.append((point.x, point.y))
        distance_along_line += distance

    return sampled_points

def points_from_line(inputfile, sample_dis):
    # Every vertex in a LineString is a keypoint
    gdf = gpd.read_file(inputfile)
    geolines = []

    for j in range(0, len(gdf) ):
        geo = gdf.geometry[j] # get geometry (GeoSeries)
        geolines.append(geo)
    
    points = []
    # Iterate over each LineString
    for geo in geolines:
        sampled_points = sample_points(geo, sample_dis)
        for point in sampled_points:
            points.append(point)
    return points


def connect_graph_nodes(points):
    # Create an undirected graph
    G = nx.Graph()
    # Add nodes
    for i, (x, y) in enumerate(points):
        G.add_node(i,pos=(x,y))
    # Compute pairwise distances and add edges
    for i in range(len(points)):
        for j in range(i+1, len(points)):
            x1, y1 = points[i]
            x2, y2 = points[j]
            distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5  # Euclidean distance
            G.add_edge(i, j, weight=distance)

    # Compute minimum spanning tree
    MST = nx.minimum_spanning_tree(G)
    return MST

def remove_long_edges(graph, max_length):
    edges_to_remove = []
    for edge in graph.edges():
        length = graph.edges[edge]['weight']
        if length > max_length:
            edges_to_remove.append(edge)
    
    graph.remove_edges_from(edges_to_remove)
    return graph

def connect_degree_1(graph, thre):
    degree_one_nodes = [node for node in graph.nodes() if graph.degree[node] == 1]
    for i in range(len(degree_one_nodes)):
        for j in range(i+1, len(degree_one_nodes)):
            node1 = degree_one_nodes[i]
            node2 = degree_one_nodes[j]
            dis = spatial.distance.euclidean(graph.nodes[node1]['pos'], graph.nodes[node2]['pos'])
            if dis < thre:
                graph.add_edge(node1, node2, weight = dis)
    return graph

def calculate_angle(p1, p2, p3):
    """Calculate the angle between three points."""
    vector1 = np.array(p1) - np.array(p2)
    vector2 = np.array(p3) - np.array(p2)
    unit_vector1 = vector1 / np.linalg.norm(vector1)
    unit_vector2 = vector2 / np.linalg.norm(vector2)
    dot_product = np.dot(unit_vector1, unit_vector2)
    if dot_product < -1: dot_product = -1
    if dot_product > 1 : dot_product = 1
    angle = np.arccos(dot_product)
    angle = np.degrees(angle)
    # try:
    #     angle = math.degrees(math.acos((a**2 + b**2 - c**2) / (2 * a * b)))
    # except:
    #     print((a**2 + b**2 - c**2) , (2 * a * b) , p1, p2, p3)
    #     tg = nx.Graph()
    #     tg.add_node(1, pos = p1)
    #     tg.add_node(2, pos = p2)
    #     tg.add_node(3, pos = p3)
    #     tg.add_edge(1,2)
    #     tg.add_edge(2,3)
    #     pos = nx.get_node_attributes(tg, 'pos')
    #     nx.draw(tg, pos, with_labels=True, node_size=6, width = 2, edge_color = 'green', node_color = 'red')
    #     plt.show()
    return angle

def simplify_graph(G):
    # Simplify the graph
    while True:
        nodes_to_remove = []
        for node in G.nodes:
            if len(list(G.adj[node])) == 2: # only process degree-2 nodes
                edge1, edge2 = G.edges(node)
                pos1 = G.nodes[edge1[0]]['pos'] if edge1[0] != node else G.nodes[edge1[1]]['pos']
                pos2 = G.nodes[edge2[0]]['pos'] if edge2[0] != node else G.nodes[edge2[1]]['pos']
                angle = calculate_angle(pos1, G.nodes[node]['pos'], pos2)
                if angle > 177:
                    nodes_to_remove.append(node)
                    G.remove_node(node)
                    G.add_edge(edge1[1] if edge1[0] == node else edge1[0], edge2[1] if edge2[0] == node else edge2[0])
                    break
        if not nodes_to_remove:
            break
    return G

if __name__ == "__main__":
    inputfile = "./demo_output/osmnx_geojson_roads/yuquan/residential.geojson"
    # graph, points = trans_custom(inputfile)
    # # Visualize result
    # pos = {n: [n[0], n[1]] for n in list(graph.nodes)}
    # nx.draw(graph, pos, with_labels=False, node_size=6, width = 2, edge_color = 'green', node_color = 'red')
    # plt.show()
    sample_dis = 0.00002
    points = points_from_line(inputfile, sample_dis)
    print(len(points))
    if len(points) < 5000: 
        MST = connect_graph_nodes(points)
        print("*******MST constructed********")
        MST = connect_degree_1(MST, 1.2*sample_dis) # search neighbors for degree-1 nodes
        print("*******Edge added********")
        MST = remove_long_edges(MST, 1.2*sample_dis)
        print("*******long edge removed********")
        # # Visualize result
        # pos = nx.get_node_attributes(MST, 'pos')
        # nx.draw(MST, pos, with_labels=False, node_size=6, width = 2, edge_color = 'green', node_color = 'red')
        # plt.show()

        sim_graph = simplify_graph(MST)
        print("*******graph simplified********")
        pos = nx.get_node_attributes(sim_graph, 'pos')
        nx.draw(sim_graph, pos, with_labels=False, node_size=6, width = 2, edge_color = 'green', node_color = 'red')
        plt.show()


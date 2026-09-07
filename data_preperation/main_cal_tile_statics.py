import rasterio
import numpy as np
import os
import json
# from sklearn.cluster import KMeans  
import matplotlib.pyplot as plt 
from tqdm import tqdm
from shapely.geometry import Polygon
from scripts.vec2raster import CRStrans
import geopandas as gpd

import networkx as nx
import osmnx as ox
from scripts.calculate_network import Topograph
import scipy
from scripts.extract_topo_layout import get_distance
from scripts.visualization import vis_metric_bins_from_npy, \
    vis_metric_bins_from_npy_clamp, vis_stacked_bins_from_npy, vis_pie_from_npy_for_cls,\
    vis_stacked_bins_from_npy_clamp

class ImageOrientation():
    def add_edge_bearings(self, G, precision=1):
        # extract edge IDs and corresponding coordinates from their nodes
        uvk = [(u, v) for u, v in G.edges if u != v]
        x = G.nodes(data="x")
        y = G.nodes(data="y")
        coords = np.array([(y[u], x[u], y[v], x[v]) for u, v in uvk])

        # calculate bearings then set as edge attributes
        bearings = ox.bearing.calculate_bearing(coords[:, 0], coords[:, 1], coords[:, 2], coords[:, 3])
        values = zip(uvk, bearings.round(precision))
        nx.set_edge_attributes(G, dict(values), name="bearing")

        return G

    def _extract_edge_bearings(self, Gu, min_length=0, weight=None):
        bearings = []
        for u, v, data in Gu.edges(data=True):
            # ignore self-loops and any edges below min_length
            if u != v and data["length"] >= min_length:
                if weight:
                    # weight edges' bearings by some edge attribute value
                    bearings.extend([data["bearing"]] * int(data[weight]))
                else:
                    # don't weight bearings, just take one value per edge
                    bearings.append(data["bearing"])

        # drop any nulls, calculate reverse bearings, concatenate and return
        bearings = np.array(bearings)
        bearings = bearings[~np.isnan(bearings)]
        bearings_r = (bearings - 180) % 360
        return np.concatenate([bearings, bearings_r])

    def _bearings_distribution(self, Gu, num_bins, min_length=0, weight=None):
        n = num_bins * 2
        bins = np.arange(n + 1) * 360 / n

        bearings = self._extract_edge_bearings(Gu, min_length, weight)
        count, bin_edges = np.histogram(bearings, bins=bins)

        # move last bin to front, so eg 0.01 degrees and 359.99 degrees will be
        # binned together
        count = np.roll(count, 1)
        bin_counts = count[::2] + count[1::2]

        # because we merged the bins, their edges are now only every other one
        bin_edges = bin_edges[range(0, len(bin_edges), 2)]
        return bin_counts, bin_edges
    
    
    def orientation_entropy(self, Gu, num_bins=36, min_length=0, weight=None):
        bin_counts, _ = self._bearings_distribution(Gu, num_bins=36, min_length=0, weight=None)
        return scipy.stats.entropy(bin_counts)
    
class GraphMetrics(Topograph):
    def __init__(self, graph):
        super().__init__(graph)
        self.graph = graph
        self.infvalue = 512*2 # Twice the image resolution
    def covert_graph_ox(self, graph):
        
        graph_ox = nx.Graph()
        for node in graph.nodes():
            if self.graph.nodes[node].get("pos", None) is None: continue #TODO
            graph_ox.add_node(node, x = graph.nodes[node]["pos"][1], y = graph.nodes[node]["pos"][0])
        for edge in graph.edges():
            if self.graph.nodes[edge[0]].get("pos", None) is None: continue #TODO
            if self.graph.nodes[edge[1]].get("pos", None) is None: continue #TODO
            graph_ox.add_edge(edge[0], edge[1], length=get_distance(graph.nodes[edge[0]]["pos"],graph.nodes[edge[1]]["pos"] ))
        return graph_ox
    
    def road_accessibility(self):
        length_list = []
        for idx1 in range(self.num_nodes-1):
            cur_node_length = []
            for idx2 in range(idx1+1, self.num_nodes):
                try:
                    path_length = nx.shortest_path_length(self.graph, idx1, idx2, weight="length")
                except Exception as e:
                    #print(e)
                    path_length = self.infvalue
                #print(path_length)
                cur_node_length.append(path_length)
            length_list.append(np.mean(cur_node_length))
        avg_length = np.mean(length_list)
        return 100/avg_length
    
    def traffic_convenience(self):
        tc_list = []
        for idx1 in range(self.num_nodes-1):
            if self.graph.nodes[idx1].get("pos", None) is None: continue #TODO
            for idx2 in range(idx1+1, self.num_nodes):
                # print(self.num_nodes, idx2, self.graph.nodes[idx2])
                if self.graph.nodes[idx2].get("pos", None) is None: continue #TODO
                eular_distance = get_distance(self.graph.nodes[idx1]["pos"], self.graph.nodes[idx2]["pos"])
                if eular_distance < 60: # 5m*60pixel=300m
                    continue
                if not nx.has_path(self.graph, idx1, idx2):
                    path_length = self.infvalue
                    continue
                else:
                    path_length = nx.shortest_path_length(self.graph, idx1, idx2, weight="length")
                tc_list.append(eular_distance/path_length)
                # break
        if len(tc_list) == 0: tc = 0
        else: tc = np.mean(tc_list)        
        return tc
    
    def road_orientation(self):
        imageort = ImageOrientation()
        graph_ox = self.covert_graph_ox(self.graph)
        Gu = imageort.add_edge_bearings(graph_ox)
        orientation = imageort.orientation_entropy(Gu)

        Gu.graph["crs"] = 'EPSG:4326'
        fig, ax = ox.plot_orientation(Gu, color="#81b5d5") #"#6A5ACD" color="#7e6ee1"
        plt.show()
        return orientation
    
    def road_order(self):
        orientation = self.road_orientation()
        hg = 1.386
        hmax = 3.854
        order = 1 - ((orientation - hg) / (hmax - hg))**2
        return order
    
    def road_connectivity(self):
        # con = np.mean(self.graph.degree())
        con = np.mean([self.graph.degree[node] for node in self.graph.nodes() if self.graph.degree[node] > 1])
        return con
    
    def intersection_density(self):
        nodes_greater_than_two = [node for node in self.graph.nodes() if self.graph.degree[node] > 2]
        insec = len(nodes_greater_than_two)/self.graph.number_of_nodes()
        return insec
    



def cal_block_buildings(image_path, geojson_path=None):
    # Low-density low-rise, low-density high-rise, high-density low-rise, high-density high-rise, large-footprint low-rise (count-based)
    with rasterio.open(image_path) as src:  
        # Read pixel data  
        building_hgt = src.read(5)
        # Count non-zero pixels  
        building_pixel =  building_hgt[building_hgt>0]
        if len(building_pixel) < 5:
            return 0, 0
        density = len(building_pixel) / (building_hgt.shape[0] * building_hgt.shape[1])
        avg_hgt = np.average(building_pixel)  
        if geojson_path is not None:
            left, bottom, right, top = src.bounds
            geoms = [Polygon(((left, top), (right, top), (right, bottom), (left, bottom)))]
            crstrans = CRStrans()
            crop_poly = crstrans.transhapely(geoms, src_crs=src.crs, dst_crs="EPSG:4326")
            gdf = gpd.read_file(geojson_path) 
            cur_polygons = gdf[gdf.intersects(crop_poly)] 
            num_building = len(cur_polygons)
            return density, avg_hgt, num_building
        else:
            return density, avg_hgt
    

def cal_roads(image_path, topo_path):
    # Road density, orientation order, traffic convenience (circuity), intersection density
    with rasterio.open(image_path) as src:
        road_p1 = src.read(1)
    total_pixels = road_p1.shape[0] * road_p1.shape[1]

    graph = nx.read_gpickle(topo_path)

    edge_weights = []  
    # Iterate over all edges in the graph  
    for edge in graph.edges(data=True):  
        edge_weights.append(graph.edges[edge[0], edge[1]]['length'])   
    total_length = sum(edge_weights)  
    road_density = total_length / total_pixels
    if total_length < 10:
        return road_density, 0, 0, 0

    gmetric = GraphMetrics(graph)
    traffic_convenience = gmetric.traffic_convenience()
    orientation = gmetric.road_orientation()
    # connectivity = gmetric.road_connectivity()
    joint_density = gmetric.intersection_density()

    return road_density, orientation, traffic_convenience, joint_density

# def cluster_by_kmeans(numbers_list, n_clusters, vis=False):
#     numbers_array = np.array(numbers_list).reshape(-1, 1)  
#     kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(numbers_array)  
#     # Get cluster centers and labels  
#     cluster_centers = kmeans.cluster_centers_  
#     labels = kmeans.labels_  
    
#     # Sort by a cluster-center attribute (e.g. the first dimension)  
#     sorted_indices = np.argsort(cluster_centers[:, 0])  
#     sorted_labels = [sorted_indices[label] for label in labels]  
    
#     if vis:
#         plt.scatter(numbers_array, [0] * len(numbers_array), c=labels)  
#         plt.xlabel('Numbers')  
#         plt.ylabel('Cluster Labels')  
#         plt.show()

#     return np.asarray(sorted_labels)

# def make_cluster_label(tile_list):
#     label_dict = {}
#     building_density = []
#     building_height = []
#     road_density = []
#     orientation = []
#     convenience = []
#     joint_density = []

#     for tile in tile_list:
#         building_density.append(tile["building_density"])
#         building_height.append(tile["building_height"])
#         road_density.append(tile["road_density"])
#         orientation.append(tile["orientation"])
#         convenience.append(tile["convenience"])
#         joint_density.append(tile["joint_density"])
    
#     sorted_labels = cluster_by_kmeans(building_density, n_clusters=2)
#     building_density = np.asarray(building_density)
#     label_dict["building_density"] = {
#         "sparse": [np.min(building_density[sorted_labels==0]), np.max(building_density[sorted_labels==0])],
#         "dense": [np.min(building_density[sorted_labels==1]), np.max(building_density[sorted_labels==1])]
#     }

#     sorted_labels = cluster_by_kmeans(building_height, n_clusters=2)
#     building_height = np.asarray(building_height)
#     label_dict["building_height"] = {
#         "low": [np.min(building_height[sorted_labels==0]), np.max(building_height[sorted_labels==0])],
#         "high": [np.min(building_height[sorted_labels==1]), np.max(building_height[sorted_labels==1])]
#     }

#     sorted_labels = cluster_by_kmeans(road_density, n_clusters=2)
#     road_density = np.asarray(road_density)
#     label_dict["road_density"] = {
#         "sparse": [np.min(road_density[sorted_labels==0]), np.max(road_density[sorted_labels==0])],
#         "dense": [np.min(road_density[sorted_labels==1]), np.max(road_density[sorted_labels==1])]
#     }

#     sorted_labels = cluster_by_kmeans(orientation, n_clusters=2)
#     orientation = np.asarray(orientation)
#     label_dict["orientation"] = {
#         "grid": [np.min(orientation[sorted_labels==0]), np.max(orientation[sorted_labels==0])],
#         "random": [np.min(orientation[sorted_labels==1]), np.max(orientation[sorted_labels==1])]
#     }

#     sorted_labels = cluster_by_kmeans(convenience, n_clusters=2)
#     convenience = np.asarray(convenience)
#     label_dict["convenience"] = {
#         "low": [np.min(convenience[sorted_labels==0]), np.max(convenience[sorted_labels==0])],
#         "high": [np.min(convenience[sorted_labels==1]), np.max(convenience[sorted_labels==1])]
#     }
    
#     sorted_labels = cluster_by_kmeans(joint_density, n_clusters=2)
#     joint_density = np.asarray(joint_density)
#     label_dict["convenience"] = {
#         "sparse": [np.min(joint_density[sorted_labels==0]), np.max(joint_density[sorted_labels==0])],
#         "dense": [np.min(joint_density[sorted_labels==1]), np.max(joint_density[sorted_labels==1])]
#     }
    
#     return label_dict


def make_label(tile_list):
    label_dict = {}
    label_dict["building_density"] = {
        "high": [0, 0.10], # right endpoint closed
        "low": [0.10, 1] # left endpoint open
    }

    label_dict["building_height"] = {
        "low-rise": [0, 21],
        "tall": [21,140]
    }

    label_dict["road_density"] = {
        "sparse": [0, 5/200],
        "dense": [5/200,1]
    }

    label_dict["orientation"] = {
        "grid-like": [0, 3],
        "random": [3, 100]
    }

    return label_dict

def main_cal_statics_per_tile():
    dataspace = r"./dataset_roads/Europe"
    image_dir = os.path.join(dataspace, "cropped_images")
    road_topo_dir = os.path.join(dataspace,"topo_simplify")
    statics_dir = os.path.join(dataspace,"statics")
    os.makedirs(statics_dir, exist_ok=True)
    tile_statics_save_path = os.path.join(statics_dir, "tile_statics.json")

    images = os.listdir(image_dir)
    tile_list = []
    
    for image in tqdm(images):
        if not image.endswith(".tif"): continue
        cur_dict = {}
        scene_name = os.path.basename(image).split(".")[0]
        cur_dict["tile_name"] = scene_name

        with rasterio.open(os.path.join(image_dir, f"{scene_name}.tif")) as src:
            waters = src.read(3)
            woods = src.read(4)
        cur_dict["waters"] = len(waters[waters>0])
        cur_dict["grass"] = len(woods[woods>0])

        image_path = os.path.join(image_dir, image)
        road_topo_path = os.path.join(road_topo_dir, f"{scene_name}.gpickle")
        building_density, avg_hgt = cal_block_buildings(image_path)
        cur_dict["building_density"] = float(building_density)
        cur_dict["building_height"] = float(avg_hgt)
        # cur_dict["building_count"] = int(num_building)

        road_density, orientation, traffic_convenience, joint = cal_roads(image_path, road_topo_path)
        cur_dict["road_density"] = float(road_density)
        cur_dict["orientation"] = float(orientation)
        cur_dict["convenience"] = float(traffic_convenience)
        cur_dict["joint_density"] = float(joint)

        tile_list.append(cur_dict)
    

    label_dict = make_label(tile_list)

    data = {"tile_list": tile_list}
    for key in label_dict.keys():
        data[key] = label_dict[key]

    with open(tile_statics_save_path,'w') as file:
        json.dump(data,file)

# Compute the coverage area of the whole dataset
def cal_total_rasterize_area():
    dataspace = r"./dataset_roads/Europe"
    big_tile_dir = os.path.join(dataspace, "aligned_tiffs")
    area = 0
    for big_tile in os.listdir(big_tile_dir):
        with rasterio.open(os.path.join(big_tile_dir, big_tile)) as bt:
            left, bottom, right, top = bt.bounds
            geoms = Polygon(((left, top), (right, top), (right, bottom), (left, bottom)))
            cur_area = geoms.area
            print(big_tile, ": ", cur_area)
            area += cur_area
    print(f"total area: {area} m2, {area/1e6}km2")
    return area

def trans_json2npy(json_path, npy_path, filter_path=None):
    with open(json_path,'r') as file:
        data = json.load(file)
    tile_list = data["tile_list"]
    building_density_list = []
    building_height_list = []
    road_density_list = []
    orientation_list = []
    convenience_list = []
    joint_density_list = []
    
    if filter_path is not None:
        filter_list = []
        with open(filter_path, "r") as f:
            datas = f.readlines()
        for data in datas:
            filter_list.append(data.replace("\n",""))
    # i = 0
    for tile in tile_list:
        if (filter_path is not None) and (tile in filter_list): continue
        # i += 1
        # if i >400: continue
        # print(tile["tile_name"])
        # print(tile["building_density"])
        # print(tile["building_height"])
        # print(tile["road_density"]*200)
        # print(tile["orientation"])
        # print(tile["convenience"])
        # print(tile["joint_density"])
        # print("_________")
        
        building_density_list.append(tile["building_density"])
        building_height_list.append(tile["building_height"])
        road_density_list.append(tile["road_density"]*200)
        orientation_list.append(tile["orientation"])
        convenience_list.append(tile["convenience"])
        joint_density_list.append(tile["joint_density"])
    
    dict_npy = {"building_density": np.asarray(building_density_list),
                "building_height": np.asarray(building_height_list),
                "road_density": np.asarray(road_density_list),
                "orientation": np.asarray(orientation_list),
                "convenience": np.asarray(convenience_list),
                "joint_density": np.asarray(joint_density_list)}
    np.save(npy_path, dict_npy)


def vis_orientation(geojsondir):
    import osmnx as ox
    import networkx as nx
    import json
    from shapely.geometry import LineString, Point
    import geopandas as gpd
    geojsonpath1 = os.path.join(geojsondir, "primary.geojson")
    geojsonpath2 = os.path.join(geojsondir, "motorway.geojson")
    # Load GeoJSON
    gdf1 = gpd.read_file(geojsonpath1)
    gdf2 = gpd.read_file(geojsonpath2)
    gdf = gdf1.append(gdf2, ignore_index=True)

    nodes_list = []
    edges_list = []

    # Assign a unique ID to each node (intersection or endpoint)
    node_id = 0
    node_dict = {}

    for index, row in gdf.iterrows():
        line = row['geometry']
        if isinstance(line, LineString):
            coords = list(line.coords)
            u = None
            for coord in coords:
                # Check if the node exists to avoid duplicates
                if coord not in node_dict:
                    node_dict[coord] = node_id
                    nodes_list.append({'osmid': node_id, 'x': coord[0], 'y': coord[1]})
                    node_id += 1
                if u is not None:
                    v = node_dict[coord]
                    geom = LineString([Point(*coords[coords.index((u_x, u_y))]), Point(coord)])
                    edges_list.append({
                        'u': u,
                        'v': v,
                        'geometry': geom,
                        # 'length' will be calculated after setting the CRS
                    })
                u = node_dict[coord]
                u_x, u_y = coord

    # Create GeoDataFrames for nodes and edges
    gdf_nodes = gpd.GeoDataFrame(nodes_list, geometry=gpd.points_from_xy([node['x'] for node in nodes_list], [node['y'] for node in nodes_list]))
    gdf_edges = gpd.GeoDataFrame(edges_list, geometry=[edge['geometry'] for edge in edges_list])

    # Step 2.5: Set CRS and calculate the length of edges
    gdf_nodes.crs = 'EPSG:4326'
    gdf_edges.crs = 'EPSG:4326'

    # Convert to a projected CRS to calculate lengths in meters
    gdf_edges = gdf_edges.to_crs(epsg=3857)  # Use an appropriate projected CRS for your area
    gdf_edges['length'] = gdf_edges.length

    # Convert back to the original CRS if needed
    gdf_edges = gdf_edges.to_crs('EPSG:4326')

    # Step 3: Ensure the edges GeoDataFrame has a MultiIndex of u, v, key
    gdf_edges['key'] = 0  # In this example, we don't handle parallel edges, so all keys are 0
    gdf_edges.set_index(['u', 'v', 'key'], inplace=True)
    gdf_nodes.set_index('osmid', inplace=True)

    G = ox.graph_from_gdfs(gdf_nodes, gdf_edges)
    G_undirected = G.to_undirected()
    edge_bearings = ox.bearing.add_edge_bearings(G_undirected)
    # G_unprojected = ox.project_graph(G_undirected)
    fig, ax = ox.plot_orientation(G_undirected, color="#81b5d5") #"#6A5ACD" color="#7e6ee1"
    plt.show()


if __name__ == "__main__":
    # main_cal_statics_per_tile()
    # cal_total_rasterize_area()

    dataspace1 = r"./dataset_roads"
    dataspace2 = r"./dataset_roads"
    tile_statics_save_path1 = os.path.join(dataspace1, "UnitedStates","statics","tile_statics.json")
    tile_statics_save_path2 = os.path.join(dataspace1, "China_5m" ,"statics", "tile_statics.json")
    tile_statics_save_path3 = os.path.join(dataspace2, "Australia","statics", "tile_statics.json")
    tile_statics_save_path4 = os.path.join(dataspace2, "Europe", "statics","tile_statics.json")
    
    npy_path1 = os.path.join(dataspace1, "UnitedStates","statics","tile_statics.npy")
    npy_path2 = os.path.join(dataspace1,"China_5m" ,"statics","tile_statics.npy")
    npy_path3 = os.path.join(dataspace2, "Australia","statics","tile_statics.npy")
    npy_path4 = os.path.join(dataspace2, "Europe","statics","tile_statics.npy")
    
    # trans_json2npy(tile_statics_save_path1, npy_path1)
    # trans_json2npy(tile_statics_save_path2, npy_path2)
    # trans_json2npy(tile_statics_save_path3, npy_path3)
    # trans_json2npy(tile_statics_save_path4, npy_path4)
    # # vis_metric_bins_from_npy([npy_path], "orientation", "orientation", distance=3)
    # vis_stacked_bins_from_npy_clamp([npy_path1, npy_path2, npy_path3, npy_path4], "orientation", "Orientation", distance=0.05, clamp_range=[2.2, 3.6])
    # vis_stacked_bins_from_npy_clamp([npy_path1, npy_path2, npy_path3, npy_path4], "road_density", "Road Density", distance=0.5, clamp_range=[1, 14])
    # vis_stacked_bins_from_npy_clamp([npy_path1, npy_path2, npy_path3, npy_path4], "building_density", "Building Density", distance=0.01, clamp_range=[0.1, 0.5])
    # vis_stacked_bins_from_npy_clamp([npy_path1, npy_path2, npy_path3, npy_path4], "building_height", "Building Height", distance=3, clamp_range=[3, 120])
    vis_stacked_bins_from_npy_clamp([npy_path1, npy_path2, npy_path3, npy_path4], "convenience", "convenience", distance=0.02, clamp_range=[0.45, 1])
    # vis_pie_from_npy_for_cls([npy_path1, npy_path2, npy_path3, npy_path4])

    # vis_orientation(geojsondir = r"./dataset_roads/Australia/roads/geojson/Melbourne")
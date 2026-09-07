import os
import sys
sys.path.append(r".")
sys.path.append(r"..")
sys.path.append(r"./../data_preperation")
from data_preperation.main_gen_road_topo import raster2topo_multichannel
from data_preperation.scripts.tiff_operation import CRStrans
import rasterio
import networkx as nx
from points2csv import random_walk
from matplotlib import pyplot as plt
import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString


def partition_roads(sim_graph):
    ####################### Partition topology into numbered roads #################################
    # Relabel nodes
    nodelist = sim_graph.nodes()
    mapping = {old_label:new_label for new_label, old_label in enumerate(nodelist)}
    labeled_graph = nx.relabel_nodes(sim_graph, mapping)
    # Random-walk partition and visualize edges visited in each round
    path_list, edge_list = random_walk(labeled_graph)
    pos = nx.get_node_attributes(labeled_graph, 'geo_pos')
    nx.draw(labeled_graph, pos, with_labels=False, node_color='black', node_size=16)
    for i,edges in enumerate(edge_list):
        print(i,edges)
        nx.draw_networkx_edges(labeled_graph, pos ,edgelist=edges, edge_color=f'C{i}', width=2)
    plt.show()
    # plt.cla()
    return path_list, labeled_graph


def save_roads_to_geojson(path_list, labeled_graph ,outgeojson):
    roadlist = []
    for i,nodes in enumerate(path_list):
        cur_road = []
        for node in nodes:
            lat, lon = labeled_graph.nodes()[node]["geo_pos"][1], labeled_graph.nodes()[node]["geo_pos"][0]
            cur_road.append((lon, lat))
        line = LineString(cur_road)
        polygon = line.buffer(0.000001*35)

        roadlist.append(polygon)
    roads = gpd.GeoDataFrame(roadlist, columns=["geometry"])
    roads.to_file(outgeojson, driver="GeoJSON")


def trans_linestring_to_geojson():
    input_file = r"./data/qgis_prj/sr/demo_roads.geojson"
    outgeojson = r"./data/qgis_prj/sr/demo_roads_polygon.geojson"
    # Read file into a GeoDataFrame
    gdf = gpd.read_file(input_file)
    
    # Ensure all geometries are LineString
    if not all(gdf.geometry.type == 'LineString'):
        raise ValueError("All features must be LineString geometries.")
    
    # Buffer each LineString
    gdf['geometry'] = gdf.geometry.buffer(0.000001*35)
    
    # Save as GeoJSON
    gdf.to_file(outgeojson, driver='GeoJSON')

def save2csv(path_list, labeled_graph, outcsv_dir):
    roadlist = []
    attrlist = []
    for i,nodes in enumerate(path_list):
        attrlist.append([i,i,"tertiary"])
        for node in nodes:
            lon, lat = labeled_graph.nodes()[node]["geo_pos"][0], labeled_graph.nodes()[node]["geo_pos"][1]
            roadlist.append([node, lon, lat, i])
    roads = pd.DataFrame(roadlist, columns=["id","lon","lat","group_id"])
    roads.to_csv(os.path.join(outcsv_dir,f'roads.csv'), index=False)
    attributes = pd.DataFrame(attrlist, columns=["id","group_id","attribute"])
    attributes.to_csv(os.path.join(outcsv_dir,f'attributes.csv'), index=False)
    return labeled_graph

def trans_graph_uv_epsg(src, road_graph):
    crstrans = CRStrans()
    for node in road_graph.nodes:
        lat_3857, lon_3857 = crstrans.uv2lat(src,road_graph.nodes[node]["pos"][1], road_graph.nodes[node]["pos"][0])
        lon, lat = crstrans.dis2lat(lon_3857, lat_3857)
        road_graph.nodes[node]["geo_pos"] = (lon, lat)
        # road_graph.nodes[node]["lon"] = lon
    return road_graph

def get_roads_of_a_tile_togeojson():
    image_dir = r"./data/qgis_prj/tiff"
    topo_dir = r"./data/qgis_prj/simple_topo"
    outcsv_dir = r"./data/qgis_prj/csv_osm"
    os.makedirs(outcsv_dir, exist_ok=True)
    # topo_dir = r"./data/qgis_prj/complex_topo"
    # raster2topo_multichannel(image_dir, topo_dir, simplify=False)
    
    image_path = os.path.join(image_dir, "Philadelphia_tile_5916_2856.tif")
    with rasterio.open(image_path) as src:
    
        topo_path = os.path.join(topo_dir, "Philadelphia_tile_5916_2856.gpickle")
        road_graph = nx.read_gpickle(topo_path)

        road_graph = trans_graph_uv_epsg(src, road_graph)
    
    path_list, label_graph = partition_roads(road_graph)
    save_roads_to_geojson(path_list, label_graph, os.path.join(topo_dir, "teaser_roads_polygon.geojson"))
    save2csv(path_list, label_graph, outcsv_dir)
    from csv2osm import csv2osm_main
    outosm = r"./data/qgis_prj/csv_osm/teaser.osm"
    outprj = r"./data/qgis_prj/csv_osm/teaser.txt"
    csv2osm_main(roadcsv= os.path.join(outcsv_dir, "roads.csv"), attrcsv=os.path.join(outcsv_dir, "attributes.csv"), outosm=outosm, outproj=outprj)

def get_generate_roads_togeojson():
    dataspace = r"./data/qgis_prj/sr"
    outcsv_dir = os.path.join(dataspace, r"csv_osm2")
    os.makedirs(outcsv_dir, exist_ok=True)

    image_path = os.path.join(dataspace, "Philadelphia_tile_5916_2856.tif")
    with rasterio.open(image_path) as src:
    
        topo_path = os.path.join(dataspace, "demo.gpickle")
        import pickle
        with open(topo_path, 'rb') as f:
            road_graph = pickle.load(f)
        # road_graph = nx.read_gpickle(topo_path)
        # road_graph.add_edge(15,22)
        # road_graph.remove_node(17)
        # road_graph.remove_node(59)
        # road_graph.remove_node(20)
        # road_graph.remove_node(29)
        # with open(topo_path, 'wb') as f:
        #     pickle.dump(road_graph, f, pickle.HIGHEST_PROTOCOL)

        road_graph = trans_graph_uv_epsg(src, road_graph)
    
    path_list, label_graph = partition_roads(road_graph)
    # save_roads_to_geojson(path_list, label_graph, os.path.join(dataspace, "demo2_roads.geojson"))
    # save2csv(path_list, label_graph, outcsv_dir)
    # from csv2osm import csv2osm_main
    # outosm = r"./data/qgis_prj/sr/csv_osm/demo2.osm"
    # outprj = r"./data/qgis_prj/sr/csv_osm/demo2.txt"
    # csv2osm_main(roadcsv= os.path.join(outcsv_dir, "roads.csv"), attrcsv=os.path.join(outcsv_dir, "attributes.csv"), outosm=outosm, outproj=outprj)
    

if __name__ == '__main__':
    # trans_linestring_to_geojson()
    # get_roads_of_a_tile_togeojson()
    get_generate_roads_togeojson()
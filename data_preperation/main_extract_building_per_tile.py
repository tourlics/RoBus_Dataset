import networkx as nx
import rasterio
from shapely.geometry import Polygon, box, Point
import os
from tqdm import tqdm
import geopandas as gpd
import json
from scripts.vec2raster import CRStrans
from matplotlib import pyplot as plt
import copy

def within_polygon_idx(polygon_gpd, ref_poly):
    idx_list = []
    for idx,polygon in enumerate(polygon_gpd.get('geometry')):
        if ref_poly.contains(polygon):
            idx_list.append(idx)
    return idx_list

def trans_single_json_to_qgis(jsonpath, outgeojson, scene_name):
    attr_list = []
    geom_list = []
    hgt_list = []
    with open(jsonpath) as f:
        json_data_list = json.load(f)
    num_item = len(json_data_list)
    infile = False
    i = 0
    for json_dict in json_data_list:
        if json_dict["boundary_name"] == scene_name:
            infile = True
            select_boundary = json_dict
            i+= 1

            boundary_coordinates = select_boundary["boundary_coordinates"]  
            attr_list.append("boundary")
            geom_list.append(Polygon(boundary_coordinates))
            hgt_list.append(0)

            gdf = gpd.GeoDataFrame({"item_type": attr_list, "geometry":geom_list, "height":hgt_list})
            gdf.to_file(outgeojson.replace(".geojson", f"{i}.geojson"), driver="GeoJSON")

            del attr_list[:]
            del geom_list[:]
            del hgt_list[:]
            buildings_list = select_boundary["buildings"]
            for building in buildings_list:
                attr_list.append("building")
                building_coordinates = building["coordinates"]
                geom_list.append(Polygon(building_coordinates))
                hgt_list.append(building["height"])
            
            gdf = gpd.GeoDataFrame({"item_type": attr_list, "geometry":geom_list, "height":hgt_list})
            gdf.to_file(outgeojson.replace(".geojson", f"{i}_b.geojson"), driver="GeoJSON")
            del attr_list[:]
            del geom_list[:]
            del hgt_list[:]
    if not infile:
        print("not in this file")

def vis_all_boundary_to_qgis(jsonpath, outgeojson):
    geom_list = []
    with open(jsonpath) as f:
        json_data_list = json.load(f)
    for select_boundary in json_data_list:
        boundary_coordinates = select_boundary["boundary_coordinates"]  
        geom_list.append(Polygon(boundary_coordinates))
    print(len(geom_list))
    gdf = gpd.GeoDataFrame({"geometry":geom_list, "crs":"EPSG:3857"})
    gdf.to_file(outgeojson, driver="GeoJSON")

def vis_all_building_to_qgis(jsonpath, outgeojson):
    groupid_list = []
    geom_list = []
    hgt_list = []
    with open(jsonpath) as f:
        json_data_list = json.load(f)
 
    for boundary in json_data_list:
        buildings_list = boundary["buildings"]
        for building in buildings_list:
            groupid_list.append(boundary["boundary_id"])
            building_coordinates = building["coordinates"]
            geom_list.append(Polygon(building_coordinates))
            hgt_list.append(building["height"])
        
    gdf = gpd.GeoDataFrame({"group_id": groupid_list, "geometry":geom_list, "height":hgt_list})
    gdf.to_file(outgeojson, driver="GeoJSON")



  
def find_simple_cycles_depracated(G):  
    # Use NetworkX cycle_basis to find fundamental cycles; incomplete, many missing
    cycles = nx.cycle_basis(G) 
    # Filter out cycles that geometrically contain other cycles
    def is_simple_cycle(cycle):  
        cycle_poly = Polygon([(G.nodes[node]["pos"][0], G.nodes[node]["pos"][1]) for node in cycle])
        for other_cycle in cycles:  
            if cycle == other_cycle: continue
            other_cycle_poly = Polygon([(G.nodes[node]["pos"][0], G.nodes[node]["pos"][1]) for node in other_cycle])
            if cycle_poly.contains(other_cycle_poly):  
                return False  
        return True  
      
    simple_cycles = [cycle for cycle in cycles if is_simple_cycle(cycle)] 
    return simple_cycles 


# Remove all degree-1 nodes
def prune_leaves(G):
    pruned = True
    while pruned:
        pruned = False
        leaves = [node for node, degree in G.degree() if degree == 1]
        if leaves:
            G.remove_nodes_from(leaves)
            pruned = True

def find_smallest_cycle_with_three_nodes(graph, node1, node2, node3, cutoff):
    # Check whether the graph contains these three nodes
    if not all(n in graph.nodes for n in [node1, node2, node3]):
        return None
    # Find all simple paths between node1 and node2
    all_paths_between_node1_and_node2 = list(nx.all_simple_paths(graph, source=node1, target=node2, cutoff=cutoff))
    smallest_cycle = None
    for path in all_paths_between_node1_and_node2:
        # Check whether node3 is on the path
        if node3 in path:
            cycle = path + [path[0]]  # Build the cycle
            # Update the smallest cycle
            if smallest_cycle is None or len(cycle) < len(smallest_cycle):
                smallest_cycle = cycle

    return smallest_cycle

# Remove degree-2 nodes and return their cycles
def remove_degree_two_nodes(G):
    cycle_list = []
    findnode = False
    nodes2_list = [node for node, degree in G.degree() if degree == 2]
    for node in nodes2_list:
        if G.degree()[node] <2 :
            continue
        node_neigbours = list(nx.neighbors(G, node))
        cycle = find_smallest_cycle_with_three_nodes(G, node, node_neigbours[0], node_neigbours[1], cutoff=12)
        if cycle is not None:
            cycle_list.append(cycle)
            findnode = True
            G.remove_node(node)
    return G, findnode, cycle_list

def find_simple_cycles(G):
    from scripts.visualization import vis_single_gpickle
    # vis_single_gpickle(G)
    prune_leaves(G)
    # vis_single_gpickle(G)
    all_cycles = []
    while True:
        G, findnode, cycle_list = remove_degree_two_nodes(G)
        # vis_single_gpickle(G)
        prune_leaves(G)
        # vis_single_gpickle(G)
        all_cycles.extend(cycle_list)
        if not findnode:
            break
    return all_cycles


def check_gpickle_boundary_to_qgis(gpicklepath, outdir):
    road_graph = nx.read_gpickle(gpicklepath)
    # pos = nx.get_node_attributes(road_graph, 'pos')
    # nx.draw(road_graph, pos, with_labels=True, node_size=40)
    # plt.show()
    # cycles = nx.cycle_basis(road_graph) 
    cycles = find_simple_cycles(road_graph)
    print(len(cycles))
    
    # Convert cycles to polygons  
    for idx, cycle in enumerate(cycles):  
        block_list = []
        cycle_coords = [(road_graph.nodes[node]["pos"][0], road_graph.nodes[node]["pos"][1]) for node in cycle]
        # Create a polygon  
        ref_poly = Polygon(cycle_coords) 
        if ref_poly.area < 300: continue # Skip tiny cycles
        block_list.append(ref_poly)
        outgeojson = os.path.join(outdir, f"{idx}.geojson")
        gdf = gpd.GeoDataFrame({"geometry":block_list})
        gdf.to_file(outgeojson, driver="GeoJSON")

def generate_road_topo_slow():
    dataspace = r"./dataset_roads/China_10m"
    image_dir = os.path.join(dataspace, r"cropped_images")
    road_topo_dir = os.path.join(dataspace, r"topo_complex")
    building_geojson_dir = os.path.join(dataspace, r"buildings\geojson")
    building_block_dir = os.path.join(dataspace, r"buildings\block_building_geojson")
    os.makedirs(building_block_dir, exist_ok=True)

    road_topos = os.listdir(road_topo_dir)
    building_id = 0
    boundary_list = []
    boundary_id = 0
    fileidx = 0

    for road_topo in tqdm(road_topos):
        if not road_topo.endswith(".gpickle"): continue
        tile_name = road_topo.split(".")[0]
        image_path = os.path.join(image_dir, f"{tile_name}.tif")
        scene_name = tile_name.split("_")[0]
        building_geojson_path = os.path.join(building_geojson_dir, scene_name, f"{scene_name}_building_hgt.geojson")
        with rasterio.open(image_path) as src:
            bounds = src.bounds
            crs = src.crs
        gdf = gpd.read_file(building_geojson_path)  
        left, bottom, right, top = bounds
        rect_bounds = box(minx=left, miny=bottom, maxx=right, maxy=top)
        crstrans = CRStrans()
        rect_bounds = crstrans.transhapely(rect_bounds, crs, "EPSG:4326")
        polygons_within_bounds = gdf[gdf.intersects(rect_bounds)]

        road_graph = nx.read_gpickle(os.path.join(road_topo_dir, f"{tile_name}.gpickle"))
        cycles = nx.cycle_basis(road_graph) 
        # Convert cycles to polygons  
        for cycle in cycles:  
            cycle_coords = [crstrans.uv2lat(src,road_graph.nodes[node]["pos"][0], road_graph.nodes[node]["pos"][1]) for node in cycle]
            # Create a polygon  
            ref_poly = Polygon(cycle_coords)  
            if ref_poly.area < 200*200: continue # Skip tiny cycles (unit: m)
            ref_poly = crstrans.transhapely(ref_poly, crs, "EPSG:4326")
            idx_list = within_polygon_idx(polygons_within_bounds, ref_poly)
            if len(idx_list) == 0:continue
            
            boundary_coordinates = list(ref_poly.exterior.coords)
            cur_boundary = {"boundary_id": '%07d' % boundary_id, "boundary_coordinates": boundary_coordinates}

            buildings_in_boundary = []
            for idx in idx_list:
                building_geometry = list(polygons_within_bounds.iloc[idx]["geometry"].exterior.coords)
                building_height = polygons_within_bounds.iloc[idx]["height"]
                cur_building = {"id":'%07d' % building_id, "height":building_height, "coordinates":building_geometry}
                buildings_in_boundary.append(cur_building)
                building_id += 1
            
            if len(buildings_in_boundary) == 0: continue
            cur_boundary["buildings"] = buildings_in_boundary
            boundary_id += 1
            boundary_list.append(cur_boundary)


        fileidx += 1
        if fileidx % 100 == 0:
            if len(boundary_list) == 0: continue
            building_block_json = os.path.join(building_block_dir, f"block_{fileidx}.json")
            json_data = json.dumps(boundary_list, indent=4)  # indent pretty-prints the output; not required  
            with open(building_block_json, "w") as file:  
                file.write(json_data)  
            del boundary_list[:]

def min_rectangle_aspect_ratio(polygon):
    # Compute the minimum bounding rectangle
    min_rect = polygon.minimum_rotated_rectangle
    
    # Get the rectangle coordinates
    x, y = min_rect.exterior.coords.xy
    
    # Compute edge lengths of the rectangle
    edge_lengths = []
    for i in range(len(x) - 1):
        edge_length = ((x[i+1] - x[i])**2 + (y[i+1] - y[i])**2)**0.5
        edge_lengths.append(edge_length)
    
    # The longest and shortest edges are the rectangle length and width
    # A rectangle has two pairs of equal sides, so only two lengths are needed
    length = max(edge_lengths)
    width = min(edge_lengths)
    
    # Compute the aspect ratio
    aspect_ratio = length / width
    return aspect_ratio

def generate_road_topo_fast():
    dataspace = r"./dataset_roads/Europe"
    image_dir = os.path.join(dataspace, r"cropped_images")
    road_topo_dir = os.path.join(dataspace, r"topo_simplify")
    building_geojson_dir = os.path.join(dataspace, r"buildings\geojson")
    building_block_dir = os.path.join(dataspace, r"urban_block_building\geojson")
    os.makedirs(building_block_dir, exist_ok=True)

   
    road_topos = os.listdir(road_topo_dir)
    building_id = 0
    boundary_list = []
    boundary_id = 0
    fileidx = 0

    ref_scene_name = road_topos[0].split('.')[0].split("_")[0]
    building_geojson_path = os.path.join(building_geojson_dir, ref_scene_name, f"{ref_scene_name}_building_hgt.geojson")
    gdf = gpd.read_file(building_geojson_path) 

    for road_topo in tqdm(road_topos):
        if not road_topo.endswith(".gpickle"): continue
        tile_name = road_topo.split(".")[0]
        image_path = os.path.join(image_dir, f"{tile_name}.tif")
        
        with rasterio.open(image_path) as src:
            crs = src.crs
        scene_name = road_topo.split(".")[0].split("_")[0]
        if scene_name != os.path.basename(building_geojson_path).split("_")[0]:
            building_geojson_path = os.path.join(building_geojson_dir, scene_name, f"{scene_name}_building_hgt.geojson")
            gdf = gpd.read_file(building_geojson_path) 
            print("read")
        crstrans = CRStrans()

        road_graph = nx.read_gpickle(os.path.join(road_topo_dir, f"{tile_name}.gpickle"))
        # pos = nx.get_node_attributes(road_graph, 'pos')
        # nx.draw(road_graph, pos, with_labels=True, node_size=40)
        # plt.show()
        cycles = find_simple_cycles(copy.deepcopy(road_graph)) 
        # Convert cycles to polygons  
        for cycle in cycles:  
            cycle_coords = [crstrans.uv2lat(src,road_graph.nodes[node]["pos"][1], road_graph.nodes[node]["pos"][0]) for node in cycle]
            # Create a polygon  
            ref_poly = Polygon(cycle_coords)  
            polygon_area = ref_poly.area
            if polygon_area < 100*100: continue # Skip tiny cycles (unit: m)
            try:
                if min_rectangle_aspect_ratio(ref_poly) > 5: continue # Filter elongated slivers
            except:
                continue
            # if polygon_area > 1000*1000: continue# Skip very large cycles that span multiple blocks
            ref_poly = crstrans.transhapely(ref_poly, crs, "EPSG:4326")

            polygons_within_bounds = gdf[gdf.within(ref_poly)]
            # polygons_within_bounds = gdf[gdf.intersects(ref_poly)] # for vis

            if len(polygons_within_bounds) < 3: continue # Filter if fewer than 5 buildings inside the boundary
            
            boundary_coordinates = list(ref_poly.exterior.coords)
            cur_boundary = {"CRS": "EPSG: 3857","boundary_id": '%07d' % boundary_id, "boundary_coordinates": boundary_coordinates, "boundary_name":road_topo.split(".")[0]}

            buildings_in_boundary = []
            for idx, row in polygons_within_bounds.iterrows():
                building_geometry = list(row["geometry"].exterior.coords)
                building_height = row["height"]
                cur_building = {"id":'%07d' % building_id, "height":building_height, "coordinates":building_geometry}
                buildings_in_boundary.append(cur_building)
                building_id += 1
            
            if len(buildings_in_boundary) == 0: continue
            cur_boundary["buildings"] = buildings_in_boundary
            boundary_id += 1
            boundary_list.append(cur_boundary)


        fileidx += 1
        if fileidx % 3000 == 0:
            if len(boundary_list) == 0: continue
            building_block_json = os.path.join(building_block_dir, f"block_{fileidx}.json")
            json_data = json.dumps(boundary_list, indent=4)  # indent pretty-prints the output; not required  
            with open(building_block_json, "w") as file:  
                file.write(json_data)  
            del boundary_list[:]
        elif fileidx == len(road_topos):
            if len(boundary_list) == 0: continue
            building_block_json = os.path.join(building_block_dir, f"block_{fileidx}.json")
            json_data = json.dumps(boundary_list, indent=4)  # indent pretty-prints the output; not required  
            with open(building_block_json, "w") as file:  
                file.write(json_data)  

def generate_single_topo_fast():
    dataspace = r"./dataset_roads/UnitedStates"
    image_dir = os.path.join(dataspace, r"cropped_images")
    road_topo_dir = os.path.join(dataspace, r"topo_simplify")
    building_geojson_dir = os.path.join(dataspace, r"buildings\geojson")
    building_block_dir = os.path.join(dataspace, r"urban_block_building\geojson")
    os.makedirs(building_block_dir, exist_ok=True)

    road_topo = os.path.join(road_topo_dir, "Philadelphia_tile_5916_3060.gpickle")
    building_id = 0
    boundary_list = []
    boundary_id = 0
    fileidx = 0

    ref_scene_name = "Philadelphia"
    building_geojson_path = os.path.join(building_geojson_dir, ref_scene_name, f"{ref_scene_name}_building_hgt.geojson")
    gdf = gpd.read_file(building_geojson_path) 

    tile_name = road_topo.split(".")[0]
    image_path = os.path.join(image_dir, "Philadelphia_tile_5916_3060.tif")
    
    with rasterio.open(image_path) as src:
        crs = src.crs
    crstrans = CRStrans()

    road_graph = nx.read_gpickle(os.path.join(road_topo_dir, f"{tile_name}.gpickle"))
    # pos = nx.get_node_attributes(road_graph, 'pos')
    # nx.draw(road_graph, pos, with_labels=True, node_size=40)
    # plt.show()
    cycles = find_simple_cycles(copy.deepcopy(road_graph)) 
    # Convert cycles to polygons  
    for cycle in cycles:  
        cycle_coords = [crstrans.uv2lat(src,road_graph.nodes[node]["pos"][1], road_graph.nodes[node]["pos"][0]) for node in cycle]
        # Create a polygon  
        ref_poly = Polygon(cycle_coords)  
        polygon_area = ref_poly.area
        # if polygon_area < 200*200: continue # Skip tiny cycles (unit: m)
        
        # if min_rectangle_aspect_ratio(ref_poly) > 5: continue # Filter elongated slivers
        
        # if polygon_area > 1000*1000: continue# Skip very large cycles that span multiple blocks
        ref_poly = crstrans.transhapely(ref_poly, crs, "EPSG:4326")

        polygons_within_bounds = gdf[gdf.within(ref_poly)]
        # polygons_within_bounds = gdf[gdf.intersects(ref_poly)] # for vis

        # if len(polygons_within_bounds) < 3: continue # Filter if fewer than 5 buildings inside the boundary
        
        boundary_coordinates = list(ref_poly.exterior.coords)
        cur_boundary = {"CRS": "EPSG: 3857","boundary_id": '%07d' % boundary_id, "boundary_coordinates": boundary_coordinates, "boundary_name":road_topo.split(".")[0]}

        buildings_in_boundary = []
        for idx, row in polygons_within_bounds.iterrows():
            building_geometry = list(row["geometry"].exterior.coords)
            building_height = row["height"]
            cur_building = {"id":'%07d' % building_id, "height":building_height, "coordinates":building_geometry}
            buildings_in_boundary.append(cur_building)
            building_id += 1
        
        if len(buildings_in_boundary) == 0: continue
        cur_boundary["buildings"] = buildings_in_boundary
        boundary_id += 1
        boundary_list.append(cur_boundary)


    # building_block_json = os.path.join(building_block_dir, f"block_{fileidx}.json")
    # json_data = json.dumps(boundary_list, indent=4)  # indent pretty-prints the output; not required  
    # with open(building_block_json, "w") as file:  
    #     file.write(json_data)  
    # del boundary_list[:]
    outgeojson = r"./data/output/boundary_vis.geojson"
    attr_list = []
    geom_list = []
    hgt_list = []
    i = 0
    for json_dict in boundary_list:
        select_boundary = json_dict
        i+= 1

        boundary_coordinates = select_boundary["boundary_coordinates"]  
        attr_list.append("boundary")
        geom_list.append(Polygon(boundary_coordinates))
        hgt_list.append(0)

        gdf = gpd.GeoDataFrame({"item_type": attr_list, "geometry":geom_list, "height":hgt_list})
        gdf.to_file(outgeojson.replace(".geojson", f"{i}.geojson"), driver="GeoJSON")

        del attr_list[:]
        del geom_list[:]
        del hgt_list[:]
        buildings_list = select_boundary["buildings"]
        for building in buildings_list:
            attr_list.append("building")
            building_coordinates = building["coordinates"]
            geom_list.append(Polygon(building_coordinates))
            hgt_list.append(building["height"])
        
        gdf = gpd.GeoDataFrame({"item_type": attr_list, "geometry":geom_list, "height":hgt_list})
        gdf.to_file(outgeojson.replace(".geojson", f"{i}_b.geojson"), driver="GeoJSON")
        del attr_list[:]
        del geom_list[:]
        del hgt_list[:]


def generate_single_topo_fast_virtual():
    road_topo_path = r"./data/qgis_prj/sr/demo.gpickle"
    building_id = 0
    boundary_list = []
    boundary_id = 0
    fileidx = 0

    building_geojson_path = r"./data/qgis_prj/sr/demo_buildings.geojson"
    gdf = gpd.read_file(building_geojson_path) 

    image_path = os.path.join(r"./data/qgis_prj/tiffs", "Philadelphia_tile_5916_2856.tif")
    
    with rasterio.open(image_path) as src:
        crs = src.crs
    crstrans = CRStrans()

    # pos = nx.get_node_attributes(road_graph, 'pos')
    # nx.draw(road_graph, pos, with_labels=True, node_size=40)
    # plt.show()
    import pickle
    with open(road_topo_path, 'rb') as f:
        road_topo = pickle.load(f)
    # road_topo = nx.read_gpickle(road_topo_path)
    cycles = find_simple_cycles(copy.deepcopy(road_topo)) 
    # Convert cycles to polygons  
    for cycle in cycles:  
        cycle_coords = [crstrans.uv2lat(src,road_topo.nodes[node]["pos"][1], road_topo.nodes[node]["pos"][0]) for node in cycle]
        # Create a polygon  
        ref_poly = Polygon(cycle_coords)  
        polygon_area = ref_poly.area
        # if polygon_area < 200*200: continue # Skip tiny cycles (unit: m)
        
        # if min_rectangle_aspect_ratio(ref_poly) > 5: continue # Filter elongated slivers
        
        # if polygon_area > 1000*1000: continue# Skip very large cycles that span multiple blocks
        ref_poly = crstrans.transhapely(ref_poly, crs, "EPSG:4326")

        polygons_within_bounds = gdf[gdf.within(ref_poly)]
        # polygons_within_bounds = gdf[gdf.intersects(ref_poly)] # for vis

        # if len(polygons_within_bounds) < 3: continue # Filter if fewer than 5 buildings inside the boundary
        
        boundary_coordinates = list(ref_poly.exterior.coords)
        cur_boundary = {"CRS": "EPSG: 3857","boundary_id": '%07d' % boundary_id, "boundary_coordinates": boundary_coordinates}

        buildings_in_boundary = []
        for idx, row in polygons_within_bounds.iterrows():
            building_geometry = list(row["geometry"].exterior.coords)
            building_height = row["building_hgt"]
            cur_building = {"id":'%07d' % building_id, "height":building_height, "coordinates":building_geometry}
            buildings_in_boundary.append(cur_building)
            building_id += 1
        
        if len(buildings_in_boundary) == 0: continue
        cur_boundary["buildings"] = buildings_in_boundary
        boundary_id += 1
        boundary_list.append(cur_boundary)


    building_block_json = r"./data/qgis_prj/sr/build_geojson/demo_building_topo.geojson"
    json_data = json.dumps(boundary_list, indent=4)  # indent pretty-prints the output; not required  
    with open(building_block_json, "w") as file:  
        file.write(json_data)  
    del boundary_list[:]

    # outgeojson = r"./data/qgis_prj/sr/build_geojson/boundary_vis.geojson"
    # attr_list = []
    # geom_list = []
    # hgt_list = []
    # i = 0
    # for json_dict in boundary_list:
    #     select_boundary = json_dict
    #     i+= 1

    #     boundary_coordinates = select_boundary["boundary_coordinates"]  
    #     attr_list.append("boundary")
    #     geom_list.append(Polygon(boundary_coordinates))
    #     hgt_list.append(0)

    #     gdf = gpd.GeoDataFrame({"item_type": attr_list, "geometry":geom_list, "height":hgt_list})
    #     gdf.to_file(outgeojson.replace(".geojson", f"{i}.geojson"), driver="GeoJSON")

    #     del attr_list[:]
    #     del geom_list[:]
    #     del hgt_list[:]
    #     buildings_list = select_boundary["buildings"]
    #     for building in buildings_list:
    #         attr_list.append("building")
    #         building_coordinates = building["coordinates"]
    #         geom_list.append(Polygon(building_coordinates))
    #         hgt_list.append(building["height"])
        
    #     gdf = gpd.GeoDataFrame({"item_type": attr_list, "geometry":geom_list, "height":hgt_list})
    #     gdf.to_file(outgeojson.replace(".geojson", f"{i}_b.geojson"), driver="GeoJSON")
    #     del attr_list[:]
    #     del geom_list[:]
    #     del hgt_list[:]

def get_buildings_of_a_tile():
    dataspace = r"./dataset_roads/UnitedStates"
    image_path = os.path.join(dataspace, r"cropped_images\Philadelphia_tile_5916_5304.tif")
    building_geojson_path = os.path.join(dataspace, r"buildings\geojson\Philadelphia\Philadelphia_building_hgt.geojson")
    out_building_block_path = os.path.join("./data/qgis_prj", "pipeline.geojson")

    with rasterio.open(image_path) as src:
        crs = src.crs
        left, bottom, right, top = src.bounds
        ref_poly = [box(minx=left, miny=bottom, maxx=right, maxy=top)]
    
    gdf = gpd.read_file(building_geojson_path)     
    crstrans = CRStrans()
    ref_poly = crstrans.transhapely(ref_poly, crs, "EPSG:4326")
    polygons_within_bounds = gdf[gdf.within(ref_poly)]
    polygons_within_bounds.to_file(out_building_block_path, driver="GeoJSON")
    

def batch_get_buildings_of_a_tile():
    dataspace = r"./dataset_roads/Europe"
    image_path = os.path.join(dataspace, r"cropped_images")
    building_geojson_path = os.path.join(dataspace, r"buildings\geojson\Atlanta\Atlanta_building_hgt.geojson")
    if os.path.exists(building_geojson_path):
        gdf = gpd.read_file(building_geojson_path) 
    
    
    images = os.listdir(image_path)
    for image in tqdm(images):
        scene_name = image.split("_")[0]
        if os.path.basename(building_geojson_path).split("_")[0] != scene_name:
            building_geojson_path = os.path.join(dataspace, rf"buildings\geojson\{scene_name}\{scene_name}_building_hgt.geojson")
            gdf = gpd.read_file(building_geojson_path) 
            print("read") 
        out_building_block_dir = os.path.join(dataspace, rf"buildings\tile_geojson\{scene_name}")
        os.makedirs(out_building_block_dir, exist_ok=True)
        out_building_block_path = os.path.join(out_building_block_dir, rf"{image.split('.')[0]}_hgt.geojson")

        with rasterio.open(os.path.join(image_path, image)) as src:
            crs = src.crs
            left, bottom, right, top = src.bounds
            ref_poly = [box(minx=left, miny=bottom, maxx=right, maxy=top)]
        
        crstrans = CRStrans()
        ref_poly = crstrans.transhapely(ref_poly, crs, "EPSG:4326")
        polygons_within_bounds = gdf[gdf.within(ref_poly)]
        if len(polygons_within_bounds) == 0:
            tt = gpd.GeoDataFrame({'geometry': [Point((0,0))]}, crs="EPSG:4326")
            tt.to_file(out_building_block_path, driver="GeoJSON")
        else:
            polygons_within_bounds.to_file(out_building_block_path, driver="GeoJSON")

if __name__ == "__main__":
    get_buildings_of_a_tile()
    # batch_get_buildings_of_a_tile()
    # generate_road_topo_fast()
    # generate_single_topo_fast()
    
    # generate_single_topo_fast_virtual()
    # trans_single_json_to_qgis(jsonpath=r"./dataset_roads/UnitedStates/urban_block_building/geojson/block_36000.json", \
    #                           outgeojson=r"./data/output/boundary_vis.geojson", scene_name="Philadelphia_tile_5916_5304")
    
    # vis_all_boundary_to_qgis(jsonpath=r"./dataset_roads/Europe/urban_block_building/geojson/block_total.json",\
    #     outgeojson=r"./dataset_roads/Europe/urban_block_building/boundary.geojson")

    # check_gpickle_boundary_to_qgis(gpicklepath=r"./dataset_roads/China_10m/topo_simplify/BeiJing_tile_0_895.gpickle",\
    #                                outdir=r"./data/output")
    # topopath = r"./dataset_roads/UnitedStates/topo_simplify/Philadelphia_tile_5916_2856.gpickle"
    # road_graph = nx.read_gpickle(topopath)
    # cycles = find_simple_cycles(copy.deepcopy(road_graph)) 
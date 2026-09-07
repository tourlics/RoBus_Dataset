import osm2gmns as og
import osmnx as ox
import networkx as nx
import os
import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
import pandas as pd
import rasterio
from scripts.basic_maths import Point2Pix
from scripts.tiff_operation import CRStrans
from shapely.geometry import LineString, Polygon
from tqdm import tqdm
import multiprocessing
from shapely.geometry import box

def drop_list_column(gdf):
    ## drop list-typed columns so the gdf can be saved as geojson
    for item in ['nodes', 'fishing','ways']:
        try:
            gdf = gdf.drop(columns=[item]) # list-typed; drop it
        except:
            continue
    return gdf

def worker_density(geo, reftiff):
    crstrans = CRStrans()
    with rasterio.open(reftiff) as ds:
        translist = []  
        pointlist = geo.coords[:-1]  
        for idx in range(len(pointlist)):  
            lon, lat = pointlist[idx][0], pointlist[idx][1]
            lat_dis, lon_dis = crstrans.lat2dis(lon, lat)
            tranx, transy = crstrans.lat2uv(ds, lon_dis, lat_dis)  
            translist.append((tranx, transy))
        allpoints = Point2Pix().linesDDA(translist)  
    return allpoints
      

    # with rasterio.open(global_reftiff) as ds:
    #     translist = []
    #     pointlist = geo.coords[:-1]
    #     crstrans = CRStrans()
    #     for idx in range(len(pointlist)):
    #         lat_dis, lon_dis = crstrans.lat2dis(pointlist[idx][0],pointlist[idx][1])
    #         transx, transy = crstrans.lat2uv(ds, lon_dis, lat_dis)
    #         translist.append([transx, transy])
    #     # increment density for every pixel each line traverses
    #     allpoints = Point2Pix().linesDDA(translist)
    return allpoints

class OSM2Roads:
    '''
    pasing osm roads
    '''
    def __init__(self, resolution) -> None:
        # self.tag_p1 = ['motorway', 'trunck', 'primary','secondary', 'motorway_link', 'trunck_link', 'primary_link','secondary_link', ]
        # self.tag_p2 = ['tertiary', 'tertiary_link', 'residential', 'living_street', 'road','unclassified']
        self.tag_p1 = ['motorway', 'trunck', 'primary']
        self.tag_p2 = ['secondary', 'tertiary', 'residential', 'unclassified']
        # self.tag_p1 = []
        # self.tag_p2 = ['residential', 'unclassified']
        
        self.resolution = resolution

        self.p1_pixel_buffer = [40] * len(self.tag_p1)  # road width in pixels per hierarchy; *5 for topology, *10 for public/graded maps
        self.p2_pixel_buffer = [20] * len(self.tag_p2)
    
    def osmnx_geojson_roads(self, inputfile, outputdir):
        tag_list = self.tag_p1
        tag_list.extend(self.tag_p2)

        for i in range(len(tag_list)):
            ctag = {'highway':tag_list[i]} 
            outputfile = os.path.join(outputdir, f'{tag_list[i]}.geojson')
            if os.path.exists(outputfile): 
                print(f"IGNORE {tag_list[i]}")
                continue
            print(f"processing {tag_list[i]}")
            gdf = ox.geometries_from_xml(inputfile, tags = ctag)
            if len(gdf) == 0: continue
            gdf = drop_list_column(gdf)
            
            gdf.to_file(outputfile, driver="GeoJSON") 
        print(f"geojson saved in {outputfile}!")

    # def osm2gmns_csv_roads(self, scene_name, inputdir, outputdir):
    #     # input: scene name (.osm file)
    #     # output: csv files (scene/road_type/.csv)
    #     outputpath = os.path.join(outputdir,scene_name)
    #     if not os.path.exists(outputpath):
    #         os.makedirs(outputpath)
        
    #     tag_list = ['primary', 'secondary', 'tertiary', 'residential', 'unclassified','motorway','trunck']

    #     inputfile = os.path.join(inputdir, f'{scene_name}.osm')

    #     for lt in tag_list:
    #         net = og.getNetFromFile(inputfile, link_types = lt)
    #         if net.number_of_nodes == 0: continue
    #         og.outputNetToCSV(net,output_folder = os.path.join(outputpath, lt))

    #     # save as csv for QGIS (includes nodes); when loading link.csv, pick the second wkt (well known text)
    #     net = og.getNetFromFile(inputfile)
    #     og.outputNetToCSV(net,output_folder = os.path.join(outputpath, "all"))
    #     print(f"csv saved in {outputpath}!")

    # def osmnx_networkx_roads(self, scene_name, inputdir, outputdir):
    #     try:
    #         raise NotImplementedError
    #     except NotImplementedError:
    #         print("osm to networkx is not implemented")

class OSM2Landuse:
    '''
    pasing osm landuse
    '''
    def __init__(self): 
        self.tags = {
            "landuse": ['forest', 'farmland', 'allotments', 'meadow', "scrub", "grass"],
            "natural": ['water', 'wood', 'wetland','glacier'],
            "water": ['reservoir', 'river'],
            "leisure": ['garden', 'nature_reserve'],
            "waterway": ["riverbank", "dock", "canal","drain", "ditch","stream","brook","wadi","drystream"]
        }
        self.all_waters = ['water', 'wetland','glacier', 'reservoir', 'river', "riverbank", "dock", "canal","drain", "ditch","stream","brook","wadi","drystream"]
        self.all_woods = ['forest', 'farmland','garden', 'wood', 'nature_reserve', 'allotments', 'meadow', "scrub", "grass"]
        
        all_item = []
        for key in self.tags.keys():
            all_item.extend(self.tags[key])
        assert len(self.all_waters)+len(self.all_woods) == len(all_item), "CHECK TAGS"

    def extract_landuse_tags(self, inputfile, outputdir):
        for tag in self.tags.keys():
            for item in self.tags[tag]:
                outputfile = os.path.join(outputdir, f"{item}.geojson")
                if os.path.exists(outputfile): 
                    print(f"IGNORE: {outputfile}")
                    continue
                print(f"extracting {outputfile}...")
                try:
                    gdf = ox.geometries_from_xml(inputfile, tags = {tag: item}, polygon=None)
                except:
                    print(f"FAILED {outputfile}")
                    continue
                if len(gdf) == 0: continue
                gdf = drop_list_column(gdf)
                gdf.to_file(outputfile, driver="GeoJSON") 
        return
    
    # def extract_forest_landuse(self, inputdir, outputdir, attributes):
    #     ctag = {"landuse":attributes} 
    #     inputfile = os.path.join(inputdir, f"{self.scene_name}.osm")
    #     gdf = ox.geometries_from_xml(inputfile, tags = ctag)
    #     if len(gdf) == 0: return
    #     gdf = drop_list_column(gdf)
    #     #print(gdf.dtypes)
    #     outputfile = os.path.join(outputdir, f"{self.scene_name}_forest.geojson")
    #     gdf.to_file(outputfile, driver="GeoJSON") 

    # def extract_water_natural(self, inputdir, outputdir, attributes):
    #     ctag = {"natural":attributes} 
    #     inputfile = os.path.join(inputdir, f"{self.scene_name}.osm")
    #     gdf = ox.geometries_from_xml(inputfile, tags = ctag)
    #     if len(gdf) == 0: return
    #     gdf = drop_list_column(gdf)
    #     #print(gdf.dtypes)
    #     outputfile = os.path.join(outputdir, f"{self.scene_name}_water.geojson")
    #     gdf.to_file(outputfile, driver="GeoJSON") 

    # def extract_water_water(self, inputdir, outputdir, attributes):
    #     ctag = {"water":attributes} 
    #     inputfile = os.path.join(inputdir, f"{self.scene_name}.osm")
    #     gdf = ox.geometries_from_xml(inputfile, tags = ctag)
    #     if len(gdf) == 0: return
    #     gdf = drop_list_column(gdf)
    #     #print(gdf.dtypes)
    #     outputfile = os.path.join(outputdir, f"{self.scene_name}_water2.geojson")
    #     gdf.to_file(outputfile, driver="GeoJSON") 
    
    # ### improvement: implement by merging gdfs
    # def get_landuse(self,inputdir, outputdir):
    #     forest_landuse = ['forest', 'nature_reserve']
    #     water_natural = ['water', 'glacier', 'wetland']
    #     water_water = ['reservoir', 'river']
        
    #     self.extract_forest_landuse(inputdir, outputdir, forest_landuse)
    #     self.extract_water_natural(inputdir, outputdir, water_natural)
    #     self.extract_water_water(inputdir, outputdir, water_water)

class OSM2POI:
    '''
    pasing Points of interest from osm
    '''
    def __init__(self): 
        self.tags = [
            {"highway":"bus_stop"},
            {"amenity":"bus_station"}
        ]
    def get_bus_stops(self, inputfile, outputdir):
        gdf_list = []
        for poi in self.tags:
            print(f"extracting {poi}...")
            gdf = ox.geometries_from_xml(inputfile, tags = poi)
            if len(gdf) == 0: continue
            gdf = drop_list_column(gdf)
            gdf_list.append(gdf)
            
        bus_station_gdf = pd.concat(gdf_list, axis=0, ignore_index=True)
        bus_station_gdf.to_file(os.path.join(outputdir, "bus_station.geojson"), driver='GeoJSON')
        return

class OSM2Orientation:
    '''
    pasing streets' bearings from osm
    '''
    def __init__(self, scene_names, ): 
        self.scene_names = scene_names

    def get_streets_bearings(self, inputdir, visfilename = None):
        n = len(self.scene_names)
        ncols = int(np.ceil(np.sqrt(n)))
        nrows = int(np.ceil(n / ncols))

        G_list = []
        Gu_list = []

        for place in sorted(self.scene_names):
            osmpath = os.path.join(inputdir, f"{place}.osm")
            G = ox.graph_from_xml(osmpath)
            Gu = ox.add_edge_bearings(ox.get_undirected(G))
            G_list.append(G)
            Gu_list.append(Gu)
        
        if visfilename:
            figsize = (ncols * 5, nrows * 5)
            fig, axes = plt.subplots(nrows, ncols, figsize=figsize, subplot_kw={"projection": "polar"})

            for idx, (ax, place) in enumerate(zip(axes.flat, sorted(self.scene_names))):
                # print(ox.utils.ts(), osmpath)
                G = G_list[idx]
                Gu = Gu_list[idx]
                fig, ax = ox.plot_orientation(Gu, ax=ax, title=place, area=True)

            # add figure title and save image
            suptitle_font = {
                "family": "DejaVu Sans",
                "fontsize": 60,
                "fontweight": "normal",
                "y": 1,
            }
            fig.suptitle("City Street Network Orientation", **suptitle_font)
            fig.tight_layout()
            fig.subplots_adjust(hspace=0.35)
            fig.savefig(os.path.join(visfilename), facecolor="w", dpi=100, bbox_inches="tight")
            plt.close()
        return G_list, Gu_list
    
class OSM2density:
    '''
    pasing streets' density or keypoints from osm
    '''
    def crop_linstring(self, line, valid_polygon):
        intersection = line.intersection(valid_polygon)
        # LineString intersection means the segment crosses the region
        if intersection.geom_type == 'LineString':
            clipped_line = intersection
            #print("LineString is clipped within the area.")
        # MultiLineString intersection means multiple segments inside the region
        elif intersection.geom_type == 'MultiLineString':
            clipped_line = intersection[0]  # take the first segment
            #print("LineString is clipped within the area in multiple segments.")
        else:
            #print("LineString does not intersect with the area.")
            clipped_line = line
        return clipped_line

    def cal_density(self, inputgeojson, valid_polygon):
        # read road-network geojson
        gdf = gpd.read_file(inputgeojson)
        # read road-network tiff
        geometry = gdf['geometry']
        crstrans = CRStrans()
        line_length_list = [] # road length inside the region
        for geo in geometry:
            #print(geo)
            translist = []
            pointlist = geo.coords[:]
            #print("********",(pointlist))
            for idx in range(len(pointlist)):
                tranx, trany = crstrans.lat2dis(pointlist[idx][0],pointlist[idx][1])
                #print(trany, tranx)
                translist.append((trany, tranx))
            line = LineString(translist)
            #print(line)
            clipped_line = self.crop_linstring(line, valid_polygon)
            line_length_list.append(clipped_line.length)
        total_length = sum(line_length_list)
        return total_length/valid_polygon.area


    def generate_gaussian_heatmap_large(self, density_map, sigma): 
        shape = density_map.shape
        points_idx = np.where(density_map!=0)
        points_x, points_y = points_idx[0], points_idx[1]
        points = [[a, b] for a, b in zip(points_x, points_y)] 
        heatmap = np.zeros(shape)  
        y, x = np.meshgrid(np.arange(shape[1]), np.arange(shape[0])) 
        
        for point in tqdm(points):
            px = np.tile(point[0].reshape(1,1), (x.shape[0], x.shape[1]))
            py = np.tile(point[1].reshape(1,1), (x.shape[0], x.shape[1]))

            # distance from each grid cell to all points
            distances = np.sqrt((px - x) ** 2 + (py - y) ** 2) 
            
            gaussian_values = np.exp(-0.5 * (distances / sigma) ** 2)  
            cur_heatmap = gaussian_values * (density_map+1)
            heatmap = np.maximum(heatmap, cur_heatmap)
        print(heatmap.shape)
        return heatmap  
    ## buggy; results are incorrect
    # def generate_gaussian_heatmap_small(self, density_map, sigma):  # only for small-resolution scenes; otherwise OOM
    #     shape = density_map.shape
    #     points_idx = np.where(density_map!=0)
    #     points_x, points_y = points_idx[0], points_idx[1]
    #     points = [[a, b] for a, b in zip(points_x, points_y)] 
    #     # init an all-zero heatmap
    #     heatmap = np.zeros(shape)  
        
    #     # grid coordinates
    #     y, x = np.meshgrid(np.arange(shape[1]), np.arange(shape[0])) 
    #     x_repeat = np.tile(x, (len(points), 1, 1)) 
    #     y_repeat = np.tile(y, (len(points), 1, 1))

    #     # points shape
    #     points = np.array(points).reshape(-1,2)
    #     px = points[:,0].reshape(-1,1,1)
    #     py = points[:,1].reshape(-1,1,1)

    #     points_x_repeat = np.tile(px, (1, x.shape[0], x.shape[1]))  
    #     points_y_repeat = np.tile(py, (1, x.shape[0], x.shape[1])) 
    #     # distance from each grid cell to all points
    #     distances = np.sqrt((x_repeat - points_x_repeat) ** 2 + (y_repeat - points_y_repeat) ** 2) 
    #     distances = np.max(distances, axis=0)
    #     # print(distances)
        
    #     # apply Gaussian; np.newaxis expands dims for broadcasting
    #     gaussian_values = np.exp(-0.5 * (distances / sigma) ** 2)  
    #     heatmap = gaussian_values * (density_map+1)
    #     return heatmap  

    def cal_geojson_to_density_map_large_multiprocess(self, geojsonlist, reftiff, outputfile, sigma):
        with rasterio.open(reftiff) as ds:
            width, hgt = (ds.width,ds.height)
            density = np.zeros((hgt,width))

        for ingeojson in geojsonlist:
            gdf = gpd.read_file(ingeojson)
            geometry = gdf['geometry']
            print(f"processing {ingeojson}, total of {len(geometry)} items...")
            with multiprocessing.Pool(processes=16) as pool:  
                allpoints_lists = pool.starmap(worker_density, [(geo, reftiff) for geo in geometry])
            for allpoints in allpoints_lists:
                for p in allpoints:
                    if p[0] >= hgt or p[1]>=width or p[0]<0 or p[1]<0: continue
                    density[p[0], p[1]] += 1

        heatmap = self.generate_gaussian_heatmap_small(density, sigma)
        with rasterio.open(outputfile, 'w', driver='GTiff', height=hgt, width=width, count=1, dtype=heatmap.dtype,
                        crs=ds.crs, transform=ds.transform) as dst:
            dst.write(heatmap, 1)

    # single-tiff path; still somewhat slow
    def cal_geojson_to_density_map_single_tiff(self, geojsonlist, reftiff, outputfile, sigma, issave=False):
        with rasterio.open(reftiff) as ds:
            width, hgt = (ds.width,ds.height)
            density = np.zeros((hgt,width))
            bounds = ds.bounds
            crstrans = CRStrans()  
            for ingeojson in geojsonlist:
                gdf = gpd.read_file(ingeojson)
                # bbox as (minx, miny, maxx, maxy)
                left, bottom, right, top = bounds
                rect_bounds = box(minx=left, miny=bottom, maxx=right, maxy=top)
                rect_bounds = crstrans.transhapely(rect_bounds, src_crs=ds.crs, dst_crs="EPSG:4326")
                # keep polygons that intersect the bbox
                geometry = gdf[gdf.intersects(rect_bounds)]
                if len(geometry) == 0: continue
                for geo in geometry["geometry"]:
                    ###### hot path start ######
                    translist = []  
                    pointlist = geo.coords[:-1]  
                    for idx in range(len(pointlist)):  
                        lon, lat = pointlist[idx][0], pointlist[idx][1]
                        lat_dis, lon_dis = crstrans.lat2dis(lon, lat)
                        tranx, transy = crstrans.lat2uv(ds, lon_dis, lat_dis)  
                        translist.append((tranx, transy))
                    allpoints = Point2Pix().linesDDA(translist) 
                    ###### hot path end ######
                    for p in allpoints:
                        if p[0] >= hgt or p[1]>=width or p[0]<0 or p[1]<0: continue
                        density[p[0], p[1]] += 1

        heatmap = self.generate_gaussian_heatmap_small(density, sigma)
        if not issave:
            return heatmap
        else:
            with rasterio.open(outputfile, 'w', driver='GTiff', height=hgt, width=width, count=1, dtype=heatmap.dtype,
                            crs=ds.crs, transform=ds.transform) as dst:
                dst.write(heatmap, 1)
    
    def cal_geojson_to_density_map_large(self, geojsonlist, reftiff, outputfile, sigma, issave=True):
        with rasterio.open(reftiff) as ds:
            width, hgt = (ds.width,ds.height)
            density = np.zeros((hgt,width))
            bounds = ds.bounds
            crstrans = CRStrans()  
            for ingeojson in geojsonlist:
                geometry = gpd.read_file(ingeojson)
                print(len(geometry))
                for geo in geometry["geometry"]:
                    ###### hot path start ######
                    translist = []  
                    pointlist = geo.coords[:-1]  
                    for idx in range(len(pointlist)):  
                        lon, lat = pointlist[idx][0], pointlist[idx][1]
                        lat_dis, lon_dis = crstrans.lat2dis(lon, lat)
                        tranx, transy = crstrans.lat2uv(ds, lon_dis, lat_dis)  
                        translist.append((tranx, transy))
                    allpoints = Point2Pix().linesDDA(translist) 
                    ###### hot path end ######
                    for p in allpoints:
                        if p[0] >= hgt or p[1]>=width or p[0]<0 or p[1]<0: continue
                        density[p[0], p[1]] += 1

        heatmap = self.generate_gaussian_heatmap_small(density, sigma)
        if not issave:
            return heatmap
        else:
            with rasterio.open(outputfile, 'w', driver='GTiff', height=hgt, width=width, count=1, dtype=heatmap.dtype,
                            crs=ds.crs, transform=ds.transform) as dst:
                dst.write(heatmap, 1)

    def estimate_density_map(self, reftiff, sigma):
        with rasterio.open(reftiff) as ds:
            width, hgt = (ds.width,ds.height)
            road_p1 = ds.read(1)
            road_p2 = ds.read(2)
            road_numpy = np.maximum(road_p1, road_p2)
        heatmap = self.generate_gaussian_heatmap_small(road_numpy, sigma)
        return heatmap
    
    def cal_geojson_to_density_map_very_slow(self, inputgeojson, inputtiff, outputfile):
        # read road-network geojson
        gdf = gpd.read_file(inputgeojson)
        # read road-network tiff
        geometry = gdf['geometry']
        with rasterio.open(inputtiff) as ds:
            width, hgt = (ds.width,ds.height)
            density = np.zeros((hgt+1,width+1))

        crstrans = CRStrans()
        for geo in geometry:
            translist = []
            pointlist = geo.coords[:-1]
            for idx in range(len(pointlist)):
                tranx, transy = crstrans.lat2uv(ds,pointlist[idx][0],pointlist[idx][1])
                translist.append((tranx, transy))
            # increment density for every pixel each line traverses
            allpoints = Point2Pix().linesDDA(translist)
            # print("********",allpoints)
            for p in allpoints:
                if p[0] > hgt or p[1]>width: continue
                density[p[0], p[1]] += 1

        # export density tiff
        with rasterio.open(outputfile, 'w', driver='GTiff', height=hgt, width=width, count=1, dtype=density.dtype,
                        crs=ds.crs, transform=ds.transform) as dst:
            dst.write(density, 1)
    
    def get_keypoints(self, inputgeojson, inputtiff, outputfile):
        # read road-network geojson
        gdf = gpd.read_file(inputgeojson)
        # read road-network tiff
        geometry = gdf['geometry']
        with rasterio.open(inputtiff) as ds:
            width, hgt = (ds.width,ds.height)
            density = np.zeros((hgt+1,width+1))

        crstrans = CRStrans()
        for geo in geometry:
            translist = []
            pointlist = geo.coords[:-1]
            for idx in range(len(pointlist)):
                tranx, transy = crstrans.lat2uv(ds,pointlist[idx][0],pointlist[idx][1])
                translist.append((tranx, transy))
            for p in translist:
                if p[0] > hgt or p[1]>width: continue
                density[p[0], p[1]] = 1
        # export tiff (keypoints)
        with rasterio.open(outputfile, 'w', driver='GTiff', height=hgt, width=width, count=1, dtype=density.dtype,
                        crs=ds.crs, transform=ds.transform) as dst:
            dst.write(density, 1)

class OSM2Buildings:
    '''
    pasing building contours from osm
    '''
    def __init__(self): 
        pass
    def extract_contours(self, inputosm, outputpath):
        ctag = {"building":True} 
        gdf = ox.geometries_from_xml(inputosm, tags = ctag)
        if len(gdf) == 0: return
        gdf = drop_list_column(gdf)
        outputfile = os.path.join(outputpath)
        gdf.to_file(outputfile, driver="GeoJSON") 
    
    # def reduce_buildings_poly(self, inputgeojson, outputgeojson):
    #     scene_name = os.path.basename(inputgeojson).split(".")[0].split("_")[0]
    #     gdf = gpd.read_file(inputgeojson)
    #     # read road-network tiff
    #     geometry = gdf['geometry']
    #     pass

    def crop_polygon(self, p, valid_polygon):
        clipped_polygon = p.intersection(valid_polygon)
        if clipped_polygon.geom_type == 'Polygon':
            clipped_polygon = clipped_polygon
        else:
            clipped_polygon = p
        return clipped_polygon
    def analyse_building_blocks(self, inputgeojson, valid_polygon):
        # read building geojson
        gdf = gpd.read_file(inputgeojson)
        
        geometry = gdf['geometry']
        crstrans = CRStrans()
        block_area_list = [] # building-block areas inside the region
        for geo in geometry:
            #print(geo)
            if geo.geom_type != 'Polygon': continue
            translist = []
            pointlist = geo.exterior.coords [:-1]
            for idx in range(len(pointlist)):
                tranx, trany = crstrans.lat2dis(pointlist[idx][0],pointlist[idx][1])
                #print(trany, tranx)
                translist.append((trany, tranx))
            p = Polygon(translist)
            #print(line)
            clipped_polygon = self.crop_polygon(p, valid_polygon)
            block_area_list.append(clipped_polygon.area)
        a_mean = np.mean(block_area_list)
        # variance
        a_var = np.var(block_area_list)
        # standard deviation
        a_std = np.std(block_area_list,ddof=1)
        return len(block_area_list), a_mean, a_var, a_std


    
if __name__ == "__main__":
    
    inputdir_osm = "./inputs_osm_zone"
    output_dir = "./outputs_data"
    for item in ["osmnx_geojson_road_zone", "buildings", "landuse"] :
        if not os.path.exists(os.path.join(output_dir, item)): os.makedirs(os.path.join(output_dir, item))

    scene_name_list = os.listdir(inputdir_osm)
    for item in scene_name_list:
        scene_name = item.split(".")[0]
        print(f"*********parsing {scene_name}.osm......**********")
        # parse roads
        roads = OSM2Roads()
        outputdir_geojson = os.path.join(output_dir,"osmnx_geojson_road_zone")
        # bug: osm2gmns output does not return control of the terminal
        #roads.osm2gmns_csv_roads(scene_name, inputdir_osm, outputdir_csv)
        roads.osmnx_geojson_roads(scene_name, inputdir_osm, outputdir_geojson)

        # # extract building contours
        # buildings = OSM2Buildings(scene_name)
        # outputdir_building = os.path.join(output_dir,"buildings")
        # buildings.extract_contours(inputdir_osm, outputdir_building)
        
        # # parse land-use types
        # landuse = OSM2Landuse(scene_name)
        # outputdir_landuse = os.path.join(output_dir,"landuse")
        # landuse.get_landuse(inputdir_osm, outputdir_landuse)

        # # parse road orientation entropy
        # # bug: requires at least two scenes
        # # bug: how to get a quantitative value?
        # scene_names = ["yuquan", "zijingang"] 
        # visfilename = os.path.join("./demo_output/orientation", "street_orientation.png")
        # orientation = OSM2Orientation(scene_names)
        # orientation.get_streets_bearings(inputdir_osm, visfilename)

        # # parse road-network density
        # inputgeojson = f'./demo_output/osmnx_geojson_roads/{scene_name}/residential.geojson'
        # inputtiff = f"./demo_output/rasterization/{scene_name}.tif"
        # outputfile = f'./demo_output/road_density/{scene_name}.tif'
        # density = OSM2density()
        # #density.cal_density(inputgeojson, inputtiff, outputfile)
        # outputfile = f'./demo_output/keypoints/{scene_name}.tif'
        # density.get_keypoints(inputgeojson, inputtiff, outputfile)

        # # get POI
        # points = OSM2POI()

    # # compute road-network density
    # scene_name = "map1_binjiang"
    # inputgeojson1 = f'./outputs_data/osmnx_geojson_roads/{scene_name}/primary.geojson'
    # inputgeojson2 = f'./outputs_data/osmnx_geojson_roads/{scene_name}/secondary.geojson'
    # inputgeojson3 = f'./outputs_data/osmnx_geojson_roads/{scene_name}/tertiary.geojson'
    # reftiff = f"./outputs_data/rasterization/{scene_name}_roads.tif"

    # with rasterio.open(reftiff) as tf:
    #     left, bottom, right, top = tf.bounds
    #     valid_polygon = Polygon(((left, top), (right, top), (right, bottom), (left, bottom)))
    #     print(valid_polygon)
    # # density = OSM2density()
    # # rden1 = density.cal_density(inputgeojson1, valid_polygon)
    # # rden2 = density.cal_density(inputgeojson2, valid_polygon)
    # # rden3 = density.cal_density(inputgeojson3, valid_polygon)
    # # print(rden1, rden2, rden3)
    # # print((rden1 + rden2 + rden3)*1000)
    # block = OSM2Buildings(scene_name)
    # inputgeojson = f'./outputs_data/buildings/{scene_name}_building.geojson'
    # num_blocks, a_mean, a_var, a_std = block.analyse_building_blocks(inputgeojson, valid_polygon)
    # print(num_blocks, a_mean, a_var, a_std)
    



import sys,os
import geopandas as gpd
import rasterio
from rasterio import features
from rasterio.crs import CRS
from rasterio.transform import Affine
import numpy as np
import sys,os
import geopandas as gpd
import pandas as pd
import rasterio
from rasterio import features
from rasterio.crs import CRS
from rasterio.transform import Affine
from rasterio.transform import from_origin
from rasterio.features import rasterize
import numpy as np
import pyproj
import csv
from shapely.geometry import Point,LineString
from scripts.tiff_operation import CRStrans, TIFoperation
from tqdm import tqdm

class Vec2Raster:
    '''
    convert vector file (.shp, .geojson) into rasterize file (.tif)
    '''
    def __init__(self,resolution):
        self.resolution = resolution
    def geojson2tiff_e4326(self,vecfile,raster):
        gdf = gpd.read_file(vecfile)
        geometry = gdf['geometry']
        bound = geometry.bounds
        width = int((bound.get('maxx').max()-bound.get('minx').min())/self.resolution)
        height = int((bound.get('maxy').max()-bound.get('miny').min())/self.resolution)
        # print(width,height)
        transform = Affine(self.resolution, 0.0, bound.get('minx').min(), 0.0, -self.resolution, bound.get('maxy').max())

        meta = {'driver': 'GTiff',
                'dtype': 'float32',
                'nodata': 0,
                'width': width,
                'height': height,
                'count': 1,
                'crs': gdf.crs,
                'transform': transform}

        with rasterio.open(raster, 'w+', **meta) as out:
            out_arr = out.read(1)
            shapes = ((geom,value) for geom, value in zip(gdf.get('geometry'), np.ones(len(geometry))))
            burned = features.rasterize(shapes=shapes, fill=0, out=out_arr, transform=out.transform)
            out.write_band(1, burned)
    

    def geojson2tiff_epsg(self,vecfiles,raster,buffer_widths, afterCoordSystem, fill_attr = None): # afterCoordSystem: target geographic CRS
        if len(vecfiles) == 0:            
            return False
        # afterCoordSystem="epsg:32650"  # UTM zone covering Shanghai
        # afterCoordSystem="epsg:3857"  # Web Mercator
        # rasterize multiple vector files in one pass
        bound_maxxs = []
        bound_maxys = []
        bound_minxs = []
        bound_minys = []
        gdfs = []
        for vecfile in vecfiles:
            # gdf = CRStrans().geotrans(vecfile, afterCoordSystem)
            gdf = gpd.read_file(vecfile)
            gdf = gdf.to_crs(afterCoordSystem)
            gdfs.append(gdf)

            geometry = gdf['geometry']
            bound = geometry.bounds
            bound_maxxs.append(bound.get('maxx').max())
            bound_maxys.append(bound.get('maxy').max())
            bound_minxs.append(bound.get('minx').min())
            bound_minys.append(bound.get('miny').min())
        bmaxx = max(bound_maxxs)
        bmaxy = max(bound_maxys)
        bminx = min(bound_minxs)
        bminy = min(bound_minys)

        width = int((bmaxx-bminx)/self.resolution)
        height = int((bmaxy-bminy)/self.resolution)
        transform = Affine(self.resolution, 0.0, bminx, 0.0, -self.resolution, bmaxy)

        meta = {'driver': 'GTiff',
                'dtype': 'float32',
                'nodata': 0,
                'width': width,
                'height': height,
                'count': 1,
                'crs': afterCoordSystem,
                'transform': transform}

        with rasterio.open(raster, 'w+', **meta) as out:
            out_arr = out.read(1)
            for idx, gdf in enumerate(gdfs):
                geometry = gdf["geometry"]
                if fill_attr is None:
                    shapes = ((geom,value) for geom, value in zip(gdf.get('geometry').buffer(buffer_widths[idx]), np.ones(len(geometry))))
                else:
                    shapes = [(feature["geometry"], float(feature[fill_attr])) for _, feature in gdf.iterrows()]
                burned = features.rasterize(shapes=shapes, fill=0, out=out_arr, transform=out.transform)
            out.write_band(1, burned)
        return True


    def shp2tiff():
        # TODO: shp to raster
        raise NotImplementedError

    def link2tiff(self, input_link):
        with open(input_link, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            link_data = list(reader)

        # project lon/lat to meter coordinates
        crs_wgs84 = pyproj.CRS('EPSG:4326')  # WGS84 CRS
        crs_utm = pyproj.CRS('EPSG:32650')  # UTM CRS
        transformer = pyproj.Transformer.from_crs(crs_wgs84, crs_utm, always_xy=True)

        # extract geometry coordinates
        geometries = []
        for link in tqdm(link_data):
            geometry = link['geometry']
            if geometry:
                coordinates = geometry.strip().replace('LINESTRING (', '').replace(')', '').split(', ')
                coordinates = [tuple(map(float, coord.split(' '))) for coord in coordinates]
                transformed_coords = [transformer.transform(coord[0], coord[1]) for coord in coordinates]
                line = LineString(transformed_coords)
                geometries.append(line)
        # compute raster size
        min_x = min(point[0] for line in geometries for point in line.coords)
        max_x = max(point[0] for line in geometries for point in line.coords)
        min_y = min(point[1] for line in geometries for point in line.coords)
        max_y = max(point[1] for line in geometries for point in line.coords)
        width = int((max_x - min_x) / self.resolution)+ 1
        height = int((max_y - min_y) / self.resolution)+ 1
        print(height, width)
        transform =  from_origin(min_x, max_y, self.resolution, self.resolution)
        meta = {'driver': 'GTiff',
                'dtype': 'float32',
                'nodata': 0,
                'width': width,
                'height': height,
                'count': 1,
                'crs': 'EPSG:32650',
                'transform': transform}

        with rasterio.open('link2tif.tif', 'w+', **meta) as out:
            out_arr = out.read(1)
            shapes =((geom, value) for geom, value in zip(geometries, np.ones(len(geometries))))
            burned = features.rasterize(shapes=shapes, fill=0, out=out_arr, transform=out.transform)
            out.write_band(1, burned)

def main_rasterize_roads():
    inputdir = "./outputs_data/osmnx_geojson_roads"
    outputdir = "H:/road_osm_rasterization/rasterization"
    if not os.path.exists(outputdir): os.makedirs(outputdir)

    levels = ['primary', 'secondary', 'tertiary', 'residential', 'unclassified','motorway','trunck']
    buffer_widths = [40, 25, 15, 10, 10, 50, 50] # [40, 24, 18, 10, 10, 50, 50]
    scene_name_list = os.listdir(inputdir)
    for scene_name in scene_name_list :
        if not os.path.exists(os.path.join(outputdir,scene_name)): 
            os.makedirs(os.path.join(outputdir,scene_name))
        else:
            print(f"***{scene_name} has been processed***")
            continue
        print(f"*********processing {scene_name}......**********")

        resolution = 5 # 5 m per pixel
        vec2ras = Vec2Raster(resolution)
        # rasterize each geojson separately
        for cur_level, buffer_width in zip(levels, buffer_widths):
            input_vec = os.path.join(inputdir, scene_name, f"{cur_level}.geojson")
            if not os.path.exists(input_vec): continue
            # # output_tif = f'./demo_output/rasterization/{scene_name}_e4326.tif'
            # # resolution = 0.0001 # 0.0001 degrees lon/lat
            # # Vec2Raster(resolution).geojson2tiff_e4326(input_vec, output_tif)
            output_tif = os.path.join(outputdir, scene_name, f'{cur_level}_rst{resolution}.tif')
            # preferred: more accurate resolution
            vec2ras.geojson2tiff_e32650([input_vec], output_tif, [buffer_width/2])
        
        # rasterize multiple geojsons (merge)
        merge_items = ['primary', 'secondary', 'tertiary']
        merge_buffer_widths = [40, 25, 15]
        merge_buffer_widths = [item/2 for item in merge_buffer_widths]
        inpath_vecs = []
        mit = ''
        for item in merge_items:
            if not os.path.exists( os.path.join(inputdir, scene_name,f"{item}.geojson") ): continue
            inpath_vecs.append(os.path.join(inputdir, scene_name,f"{item}.geojson"))
            mit += item[0]
        outpath = os.path.join(outputdir, scene_name, f'{scene_name}_{mit}_rst{resolution}.tif')
        vec2ras.geojson2tiff_e32650(inpath_vecs, outpath, merge_buffer_widths)

    # # convert link data to tiff
    # resolution = 10 # 10 m per pixel
    # input_link = './demo_output/osm2gmns_csv_roads/Hangzhou/primary/link.csv'
    # Vec2Raster(resolution).link2tiff(input_link)
    # # Vec2Raster(resolution).node_link2tiff(input_node, input_link)

def main_rasterize_buildings():
    inputdir = "./outputs_data/buildings"
    outputdir = "H:/road_osm_rasterization/rasterization_buildings"
    if not os.path.exists(outputdir): os.makedirs(outputdir)

    scene_list = os.listdir(inputdir)
    for scene in scene_list :
        
        output_tif = os.path.join(outputdir, f'{scene.split(".")[0]}.tif')
        if os.path.exists(output_tif): 
            print(f"***{scene} has been processed***")
            continue
        else:
            print(f"*********processing {scene}......**********")
            resolution = 5 # 5 m per pixel
            vec2ras = Vec2Raster(resolution)
            input_vec = os.path.join(inputdir, scene)
            vec2ras.geojson2tiff_e32650([input_vec], output_tif,[0])

if __name__ == '__main__':
    main_rasterize_buildings()
    #main_rasterize_roads()
    # TODO 0803: crop building tiff by road tiff; plus tiff crop helpers
    


    


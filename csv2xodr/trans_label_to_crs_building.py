import os
import json
from shapely.geometry import Point, Polygon
from shapely.affinity import rotate, translate
import random
import matplotlib.pyplot as plt
import rasterio
import sys
import geopandas as gpd
sys.path.append(r".")
sys.path.append(r"..")
sys.path.append(r"./data_preperation")

def vis_results(rectangles):
    for rect in rectangles:
        x, y = rect.exterior.xy
        plt.plot(x, y)

    plt.axis('equal')

    plt.show()

def random_rotate_rect_from_point(x,y):
    # Randomly sample rectangle width and height
    w = random.uniform(1.0, 3.5)  # length range [1.0, 5.0]
    h = random.uniform(1.0, 3.5)  # width range [1.0, 5.0]

    bottom_left = (-w / 2, -h / 2)
    bottom_right = (w / 2, -h / 2)
    top_right = (w / 2, h / 2)
    top_left = (-w / 2, h / 2)

    rectangle = Polygon([bottom_left, bottom_right, top_right, top_left, bottom_left])
    translated_rectangle = translate(rectangle, x, y)

    angle = random.uniform(0, 5)  # angle range [0, 360]
    # Rotate rectangle to form a new polygon
    rotated_rectangle = rotate(translated_rectangle, angle, origin='centroid')
    return rotated_rectangle

def trans_left_top_to_rect(left_top, right_bottom):
    x1, y1 = left_top
    x2, y2 = right_bottom
    # Derive the four corners from these two points
    top_right = (x2, y1)
    bottom_left = (x1, y2)
    # Create rectangle polygon
    rectangle = Polygon([left_top, top_right, right_bottom, bottom_left])
    return rectangle

def polygons2geojson(rectangles, reftiff, outpath):
    with rasterio.open(ref_tiff) as src:
        transform = src.transform
    from data_preperation.scripts.tiff_operation import CRStrans
    crstrans = CRStrans()
    poly_list = []
    building_hgt = []
    for rect in rectangles:
        r = crstrans.transshaply_uv_dis(transform, rect)
        r = crstrans.transhapely(r, "EPSG:3857", "EPSG:4326")
        poly_list.append(r)
        building_hgt.append(random.uniform(15, 21))
    buildings = gpd.GeoDataFrame({"geometry":poly_list, "building_hgt":building_hgt})
    buildings.to_file(outpath, driver="GeoJSON")


polygons = []
json_path = r"./data/qgis_prj/sr/demo.json"
with open(json_path, encoding='utf-8') as f:
    data = json.load(f)
    shapes = data["shapes"]
    for shape in shapes:
        label_name = shape["label"]     
        if label_name== "b":
            x,y = shape["points"][0][0], shape["points"][0][1]
            polygon = random_rotate_rect_from_point(x,y)
            polygons.append(polygon)
        if label_name=="r":
            left_top = shape["points"][0]
            right_bottom = shape["points"][1]
            rect = trans_left_top_to_rect(left_top, right_bottom)
            angle = random.uniform(0, 5)  # angle range [0, 360]
            rectangle = rotate(rect, angle, origin='centroid')
            polygons.append(rectangle)
        if label_name=="rb":
            left_top = shape["points"][0]
            right_bottom = shape["points"][1]
            rect = trans_left_top_to_rect(left_top, right_bottom)
            angle = random.uniform(5, 360)  # angle range [0, 360]
            rectangle = rotate(rect, angle, origin='centroid')
            polygons.append(rectangle)
            print(angle)
        if label_name=="e1":
            left_top = shape["points"][0]
            right_bottom = shape["points"][1]
            rect = trans_left_top_to_rect(left_top, right_bottom)
            angle = random.uniform(0,10)  # angle range [0, 360]
            angle  =0
            rectangle = rotate(rect, angle, origin='centroid')
            polygons.append(rectangle)
        if label_name=="e2":
            left_top = shape["points"][0]
            right_bottom = shape["points"][1]
            rect = trans_left_top_to_rect(left_top, right_bottom)
            angle = random.uniform(25, 40)  # angle range [0, 360]
            # angle = 0
            rectangle = rotate(rect, angle, origin='centroid')
            polygons.append(rectangle)

        if label_name== "t":
            x,y = shape["points"][0][0], shape["points"][0][1]
            polygon = random_rotate_rect_from_point(x,y)
            polygons.append(polygon)
        if label_name == 'p':
            polygons.append(Polygon([node for node in shape["points"]]))
# vis_results(polygons)
ref_tiff = os.path.join(r"./data/qgis_prj/sr", "Philadelphia_tile_5916_2856.tif")
out_path = os.path.join(r"./data/qgis_prj/sr", "demo_buildings.geojson")
polygons2geojson(polygons,ref_tiff, out_path)

        
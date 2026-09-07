import fiona
import rasterio
from rasterio.mask import mask
from rasterio.merge import merge
import sys,os
import geopandas as gpd
import rasterio
import numpy as np
import pyproj
import math
from PIL import Image
from shapely.geometry import  Polygon, box
from rasterio.transform import from_origin, from_bounds 
from rasterio.warp import calculate_default_transform, reproject
Image.MAX_IMAGE_PIXELS = 10**9
from rasterio.crs import CRS  
from shapely.ops import unary_union
import random

class CRStrans:
    '''
    convert tiff crs
    '''
    # epsg:4326 to pixel coordinates
    def lat2uv(self, raster, lon, lat):
        row, col = raster.index(lon, lat)  # corresponding row/col
        return row, col

    # pixel coordinates to epsg:4326
    def uv2lat(self, raster, row, col):
        lon, lat = raster.xy(row, col)  # center-pixel coordinates
        return lon, lat
    
    # epsg:4326 to epsg:32650
    def lat2dis(self, lon, lat):
        lat3,lon3 = pyproj.transform('epsg:4326','epsg:3857',lat,lon) # epsg:32650
        return lon3, lat3

    # pixel coordinates to epsg:32650
    def uv2dis(self, raster, row, col):
        lon, lat = raster.xy(row, col)
        lat3,lon3 = pyproj.transform('epsg:4326','epsg:3857',lat,lon)
        return lon3, lat3
    def dis2lat(self, lon, lat):
        lat3,lon3 = pyproj.transform('epsg:3857','epsg:4326',lat,lon) # epsg:32650
        return lon3, lat3
    
    def transhapely(self, geoms, src_crs, dst_crs):
        currentpoly = gpd.GeoSeries(geoms, crs=src_crs)
        transformedPoly = currentpoly.to_crs(dst_crs)
        crop_poly = transformedPoly[0]
        return crop_poly
    
    def transshaply_uv_dis(self, transformer, shaplyobj):
        obj_dis = []
        for row, col in list(shaplyobj.exterior.coords):
            # lon, lat = rasterio.transform.AffineTransformer(transformer).xy(row, col) # higher version
            lon, lat = transformer * (row, col) 
            obj_dis.append((lon, lat))
        return Polygon(obj_dis)

    def geotrans_depracated(self, invecfile, afterCoordSystem, outvecfile = None):
        import warnings
        try:
            warnings.warn("very slow!", DeprecationWarning)
        except Warning as e:
            print(e)

        # originCoordSystem = 'epsg:4326'  # source geographic CRS
        # afterCoordSystem = 'epsg:32650'  # target geographic CRS

        gdf = gpd.read_file(invecfile)
        originCoordSystem = gdf.crs
        # print(gdf.crs)
        # print(len(gdf))
        droplist=[]
        for i in range(0, len(gdf)):
            currentGeometry = gdf.loc[i, 'geometry']
            #print(currentGeometry.type)
            if str(currentGeometry.type) == 'MultiPolygon':
                #print("yes")
                droplist.append(i)
                #gdf.drop(gdf.index[i])
        gdf.drop(droplist,inplace=True)
        gdf.reset_index(drop=True, inplace=True)
        #print(droplist)
        # print(len(gdf))
        for i in range(0, len(gdf)):
            # read current line geometry
            currentGeometry = gdf.loc[i, 'geometry']
            if str(currentGeometry.type) == 'MultiPolygon':
                print("Warning: ignore MultiPolygon!!!")
                continue
            currentLine = gpd.GeoSeries(currentGeometry, crs=originCoordSystem)
            transformedLine = currentLine.to_crs(afterCoordSystem)
            # print(transformedLine[0]) # take index 0
            # replace original geometry with transformed line
            gdf.loc[i, 'geometry'] = transformedLine[0]
        if outvecfile:
            gdf.to_file(outvecfile, driver='GeoJSON', encoding="GB2312")
        return gdf
        

class TIFoperation:
    def read_shp(inputshp):
        with fiona.open(inputshp, "r", encoding='utf-8') as shapefile:
            # obtain all the points of the polygon
            geoms = [feature["geometry"] for feature in shapefile]
            return geoms

    def crop_tiff_from_boundary(self, inputtiff, geoms, outputtiff):
        # crop image by boundary polygon
        # geoms is a list
        with rasterio.open(inputtiff) as src:
            out_image, out_transform = mask(src, geoms, crop=True)
            out_meta = src.meta.copy()
        # update metadata for the output file
        out_meta.update({"driver": "GTiff",
                        "height": out_image.shape[1],
                        "width": out_image.shape[2],
                        "transform": out_transform})

        with rasterio.open(outputtiff, "w", **out_meta) as dest:
            dest.write(out_image)
        
        return

    def filter_cropped_tiff(self, tile):
        img = np.array(tile).astype(np.float32)
        if len(img[img==1])>10000:
            return False
        else:
            return True
        
    def crop_tiff_from_pixel(self, inputtiff, pixel_rect, outputtiff):
        # crop image by pixel rect: top-left, bottom-right
        with rasterio.open(inputtiff) as src:    
            data = src.read(1)  # assume single-band TIFF
        tile = data[pixel_rect[0][0]:pixel_rect[1][0], pixel_rect[0][1]:pixel_rect[1][1]]
        if self.filter_cropped_tiff(tile): return
        rect_shape = (pixel_rect[1][0]-pixel_rect[0][0], pixel_rect[1][1]-pixel_rect[0][1])
        # rewrite src metadata
        meta = src.meta.copy()  
        meta.update({"driver": "GTiff",  
                    "height": rect_shape[0],  
                    "width": rect_shape[1],  
                    "transform": src.transform,  
                    "crs": src.crs})  
        with rasterio.open(outputtiff, "w", **meta) as dst:  
            dst.write(tile, 1)  # write merged data to band 1
    
    def crop_tiff_from_pixel_multichannels_slow_ignorepos(self, inputtiff, pixel_rect, outputtiff):
        with rasterio.open(inputtiff) as src:    
            data = src.read()  
        tile = data[:,pixel_rect[0][0]:pixel_rect[1][0], pixel_rect[0][1]:pixel_rect[1][1]]
        # if self.filter_cropped_tiff(tile[0]): return
        rect_shape = (pixel_rect[1][0]-pixel_rect[0][0], pixel_rect[1][1]-pixel_rect[0][1])
        # rewrite src metadata
        meta = src.meta.copy()  
        meta.update({"driver": "GTiff",  
                    "height": rect_shape[0],  
                    "width": rect_shape[1],  
                    "transform": src.transform,  
                    "crs": src.crs})  
        with rasterio.open(outputtiff, "w", **meta) as dst:  
            dst.write(tile)

    def crop_tiff_from_pixel_multichannels_ignorepos(self, inputpath, non_overlap, target_size, out_imagedir):
        with rasterio.open(inputpath) as src:
            image_width = src.width
            image_height = src.height
            data = src.read()  
        step = int(non_overlap*target_size)
        scene_name = os.path.basename(inputpath).split(".")[0]
        tifopr = TIFoperation()
        for i in range(0, image_height-target_size, step):
            print(f"cropping {scene_name}: {i}th of total {image_height-target_size}...")
            for j in range(0, image_width-target_size, step):
                pixel_rect = [(i, j), (i+target_size, j+target_size)] # top-left, bottom-right
                tile = data[:,pixel_rect[0][0]:pixel_rect[1][0], pixel_rect[0][1]:pixel_rect[1][1]]
                # if self.filter_cropped_tiff(tile[0]): return
                rect_shape = (pixel_rect[1][0]-pixel_rect[0][0], pixel_rect[1][1]-pixel_rect[0][1])
                # rewrite src metadata
                meta = src.meta.copy()  
                meta.update({"driver": "GTiff",  
                            "height": rect_shape[0],  
                            "width": rect_shape[1],  
                            "transform": src.transform,  
                            "crs": src.crs})  
                outputfile = os.path.join(out_imagedir, f"{scene_name}_tile_{i}_{j}.tif")
                with rasterio.open(outputfile, "w", **meta) as dst:  
                    dst.write(tile)
    
    def crop_tiff_randomly(self, inputpath, target_size, num_crops, out_imagedir):
        with rasterio.open(inputpath) as src:
            image_width = src.width
            image_height = src.height
            transformer = src.transform
            scene_name = os.path.basename(inputpath).split(".")[0]
            crstrans = CRStrans()
        
            for crop_index in range(num_crops):
                # random top-left corner
                i = random.randint(0, image_width - target_size)
                j = random.randint(0, image_height - target_size)
                
                print(f"Random cropping {scene_name}: {crop_index + 1}th crop at position ({i}, {j})...")
                
                outputfile = os.path.join(out_imagedir, f"{scene_name}_tile_{crop_index + 1}.tif")
                if os.path.exists(outputfile):
                    continue
                
                crop_box_uv = box(minx=i, miny=j, maxx=i + target_size, maxy=j + target_size)
                crop_box = crstrans.transshaply_uv_dis(transformer, crop_box_uv)
                out_image, out_transform = rasterio.mask.mask(src, [crop_box], crop=True)
                
                out_meta = src.meta.copy()
                out_meta.update({
                    "driver": "GTiff",
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform,
                    "crs": src.crs
                })
                
                with rasterio.open(outputfile, "w", **out_meta) as dst:
                    dst.write(out_image)

    def crop_tiff_from_pixel_multichannels(self, inputpath, non_overlap, target_size, out_imagedir):
        with rasterio.open(inputpath) as src:
            image_width = src.width
            image_height = src.height
            transformer = src.transform
            step = int(non_overlap*target_size)
            scene_name = os.path.basename(inputpath).split(".")[0]
            crstrans = CRStrans()
            for i in range(0, image_width-target_size, step):
                print(f"cropping {scene_name}: {i}th of total {image_width-target_size}...")
                for j in range(0, image_height-target_size, step):
                    # pixel_rect = [(i, j), (i+target_size, j+target_size)] # top-left, bottom-right
                    outputfile = os.path.join(out_imagedir, f"{scene_name}_tile_{i}_{j}.tif")
                    if os.path.exists(outputfile): continue
                    crop_box_uv = box(minx=i, miny=j, maxx=i+target_size, maxy=j+target_size)
                    crop_box = crstrans.transshaply_uv_dis(transformer,crop_box_uv)
                    out_image, out_transform = rasterio.mask.mask(src, [crop_box], crop=True)
                    # print(out_image.shape,i,j)
                    out_meta = src.meta.copy()
                    out_meta.update({"driver": "GTiff",  
                                "height": out_image.shape[1],  
                                "width": out_image.shape[2],  
                                "transform": out_transform,  
                                "crs": src.crs})
                    
                    with rasterio.open(outputfile, "w", **out_meta) as dst:  
                        dst.write(out_image)
    # distance from lat/lon
    def getDistance(self, latA, lonA, latB, lonB):
        ra = 6378140  # equatorial radius
        rb = 6356755  # polar radius
        flatten = (ra - rb) / ra  # Partial rate of the earth
        radLatA = math.radians(latA)
        radLonA = math.radians(lonA)
        radLatB = math.radians(latB)
        radLonB = math.radians(lonB)
        pA = math.atan(rb / ra * math.tan(radLatA))
        pB = math.atan(rb / ra * math.tan(radLatB))
        x = math.acos(math.sin(pA) * math.sin(pB) + math.cos(pA) * math.cos(pB) * math.cos(radLonA - radLonB))
        c1 = (math.sin(x) - x) * (math.sin(pA) + math.sin(pB)) ** 2 / math.cos(x / 2) ** 2
        c2 = (math.sin(x) + x) * (math.sin(pA) - math.sin(pB)) ** 2 / math.sin(x / 2) ** 2
        dr = flatten / 8 * (c1 - c2)
        distance = ra * (x + dr)
        distance = round(distance, 4)
        return distance
    
    # ground distance between two pixels
    def distance_pixels(self, raster, px1, px2):    
        raster_crs = raster.crs # 'epsg:4326'
        a,b = px1
        c,d = px2
        xa, yb = raster.xy(a, b)
        xc, yd = raster.xy(c, d)
        yb_3,xa_3 = pyproj.transform(raster_crs,'epsg:32650',yb,xa)
        yd_3,xc_3 = pyproj.transform(raster_crs,'epsg:32650',yd,xc)
        distance = ((xa_3-xc_3)**2 + (yb_3-yd_3)**2) ** 0.5
        print(f'distance in epsg:32650 is {distance}m')
        # estimate from lat/lon-distance relation https://blog.csdn.net/welcome_yu/article/details/114766633
        distance2 = self.getDistance(yb,xa,yd,xc)
        print(f'distance estimated from lat/lon is {distance2}m')

        return distance

    def split_tiff(self, tiff_path, tile_width, tile_height):
        # open TIFF to split
        img_path = os.path.join(tiff_path, 'primary.tif')
        image = Image.open(img_path)
        image_width, image_height = image.size

        # number of tile columns and rows
        num_tiles_x = image_width // tile_width
        num_tiles_y = image_height // tile_height
        print(num_tiles_y, num_tiles_x)
        #split tiff image
        for y in range (num_tiles_y):
            for x in range (num_tiles_x):
                # tile top-left and bottom-right
                left = x * tile_width
                upper = y * tile_height
                right = left + tile_width
                lower = upper + tile_height

                # extract tile
                tile = image.crop((left, upper, right, lower))

                # save tile
                os.makedirs(f"{tiff_path}/split",exist_ok=True)
                outputfile = os.path.join(f"{tiff_path}/split", f"tile_{y*num_tiles_x+x}.tiff")
                tile.save(outputfile)

        # close image
        image.close()
  
    def resize_tiff(self, tiffpath, outputpath, scale_factor=4): 
        with rasterio.open(tiffpath) as src_ds:
            # affine transform and size in the new CRS
            dst_transform, dst_width, dst_height = calculate_default_transform(
                src_ds.crs, # source CRS
                src_ds.crs, # destination CRS
                src_ds.width, # source width
                src_ds.height, # source height
                dst_width = int(src_ds.width // scale_factor),
                dst_height = int(src_ds.height // scale_factor),
                *src_ds.bounds) # source bounds
            
            # update dataset metadata
            profile = src_ds.meta.copy()
            profile.update({
                'crs': src_ds.crs,
                'transform': dst_transform,
                'width': dst_width,
                'height': dst_height
                })

            # reproject and write
            with rasterio.open(outputpath, 'w', **profile) as dst_ds:
                # for i in range(1, src_ds.count + 1): # iterate bands; usually band 1 is enough
                src_array = src_ds.read(1)
                dst_array = np.empty((dst_height, dst_width), dtype=profile['dtype']) # init output array
                # reproject
                reproject(
                    # source args
                    source=src_array,
                    src_crs=src_ds.crs,
                    src_transform=src_ds.transform,
                    # destination args
                    destination=dst_array,
                    dst_transform=dst_transform,
                    dst_crs=src_ds.crs,)
                # write image
                dst_ds.write(dst_array, 1)

    def convert_polygon_to_integers(self,polygon):    
        # polygon exterior coords
        coords = list(polygon.exterior.coords)  
        # convert coords to integers
        integer_coords = [(int(round(x)), int(round(y))) for x, y in coords]  
        integer_polygon = Polygon(integer_coords)  
        return integer_polygon
    
    def concate_tiffs(self, tiff_files, output_file):
        concated_file = []
        for tif_f in tiff_files:
            src = rasterio.open(tif_f)
            concated_file.append(src)
        mosaic, out_trans = merge(concated_file)

        out_meta = src.meta.copy()
        # update metadata; set "crs" to the required coordinate system
        out_meta.update({"driver": "GTiff",
                        "height": mosaic.shape[1],
                        "width": mosaic.shape[2],
                        "transform": out_trans,
                        "crs": "+proj=utm +zone=49 +datum=WGS84 +units=m +no_defs"
                        }
                        )
        # save file
        with rasterio.open(output_file, "w", **out_meta) as dest:
            dest.write(mosaic)

    def align_two_tif(self, tif1path, tif2path, outpath):
        with rasterio.open(tif1path) as t1p:
            left, bottom, right, top = t1p.bounds
            poly1 = Polygon(((left, top), (right, top), (right, bottom), (left, bottom)))
            # import matplotlib.pyplot as plt
            # plt.plot(*poly1.exterior.xy)
            
        with rasterio.open(tif2path) as t2p:
            left, bottom, right, top = t2p.bounds
            poly2 = Polygon(((left, top), (right, top), (right, bottom), (left, bottom)))
            # plt.plot(*poly2.exterior.xy)
        if poly1.intersects(poly2):
            poly = poly1.intersection(poly2)
            # plt.plot(*poly.exterior.xy)
            # plt.show()
        else:
            print("No intersection!!!")
            return
        align1_path = os.path.join(outpath, os.path.basename(tif1path))
        align2_path = os.path.join(outpath, os.path.basename(tif2path))
        # poly = self.convert_polygon_to_integers(poly)
        self.crop_tiff_from_boundary(tif1path, [poly], align1_path)
        self.crop_tiff_from_boundary(tif2path, [poly], align2_path)
        # # crop road and building TIFFs separately
        # scene_name = str(os.path.split(outpath)[-1])
        # self.crop_tiff_from_boundary(tif1path, [poly], os.path.join(outpath, f"{scene_name}_roads.tif"))
        # self.crop_tiff_from_boundary(tif2path, [poly], os.path.join(outpath, f"{scene_name}_buildings.tif"))

    def align_multiple_tif(self, tifpath_list, outpath): # default: use the first image as reference
        # get common-area polygon
        reftiff = tifpath_list[0]
        with rasterio.open(reftiff) as ref:
            left, bottom, right, top = ref.bounds
            refpoly = Polygon(((left, top), (right, top), (right, bottom), (left, bottom)))
        for idx in range(1, len(tifpath_list)):
            tiff_path = tifpath_list[idx]
            with rasterio.open(tiff_path) as cur_tiff:
                left, bottom, right, top = cur_tiff.bounds
                cur_poly = Polygon(((left, top), (right, top), (right, bottom), (left, bottom)))
                if refpoly.intersects(cur_poly):
                    refpoly = refpoly.intersection(cur_poly)
                else:
                    raise ValueError
                
        for tifpath in tifpath_list:
            align_path = os.path.join(outpath, f"{os.path.basename(tifpath)}.tiff")
            self.crop_tiff_from_boundary(tifpath, [refpoly], align_path)


  
    def merge_multiple_tif_channel(self, inputfiles, outputfile):
        bounds = [rasterio.open(f).bounds for f in inputfiles]  
        minx = max(b.left for b in bounds)  
        miny = max(b.bottom for b in bounds)  
        maxx = min(b.right for b in bounds)  
        maxy = min(b.top for b in bounds) 
        common_poly = Polygon([(minx, miny), (minx, maxy), (maxx, maxy), (maxx, miny)])

        with rasterio.open(inputfiles[0]) as src: 
            out_image, out_transform = mask(src, [common_poly], crop=True)
            out_meta = src.meta.copy()
            bounds = src.bounds  
            transform = src.transform  
            crs =src.crs  
            res =src.res  
            dtype = src.dtypes[0]   
            
        shape1 = 1000000
        shape2 = 1000000
        for i, file in enumerate(inputfiles):  
            with rasterio.open(file) as cur:  
                cur_image, cur_transform = mask(cur, [common_poly], crop=True) 
                shape1 = min(cur_image.shape[1], shape1)
                shape2 = min(cur_image.shape[2], shape2)

        data = np.empty((len(inputfiles), shape1, shape2), dtype=dtype) 
        # read each file into the data array
        for i, file in enumerate(inputfiles):  
            with rasterio.open(file) as cur:  
                cur_image, cur_transform = mask(cur, [common_poly], crop=True) 
                data[i, :data.shape[1], :data.shape[2]] = cur_image[0,:data.shape[1], :data.shape[2]] 
        
        # write merged GeoTIFF
        profile = {  
            'driver': 'GTiff',  
            'height': data.shape[1],  
            'width': data.shape[2],  
            'count': data.shape[0],  # band count
            'dtype': dtype,  
            'crs': crs,  
            'transform': transform,   
            'tiled': True,  
        } 
        with rasterio.open(outputfile, 'w', **profile) as dst:  
            dst.write(data)


    def union_two_tif(self, tif1path, tif2path, outpath):
        # open first TIFF
        with rasterio.open(tif1path) as src1:  
            # read first file pixels
            data1 = src1.read(1)  # assume single-band TIFF
        # open second TIFF
        with rasterio.open(tif2path) as src2:  
            # require same bounds and resolution as the first file
            assert src1.res == src2.res, "Resolutions do not match"  
            # read second file pixels
            data2 = src2.read(1)  # also assume single-band
        # crop rounding may cause a 1-pixel size mismatch
        merge_shape = (min(data1.shape[0], data2.shape[0]), min(data1.shape[1], data2.shape[1]))

        # rewrite src1  
        meta = src1.meta.copy()  
        meta.update({"driver": "GTiff",  
                    "height": merge_shape[0],  
                    "width": merge_shape[1],  
                    "transform": src1.transform,  
                    "crs": src1.crs})  
        with rasterio.open(tif1path, "w", **meta) as dst:  
            dst.write(data1[:merge_shape[0],:merge_shape[1]], 1)  # write merged data to band 1

        # rewrite src2  
        meta = src2.meta.copy()  
        meta.update({"driver": "GTiff",  
                    "height": merge_shape[0],  
                    "width": merge_shape[1],  
                    "transform": src2.transform,  
                    "crs": src2.crs})  
        with rasterio.open(tif2path, "w", **meta) as dst:  
            dst.write(data2[:merge_shape[0],:merge_shape[1]], 1)  # write merged data to band 1
        
        # merge pixels by addition (union may need more complex logic)
        merged_data = data1[:merge_shape[0],:merge_shape[1]] + data2[:merge_shape[0],:merge_shape[1]] 
        merged_data[merged_data>1] = 1 
        # create output file
        with rasterio.open(outpath, "w", **meta) as dst:  
            dst.write(merged_data, 1)  # write merged data to band 1

    def tiff_crs_trans(self, originpath, outpath, dst_crs="EPSG:4326"):
        # open source TIFF
        with rasterio.open(originpath) as src:  
            # get source metadata
            meta = src.meta  
            meta.update({"crs": CRS.from_string(dst_crs)})  
            # compute transform in the new CRS
            transform, width, height = calculate_default_transform(  
                src.crs, meta['crs'], src.width, src.height, *src.bounds  
            )  
            # update transform and dimensions in metadata
            meta.update({"transform": transform, "width": width, "height": height}) 
            # create a new Rasterio dataset for the reprojected data
            with rasterio.open(outpath, 'w', **meta) as dst:  
                # reproject image data
                reproject(  
                    source=rasterio.band(src, 1),  
                    destination=rasterio.band(dst, 1),  
                    src_transform=src.transform,  
                    src_crs=src.crs,  
                    dst_transform=transform,  
                    dst_crs=meta['crs'],  
                    resampling=rasterio.enums.Resampling.bilinear  
                )  

if __name__ == "__main__":
    # scene_name = "hangzhou"
    # inputtiff = f"./demo_output/rasterization/{scene_name}_e4326.tif"
    # #inputtiff = f"./demo_output/rasterization/{scene_name}_e32650.tif"
    # crstrans = CRStrans()
    tifopr = TIFoperation()
    # with rasterio.open(inputtiff) as ds:
    #     # coordinate transform
    #     lon, lat = (ds.bounds.left, ds.bounds.top)  # top-left epsg:4326 coords
    #     row, col = crstrans.lat2uv(ds, lon, lat)
    #     print(f'epsg:4326 coords {lon}, {lat} map to pixel ({row}, {col})')
    #     lon, lat = crstrans.uv2lat(ds, row, col)
    #     print(f'pixel ({row}, {col}) maps to epsg:4326 ({lon}, {lat})')
    #     lon3, lat3 = crstrans.lat2dis(lon, lat)
    #     print(f'epsg:4326 ({lon}, {lat}) maps to epsg:32650 ({lon3}, {lat3})')
    #     lon3, lat3 = crstrans.uv2dis(ds, row, col)
    #     print(f'pixel ({row}, {col}) maps to epsg:32650 ({lon3}, {lat3})')
    #
    #     # compute distance
    #     px1 = (10,10)
    #     px2 = (10,20)
    #     distance = tifopr.distance_pixels(ds, px1, px2)
    
    
    # # crop tiff
    # inputtiff = './demo_input/chn_pd_2020_1km.tif'
    # inputshp = "./demo_input/shp/hangzhou/hangzhou.shp"
    # geoms = tifopr.read_shp(inputshp)
    # outputtiff = "./demo_output/population/hangzhou.tif"
    # tifopr.crop_tiff(inputtiff, geoms, outputtiff)

    # # split tiff
    # tifopr = TIFoperation()
    # tiff_path = f"./demo_output/rasterization/{scene_name}"
    # tile_width = 256
    # tile_height = 256
    # tifopr.split_tiff(tiff_path, tile_width, tile_height)

    # align and crop two tiffs
    base_dir = "H:/road_osm_rasterization/rasterization"
    scene_name_list = []
    for item in os.listdir(base_dir):
        scene_name_list.append(item)
    for scene_name in scene_name_list:
        tif1path = None
        for filename in os.listdir(os.path.join(base_dir,scene_name)):
            if filename.startswith(scene_name): 
                tif1path = os.path.join(base_dir,scene_name,filename)
        if tif1path is None:
            print("missed file!!!")
            break
        tif2path = f"H:/road_osm_rasterization/rasterization_buildings/{scene_name}_building.tif"
        outpath = f"H:/road_osm_rasterization/rasterization_aligned/{scene_name}"
        if not os.path.exists(outpath): 
            os.makedirs(outpath)
            print(f"**********processing {scene_name}...***********")
        else:
            print(f"**{scene_name} processed**")
            continue
        tifopr.align_two_tif(tif1path,tif2path,outpath)
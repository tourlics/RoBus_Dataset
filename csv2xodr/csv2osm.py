import pandas as pd
import numpy as np
import re

# 1. Load raw point data
def read_data(path,dtype):
    # Read header
    head_row = pd.read_csv(path, nrows=0) 
    # Convert header columns to list
    head_row_list = list(head_row)
    # Read
    csv_result = pd.read_csv(path,usecols=head_row_list,dtype=dtype)#{'lon':np.float64,'lat':np.float64}
    # row_list = csv_result.values.tolist()
    proj = f"+proj=tmerc +lat_0={csv_result['lat'].loc[0]} +lon_0={csv_result['lon'].loc[0]}"
    return csv_result,proj

def read_attributes(path):
    # Read header
    head_row = pd.read_csv(path, nrows=0) 
    # Convert header columns to list
    head_row_list = list(head_row)
    # Read
    attributes = pd.read_csv(path,usecols=head_row_list)#{'lon':np.float64,'lat':np.float64}
    road_attr_dict = {}
    for i in range(len(attributes)):
        group_id = attributes['group_id'].loc[i]
        attr = attributes['attribute'].loc[i]
        road_attr_dict[group_id] = attr
    return road_attr_dict

# 2. Helper functions
# Create a node element
def creat_node(id,lon,lat):
    # lon = lon - 112.1851171
    # lat = lat - 30.91744581
    content = ' <node id='+'"'+str(id)+'" '+'version = "3" '+'lat='+'"'+str(lat)+'" '+'lon='+'"'+str(lon)+'"/>'
    return content
# Create a way element
def creat_way(id,node_list):
    head = ' <way id="'+str(id)+'" version = "3" >' 
    end  = ' </way>'
    content = []
    for node_id in node_list:
        content.append('  <nd ref="'+str(node_id)+'"/>')

    return head , content , end
# 3. Generate files
def csv2osm_main(roadcsv, attrcsv, outosm, outproj):
    node_list = []
    way_list = []
    # OSM boilerplate
    osm_head1 = '<?xml version="1.0" encoding="UTF-8"?>'
    osm_head2 = '<osm version="0.6" >'
    osm_end = '</osm>'
    # Load data
    print(roadcsv)
    data,proj = read_data(roadcsv,dtype = {'lon':np.float64,'lat':np.float64})
    # Write proj string
    print(proj)
    with open(outproj,"w+") as f:
        f.write(proj)

    road_attr_dict = read_attributes(attrcsv)
    # Build OSM elements
    for i in range(len(data)):
        id = data['id'].loc[i]
        lon = data['lon'].loc[i]
        lat = data['lat'].loc[i]
        node_content = creat_node(id,lon,lat)
        node_list.append(node_content)
    
    group_id_save = []
    way_list_ = {}
    for i in range(len(data)):
        id = data['id'].loc[i]
        group_id = data['group_id'].loc[i]    
        if group_id in group_id_save:
            way_list_[group_id].append(id)
        else:
            group_id_save.append(group_id)
            way_list_[group_id] = [id]
    for id in way_list_:
        head , content , end = creat_way(id,way_list_[id])
        way_list.append([head,content,end])
    
    # Write OSM file
    Note=open(outosm,mode='w')
    Note.write(osm_head1+'\n')
    Note.write(osm_head2+'\n')
    
    for row in node_list:
        Note.write(row+'\n')
    for row in way_list:
        Note.write(row[0]+'\n')
        cur_group_id = int( re.findall(r'id="(.*?)"',row[0])[0] )
        cur_road_attribute = road_attr_dict[cur_group_id]
        for nd in row[1]:
            Note.write(nd+'\n')    
        Note.write(f'  <tag k="highway" v="{cur_road_attribute}"/>\n') # set highway type
        Note.write(row[2]+'\n')
    
    Note.write(osm_end+'\n')
    Note.close()


if __name__ == "__main__":
    # num_samples = 40
    # for i in range(num_samples):
    #     cur_scene_name = f"custom{i}"
    #     roadcsv = f"./demo/csv/{cur_scene_name}_roads.csv"
    #     attrcsv = f"./demo/csv/{cur_scene_name}_attributes.csv"
    #     outosm = f'./demo/osm/{cur_scene_name}.osm'
    #     outproj = f'./demo/proj/{cur_scene_name}.txt'
    #     csv2osm_main(roadcsv, attrcsv, outosm, outproj)
    #     print(f'{cur_scene_name} csv converted to osm successfully!')

    # cur_scene_name = f"customY"
    # roadcsv = f"./demo/csv/{cur_scene_name}_roads.csv"
    # attrcsv = f"./demo/csv/{cur_scene_name}_attributes.csv"
    # outosm = f'./demo/osm/{cur_scene_name}.osm'
    # outproj = f'./demo/proj/{cur_scene_name}.txt'
    # csv2osm_main(roadcsv, attrcsv, outosm, outproj)
    # print(f'{cur_scene_name} csv converted to osm successfully!')

    # ###20231017
    # cur_scene_name = f"002"
    # roadcsv = f"./../data_preperation/demo_output/topo_csv/csv/{cur_scene_name}_roads.csv"
    # attrcsv = f"./../data_preperation/demo_output/topo_csv/csv/{cur_scene_name}_attributes.csv"
    # outosm = f"./../data_preperation/demo_output/topo_csv/osm/{cur_scene_name}.osm"
    # outproj = f"./../data_preperation/demo_output/topo_csv/proj/{cur_scene_name}.txt"
    # csv2osm_main(roadcsv, attrcsv, outosm, outproj)
    # print(f'{cur_scene_name} csv converted to osm successfully!')

    ### 20240123
    # scene_name_list = [0,3,6,9,12,13, 16]
    # for item in scene_name_list:
    #     cur_scene_name = str(item)
    #     roadcsv = fr"./data/data_road_generation/pics_vis/visualization/select/out/csv/{cur_scene_name}_roads.csv"
    #     attrcsv = fr"./data/data_road_generation/pics_vis/visualization/select/out/csv/{cur_scene_name}_attributes.csv"
    #     outosm = fr"./data/data_road_generation/pics_vis/visualization/select/out/osm/{cur_scene_name}.osm"
    #     outproj = fr"./data/data_road_generation/pics_vis/visualization/select/out/proj/{cur_scene_name}.txt"
    #     csv2osm_main(roadcsv, attrcsv, outosm, outproj)
    #     print(f'{cur_scene_name} csv converted to osm successfully!')

    ### 20240723
    scene_name_list = range(0,7)
    for item in scene_name_list:
        cur_scene_name = str(item)
        roadcsv = fr"./data/topos/csv/{cur_scene_name}_roads.csv"
        attrcsv = fr"./data/topos/csv/{cur_scene_name}_attributes.csv"
        outosm = fr"./data/topos/osm/{cur_scene_name}.osm"
        outproj = fr"./data/topos/proj/{cur_scene_name}.txt"
        csv2osm_main(roadcsv, attrcsv, outosm, outproj)
        print(f'{cur_scene_name} csv converted to osm successfully!')
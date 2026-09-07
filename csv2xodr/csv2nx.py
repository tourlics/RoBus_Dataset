import networkx as nx 
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import pandas as pd

def read_csv(path,dtype):
    head_row = pd.read_csv(path, nrows=0) 
    head_row_list = list(head_row)
    csv_result = pd.read_csv(path,usecols=head_row_list,dtype=dtype)

    node_list = []
    for i in range(len(csv_result)):
        id = csv_result['id'].loc[i]
        lon = csv_result['lon'].loc[i]
        lat = csv_result['lat'].loc[i]
        group_id = csv_result['group_id'].loc[i] 
        node_content = (id, {'pos':(lon, lat), 'group':group_id})
        node_list.append(node_content)
    
    way_lists = []

    group_id_save = []
    way_list_ = {}
    for i in range(len(csv_result)):
        id = csv_result['id'].loc[i]
        group_id = csv_result['group_id'].loc[i]    
        if group_id in group_id_save:
            way_list_[group_id].append(id)
        else:
            group_id_save.append(group_id)
            way_list_[group_id] = [id]
    for id in way_list_:
        way_lists.append(way_list_[id])
    print(node_list, way_lists)
    return node_list, way_lists

def csv2networkx(node_list, way_lists):
    G = nx.Graph()
    G.add_nodes_from(node_list)
    con_list = []
    for edge_list in way_lists:
        for idx in range(len(edge_list)-1):
            con_list.append( (edge_list[idx], edge_list[idx+1]) )
    G.add_edges_from(con_list)
    # Visualize the original graph
    pos = nx.get_node_attributes(G, 'pos')
    plt.title("Topo Graph")
    nx.draw(G, pos, with_labels=False, node_size=6, width = 2, edge_color = 'green', node_color = 'red')
    plt.show()
    return G


if __name__ == "__main__":
    node_list, way_lists = read_csv("./demo/roads.csv",{'lon':np.float64,'lat':np.float64})
    G = csv2networkx(node_list, way_lists)
import os

filelist = os.listdir("./proj")
for file in filelist:
    cur_scene_name = file.split(".")[0]
    with open(os.path.join("./proj",file)) as ft:
        cur_proj = ft.readline()
    inputosm = os.path.join("./osm",f"{cur_scene_name}.osm")
    outputxodr = os.path.join("./xodr",f"{cur_scene_name}.xodr")
    exe_osm2xodr = f"python c_osm_to_xodr.py -i {inputosm} -o {outputxodr} --proj_string '{cur_proj}' "
    # print(exe_osm2xodr)
    # os.system(exe_osm2xodr)

    output_sumo_net = os.path.join("./sumo_net",f"{cur_scene_name}.net.xml")
    exe_xodr2sumonet = f"python ./Sumo/util/netconvert_carla.py {outputxodr} -o {output_sumo_net}"
    os.system(exe_xodr2sumonet)

    output_sumo_rou = os.path.join("./sumo_rou",f"{cur_scene_name}.rou.xml")
    exe_xodr2sumorou = f"python randomTrips.py -n {output_sumo_net} -r {output_sumo_rou}"
    os.system(exe_xodr2sumorou)
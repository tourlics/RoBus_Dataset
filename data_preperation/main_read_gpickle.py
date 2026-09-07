import os
from scripts.visualization import vis_dir_gpickle, vis_single_gpickle, vis_single_gpickle_posxy
root_dir = r"./dataset_roads/UnitedStates"

topo_dir = os.path.join(root_dir, "topo_simplify")

topo_vis_dir = os.path.join(root_dir, "topo_vis_png_simplify")

os.makedirs(topo_vis_dir, exist_ok=True)
vis_dir_gpickle(topo_dir, topo_vis_dir)

# gpickle_path = r"./data/sample.gpickle"
# vis_single_gpickle_posxy(gpickle_path)
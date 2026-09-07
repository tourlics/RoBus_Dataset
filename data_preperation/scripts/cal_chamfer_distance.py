import numpy as np
from sklearn.neighbors import NearestNeighbors
from PIL import Image
import os
from tqdm import tqdm
import random

def chamfer_distance(x, y, metric='l2', direction='bi'):
    """Chamfer distance between two point clouds

    Parameters
    ----------
    x: numpy array [n_points_x, n_dims]
        first point cloud
    y: numpy array [n_points_y, n_dims]
        second point cloud
    metric: string or callable, default ‘l2’
        metric to use for distance computation. Any metric from scikit-learn or scipy.spatial.distance can be used.
    direction: str
        direction of Chamfer distance.
            'y_to_x':  computes average minimal distance from every point in y to x
            'x_to_y':  computes average minimal distance from every point in x to y
            'bi': compute both
    Returns
    -------
    chamfer_dist: float
        computed bidirectional Chamfer distance:
            sum_{x_i \in x}{\min_{y_j \in y}{||x_i-y_j||**2}} + sum_{y_j \in y}{\min_{x_i \in x}{||x_i-y_j||**2}}
    """

    if direction=='y_to_x':
        x_nn = NearestNeighbors(n_neighbors=1, leaf_size=1, algorithm='kd_tree', metric=metric).fit(x)
        min_y_to_x = x_nn.kneighbors(y)[0]
        chamfer_dist = np.mean(min_y_to_x)
    elif direction=='x_to_y':
        y_nn = NearestNeighbors(n_neighbors=1, leaf_size=1, algorithm='kd_tree', metric=metric).fit(y)
        min_x_to_y = y_nn.kneighbors(x)[0]
        chamfer_dist = np.mean(min_x_to_y)
    elif direction=='bi':
        x_nn = NearestNeighbors(n_neighbors=1, leaf_size=1, algorithm='kd_tree', metric=metric).fit(x)
        min_y_to_x = x_nn.kneighbors(y)[0]
        y_nn = NearestNeighbors(n_neighbors=1, leaf_size=1, algorithm='kd_tree', metric=metric).fit(y)
        min_x_to_y = y_nn.kneighbors(x)[0]
        chamfer_dist = np.mean(min_y_to_x) + np.mean(min_x_to_y)
    else:
        raise ValueError("Invalid direction type. Supported types: \'y_x\', \'x_y\', \'bi\'")

    return chamfer_dist

def chamfer_dist_from_two_dir(image_dir1_path, image_dir2_path):
    image_dir1 = os.listdir(image_dir1_path)
    image_dir2 = os.listdir(image_dir2_path)
    cd_list = []
    for image1 in image_dir1:
        img1 = np.array(Image.open(os.path.join(image_dir1_path, image1)))
        p1 = np.argwhere(img1>0)
        cd_min = 99999999
        for image2 in tqdm(image_dir2):
            img2 = np.array(Image.open(os.path.join(image_dir2_path, image2)))
            p2 = np.argwhere(img2>0)
            dist = chamfer_distance(p1,p2)
            if dist < cd_min: cd_min = dist
        cd_list.append(dist)
    return cd_list

def chamfer_dist_from_two_dir_sampled(image_dir1_path, image_dir2_path):
    image_dir1_all = os.listdir(image_dir1_path)
    image_dir2_all = os.listdir(image_dir2_path)
    print(int(len(image_dir1_all)/5))
    image_dir1 = random.sample(image_dir1_all, int(len(image_dir1_all)/5)) # randomly sample 20% of images
    image_dir2 = random.sample(image_dir2_all, int(len(image_dir2_all)/20)) # randomly sample 5% of images
    cd_list = []
    for idx, image1 in enumerate(image_dir1):
        print(f"calculating the {idx}-th image...")
        img1 = np.array(Image.open(os.path.join(image_dir1_path, image1)))
        p1 = np.argwhere(img1>0)
        cd_min = 99999999
        for image2 in tqdm(image_dir2):
            img2 = np.array(Image.open(os.path.join(image_dir2_path, image2)))
            p2 = np.argwhere(img2>0)
            dist = chamfer_distance(p1,p2)
            if dist < cd_min: cd_min = dist
        cd_list.append(dist)
    return cd_list

if __name__ == "__main__":
    image_dir1_path = r"./data/data_road_generation/sample"
    image_dir2_path = r"./data/data_road_generation/image"
    cd_list = chamfer_dist_from_two_dir_sampled(image_dir1_path, image_dir2_path)
    print(cd_list)
    print(np.mean(cd_list))
    
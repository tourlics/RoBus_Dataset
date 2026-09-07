import numpy as np
from sklearn.neighbors import NearestNeighbors
from PIL import Image
import os
from tqdm import tqdm
import random
from scipy.stats import wasserstein_distance
import shutil
import cv2
import numpy as np

# FID, WD, and diversity

class RoadDiversity:
    def __init__(self) -> None:
        pass
    def chamfer_distance(self, x, y, metric='l2', direction='bi'):
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

    def chamfer_dist_from_two_dir(self, image_dir1_path, image_dir2_path):
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
                dist = self.chamfer_distance(p1,p2)
                if dist < cd_min: cd_min = dist
            cd_list.append(dist)
        return cd_list

    def chamfer_dist_from_two_dir_sampled(self, image_dir1_path, image_dir2_path):
        image_dir1_all = os.listdir(image_dir1_path)
        image_dir2_all = os.listdir(image_dir2_path)
        image_dir1 = random.sample(image_dir1_all, int(len(image_dir1_all)/20)) # Randomly sample 5% of the images
        image_dir2 = random.sample(image_dir2_all, int(len(image_dir2_all)/20)) # Randomly sample 5% of the images
        cd_list = []
        for idx, image1 in enumerate(image_dir1):
            print(f"calculating the {idx}-th image of total {len(image_dir1)} images...")
            img1 = np.array(Image.open(os.path.join(image_dir1_path, image1)))
            p1 = np.argwhere(img1>0)
            cd_min = 99999999
            for image2 in tqdm(image_dir2):
                img2 = np.array(Image.open(os.path.join(image_dir2_path, image2)))
                p2 = np.argwhere(img2>0)
                dist = self.chamfer_distance(p1,p2)
                if dist < cd_min: cd_min = dist
            cd_list.append(dist)
        return cd_list
    
    def chamfer_dist_from_two_dir_paired(self, image_dir1_path, image_dir2_path, num_samples=200):
        image_dir1_all = os.listdir(image_dir1_path)
        image_dir1 = random.sample(image_dir1_all, num_samples)
        cd_list = []
        for image1 in tqdm(image_dir1):
            scene_name = image1[:-11]
            img1 = np.array(Image.open(os.path.join(image_dir1_path, image1)))
            p1 = np.argwhere(img1>0)
            cd_min = 99999999
            image2 = f"{scene_name}_real_B.png"
            img2 = np.array(Image.open(os.path.join(image_dir2_path, image2)))
            p2 = np.argwhere(img2>0)
            dist = self.chamfer_distance(p1,p2)
            if dist < cd_min: cd_min = dist
            cd_list.append(dist)
        return cd_list

    def get_road_diversty_score(self, image_dir1_path, image_dir2_path, num_samples=200):
        # cd_list = self.chamfer_dist_from_two_dir_sampled(image_dir1_path, image_dir2_path)
        cd_list = self.chamfer_dist_from_two_dir_paired(image_dir1_path, image_dir2_path, num_samples)
        return np.mean(cd_list)

class BuldDiversity:
    def __init__(self) -> None:
        pass
    def calculate_overlap_ratio(self, image_path1, image_path2):
        image1 = cv2.imread(image_path1, cv2.IMREAD_UNCHANGED)
        image2 = cv2.imread(image_path2, cv2.IMREAD_UNCHANGED)
        
        # Ensure both images have the same size
        if image1.shape != image2.shape:
            raise ValueError("Images should have the same dimensions.")
        
        # Operate on binary images (assumed already binarized)
        # Overlap: pixels that are max-valued in both images
        overlap = np.logical_and(image1, image2)
        
        # Count non-zero pixels in image1
        image1_area = np.count_nonzero(image1)
        
        # Count overlap pixels
        overlap_count = np.count_nonzero(overlap)
        
        # Compute the overlap ratio
        overlap_ratio = overlap_count / image1_area if image1_area != 0 else 0
        
        return overlap_ratio
    def batch_cal_overlap_two_dir(self, image_dir1_path, image_dir2_path, num_samples=200):
        image_dir1_all = os.listdir(image_dir1_path)
        image_dir1 = random.sample(image_dir1_all, num_samples)
        ol_list = []
        for image in tqdm(image_dir1):
            img1 = os.path.join(image_dir1_path, image)
            img2 = os.path.join(image_dir2_path, image)
            ol = self.calculate_overlap_ratio(img1, img2)
            ol_list.append(ol)
        return np.mean(ol_list)


class FID:
    def __init__(self, dim=2048) -> None:
        self.dim = dim
        # 64: 0,  # First max pooling features
        # 192: 1,  # Second max pooling featurs
        # 768: 2,  # Pre-aux classifier features
        # 2048: 3,  # Final average pooling features
    def get_fid_score(self, imgdir1, imgdir2):
        cmd = f"python -m pytorch_fid {imgdir1} {imgdir2} --dim={self.dim}"
        res = os.popen(cmd)
        return res.read()

class WD:
    def __init__(self) -> None:
        pass
    def get_wd_score_from_list(self, list1, list2):
        wd_score = wasserstein_distance(list1, list2)
        return wd_score
    def get_wd_score_from_building_dirs(self, dir1, dir2):
        density_list1 = self.cal_building_density(dir1)
        density_list2 = self.cal_building_density(dir2)
        wd_socre = wasserstein_distance(density_list1, density_list2)
        return wd_socre
    def get_wd_score_from_road_topo_dirs(self, dir1, dir2):
        tfc1, ort1 = self.cal_road_topo(dir1)
        tfc2, ort2 = self.cal_road_topo(dir2)
        wd_score_tfc = wasserstein_distance(tfc1, tfc2)
        wd_score_ort = wasserstein_distance(ort1, ort2)
        return wd_score_tfc, wd_score_ort

    def cal_road_topo(self, topo_dir):
        from main_cal_tile_statics import GraphMetrics
        import networkx as nx
        tfc = []
        ort = []
        for topo_path in os.listdir(topo_dir):
            graph = nx.read_gpickle(topo_path)
            gmetric = GraphMetrics(graph)
            traffic_convenience = gmetric.traffic_convenience()
            orientation = gmetric.road_orientation()
            tfc.append(traffic_convenience)
            ort.append(orientation)
        return tfc, ort

    def cal_building_density(self, image_dir):
        images_path = os.listdir(image_dir)
        density_list = []
        for image_path in images_path:
            image = cv2.imread(os.path.join(image_dir, image_path), cv2.IMREAD_UNCHANGED)
            building_area = np.count_nonzero(image)
            image_area = image.shape[0] * image.shape[1]
            density_list.append(building_area/image_area * 100)
        return density_list

# Ratio of rectangles that violate the boundary constraint
class OutRatio:
    def __init__(self) -> None:
        pass
    def cal_bound_rect_list(self, boundary:Polygon, rect_list:list[Polygon]):
        intersection_area = 0
        invalid_rect = 0
        rect_area = 0
        for rect in rect_list:
            rect_area += rect.area
            if boundary.contains(rect): # contained
                pass
            elif boundary.intersects(rect): # intersecting
                invalid_rect += 1
                intersection = boundary.intersection(rect)
                intersection_area += intersection.area
            else: # outside
                invalid_rect += 1
                intersection_area += rect.area

        invalid_ratio = invalid_rect / len(rect_list)
        invalid_ratio_area = intersection_area / rect_area
        return invalid_ratio, invalid_ratio_area

class BuildExtractor:
    def __init__(self) -> None:
        pass
    def extract_building_maps(self, scenename, gt_dir, generate_dir, output_dir):
        image1 = cv2.imread(os.path.join(gt_dir, f"{scenename}_real_A.png"))
        if os.path.exists(os.path.join(generate_dir, f"{scenename}_real_B.png")):
            image2 = cv2.imread(os.path.join(generate_dir, f"{scenename}_real_B.png"))
        else:
            image2 = cv2.imread(os.path.join(generate_dir, f"{scenename}_fake_B.png"))
        
        # image1 = cv2.imread(os.path.join(gt_dir, f"{scenename}.png"))
        # image2 = cv2.imread(os.path.join(generate_dir, f"{scenename}.png"))
        # Ensure both images have the same size
        assert image1.shape == image2.shape, "Images do not have the same dimensions."

        # Convert images to grayscale
        gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

        # Compute the absolute difference of the two images
        difference = cv2.absdiff(gray1, gray2)

        # Threshold to obtain a binary image
        _, binary_image = cv2.threshold(difference, 50, 255, cv2.THRESH_BINARY)

        # Save the binary image
        cv2.imwrite(os.path.join(output_dir, f"{scenename}.png"), binary_image)
    def batch_extract_building_map(self, gt_dir, generate_dir, output_dir):
        files = os.listdir(gt_dir)
        # select_files = random.sample(files, num_samples)
        for file in tqdm(files):
            scenename = file[:-11]
            # print(scenename)
            self.extract_building_maps(scenename, gt_dir, generate_dir, output_dir)


class RoadExtractor:
    def __init__(self) -> None:
        pass

    def extract_road_maps(self, image_path, output_path):
        image = cv2.imread(image_path)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Yellow range in HSV
        yellow_lower = np.array([20, 100, 100], np.uint8)
        yellow_upper = np.array([30, 255, 255], np.uint8)

        # Gray range in HSV
        # Gray is typically low-saturation and high-value
        # Tune the range to the specific images if needed
        gray_lower = np.array([0, 0, 50], np.uint8)
        gray_upper = np.array([180, 50, 220], np.uint8)

        # Create masks from the defined thresholds
        yellow_mask = cv2.inRange(hsv, yellow_lower, yellow_upper)
        gray_mask = cv2.inRange(hsv, gray_lower, gray_upper)

        # Merge the yellow and gray masks
        combined_mask = cv2.bitwise_or(yellow_mask, gray_mask)

        # Apply the mask to get a binary image
        binary_image = cv2.bitwise_and(image, image, mask=combined_mask)

        # # Convert the binary image to grayscale if needed
        # binary_gray = cv2.cvtColor(binary_image, cv2.COLOR_BGR2GRAY)

        # Save the binary image
        cv2.imwrite(output_path, binary_image)
    
    def extract_roads_of_two_dirs(self, gt_dir, generate_dir, real_road_dir, gen_road_dir):
        for image in os.listdir(generate_dir):
            self.extract_road_maps(os.path.join(generate_dir, image), os.path.join(gen_road_dir, image))
        for image in os.listdir(gt_dir):
            self.extract_road_maps(os.path.join(gt_dir, image), os.path.join(real_road_dir, image))
    


def split_pix2pix_results(dataroot):
    
    original_dir = os.path.join(dataroot, "images")
    generate_dir = os.path.join(dataroot, "generate")
    os.makedirs(generate_dir, exist_ok=True)
    gt_dir = os.path.join(dataroot, "gt")
    os.makedirs(gt_dir, exist_ok= True)
    gtA_dir = os.path.join(dataroot, "gtA")
    os.makedirs(gtA_dir, exist_ok= True)

    files = os.listdir(original_dir)
    for file in files:
        if file[-10:] == "fake_B.png":
            shutil.copy(os.path.join(original_dir, file), os.path.join(generate_dir, file))
        elif file[-10:] == "real_B.png":
            shutil.copy(os.path.join(original_dir, file), os.path.join(gt_dir, file))
        elif file[-10:] == "real_A.png":
            shutil.copy(os.path.join(original_dir, file), os.path.join(gtA_dir, file))

if __name__ == "__main__":
    dataroot = "./CycleGAN-pix2pix/results/sbuilding_0411/test_latest"
    split_pix2pix_results(dataroot)

    generate_dir = os.path.join(dataroot, "generate")
    gt_dir = os.path.join(dataroot, "gt")
    gtA_dir = os.path.join(dataroot, "gtA")

    gen_road_dir = os.path.join(dataroot, "gen_roads")
    real_road_dir = os.path.join(dataroot, "real_roads")
    os.makedirs(gen_road_dir, exist_ok=True)
    os.makedirs(real_road_dir, exist_ok=True)
    # roadextract = RoadExtractor()
    # roadextract.extract_roads_of_two_dirs(gt_dir, generate_dir, real_road_dir, gen_road_dir)

    
    # fid = FID(dim=192) # dim=64, 192, 768, 2048
    # fid_score = fid.get_fid_score(generate_dir, gt_dir)
    # print(fid_score)

    # gen_road_dir = gen_road_dir
    # real_road_dir = gt_dir # for binary

    # divcal = RoadDiversity()
    # road_diversity = divcal.get_road_diversty_score(gen_road_dir, real_road_dir, num_samples=97)
    # print(road_diversity)

    # buildextract = BuildExtractor()
    gen_diff_build_dir = os.path.join(dataroot, "gen_diff_builds")
    gt_diff_build_dir = os.path.join(dataroot, "gt_diff_builds")
    # os.makedirs(gen_diff_build_dir, exist_ok=True)
    # os.makedirs(gt_diff_build_dir, exist_ok=True)
    # buildextract.batch_extract_building_map(gtA_dir, generate_dir, gen_diff_build_dir)
    # buildextract.batch_extract_building_map(gtA_dir, gt_dir, gt_diff_build_dir)

    # bdiv = BuldDiversity()
    # overlap = bdiv.batch_cal_overlap_two_dir(gen_diff_build_dir, gt_diff_build_dir, num_samples=200)
    # print(overlap)
    # gen_road_topo_dir = os.path.join(dataroot, "gen_road_topos")
    # os.makedirs(gen_road_topo_dir, exist_ok=True)
    # from main_gen_road_topo import raster2topo
    # raster2topo(gen_road_dir, gen_road_topo_dir)

    wdcal = WD()
    # wd = wdcal.get_wd_score_from_road_topo_dirs()
    wd = wdcal.get_wd_score_from_building_dirs(gen_diff_build_dir, gt_diff_build_dir)
    print(wd)

    

    
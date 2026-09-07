import imageio
import torch
import numpy as np
from skeleton_iccv import Skeletonize

if __name__ == "__main__":

    img = imageio.imread('./test2.png') / 255.
    img = torch.tensor(img, dtype=torch.float32).unsqueeze(0).unsqueeze(0)

    skeletonization_module = Skeletonize(probabilistic=True, beta=0.33, tau=1.0, simple_point_detection='Boolean')
    skeleton = skeletonization_module(img)

    skeleton = skeleton.numpy().squeeze() * 255
    skeleton[:,:,2] = skeleton[:,:,1]
    skeleton[:,:,1] = skeleton[:,:,0]
    print(skeleton.shape)
    imageio.imwrite('./test.png', skeleton.astype(np.uint8))
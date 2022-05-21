import os
import glob
import shutil
import argparse

import numpy as np
from PIL import Image


def ensure_dir(name):
    if not os.path.exists(name):
        os.makedirs(name)
    return name


def get_pil_image_weight(image):
    data = np.array(image)
    rows, cols = data.shape
    return data.sum() / cols


def get_weight(path):
    with Image.open(path) as image:
        return get_pil_image_weight(image)


def get_weights(names):
    result = []
    for name in names:
        w = get_weight(name)
        result.append(w)
        print(name, w)
    return result


def main():
    parser = argparse.ArgumentParser(
        description='Calculate weight of the images in a directory')
    parser.add_argument('--dir', help='path to the directory with images')
    parser.add_argument('--order', help='where to store reorder images')
    args = parser.parse_args()
    names = sorted(glob.glob(args.dir + '/*'))
    weights = get_weights(names)
    if args.order:
        order_dir = ensure_dir(args.order)
        both = zip(names, weights)
        both = reversed(sorted(both, key=lambda x: x[1]))
        for i, (name, weight) in enumerate(both):
            new_name = os.path.join(order_dir, '{:05d}.png'.format(i))
            print(name, new_name)
            shutil.copy(name, new_name)


if __name__ == '__main__':
    main()

import numpy as np
from skimage import io
from skimage.color import rgb2gray
from skimage.transform import rotate

from deskew import determine_skew

import subprocess

def rgba2rgb(rgba, background=(255,255,255)):
    row, col, ch = rgba.shape
    if ch == 3:
        return rgba
    assert ch == 4, 'RGBA image has 4 channels.'
    rgb = np.zeros((row, col, 3), dtype='float32')
    r, g, b, a = rgba[:,:,0], rgba[:,:,1], rgba[:,:,2], rgba[:,:,3]
    a = np.asarray(a, dtype='float32') / 255.0
    R, G, B = background
    rgb[:,:,0] = r * a + (1.0 - a) * R
    rgb[:,:,1] = g * a + (1.0 - a) * G
    rgb[:,:,2] = b * a + (1.0 - a) * B
    return np.asarray(rgb, dtype='uint8')

def deskew_copied(input, output: str, sigma=3.0, num_peaks=20) -> None:
    image = rgba2rgb(io.imread(input))
    grayscale = rgb2gray(image)
    angle = determine_skew(grayscale, sigma=sigma, num_peaks=num_peaks)
    background = 255 #[255, 255, 255]
    rotated = rotate(image, angle, resize=True, cval=-1) * 255
    pos = np.where(rotated == -255)
    rotated[pos[0], pos[1], :] = background
    rotated = rotate(image, angle, resize=True) * 255
    io.imsave(output, rotated.astype(np.uint8))

def deskew(input, output: str) -> None:
    deskew_copied(input, output)
    #subprocess.run(['deskew', '-o', output, input])

    # image = io.imread(input)
    # grayscale = rgb2gray(image)
    # angle = determine_skew(grayscale)
    # rotated = rotate(image, angle, resize=True) * 255
    # io.imsave(output, rotated.astype(np.uint8))


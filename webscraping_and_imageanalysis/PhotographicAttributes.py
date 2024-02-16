#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 29 16:52:42 2023

@author: hienhuynh
"""

#%% IMPORT LIBRARIES
from PIL import Image, ImageStat
from urllib import request
from io import BytesIO
import numpy as np
import cv2 as cv
from skimage import io, color, segmentation, graph, measure
from scipy import ndimage
import matplotlib.pyplot as plt


#%% DISPLAY IMAGE
def display_image(url):
    res = request.urlopen(url).read()
    img = Image.open(BytesIO(res))
    display(img)
    return img

#%% BRIGHTNESS
def brightness(url):
    """
    AVERAGE PIXEL BRIGHTNESS
    """
    # READ IMAGE FROM URL
    res = request.urlopen(url,timeout=5).read()
    img = Image.open(BytesIO(res))
    
    # CONVERT TO GRAYSCALE
    img_gr = img.convert('L')
    
    # IMAGESTAT
    stat = ImageStat.Stat(img_gr)
    
    # BRIGHTNESS
    brightness = stat.mean[0]
    return brightness


#%% CONTRAST
def contrast_range(url,mass=98):
    # READ IMAGE & CONVERT TO GRAYSCALE
    res = request.urlopen(url,timeout=10).read()
    img = Image.open(BytesIO(res))
    gray = img.convert('L')
    # CONSTRUCT HISTOGRAM FOR THE GRAYSCALE IMAGE
    hist = np.bincount(np.ravel(gray), minlength=256)
    # NORMALIZE THE HISTOGRAM, AS EACH IMAGE IS OF DIFFERENT SIZE
    sum_hist = np.sum(hist)
    phist = hist/sum_hist
    
    # DETERMINE CONTRAST, EQUALS TO THE WIDTH OF THE MIDDLE MASS%
    # OF THE HISTOGRAM
    total = 0
    for high_idx in range(len(phist)):
        if total < mass * 0.01:
            total += phist[high_idx]
        else:
            break

    total = 0
    for low_idx in range(len(phist)-1,-1,-1):
        if total < mass * 0.01:
            total += phist[low_idx]
        else:
            break
    
    # CONTRAST RANGE
    contrast = high_idx - low_idx + 1
    return contrast


#%% COLORFULNESS
def colorfulness(url):
    # READ IMAGE
    res = request.urlopen(url).read()
    img = io.imread(BytesIO(res))
    # IMAGE TO NUMPY ARRAY
    img = np.array(img)
    
    # RED, GREEN AND BLUE CHANNELS
    red_channel = img[:,:,0]
    green_channel = img[:,:,1]
    blue_channel = img[:,:,2]
    
    # HASLER AND SÜSSTRUNK'S COLORFULNESS METRIC
    # COMPUTE rg
    rg = np.abs(red_channel - green_channel)
    # COMPUTE yb
    yb = np.abs(0.5*(red_channel + green_channel) - blue_channel)
    
    # COMPUTE THE MEAN & STANDARD DEVIATION OF rg & yb
    rg_mean, yb_mean = np.mean(rg), np.mean(yb)
    rg_std, yb_std = np.std(rg), np.std(yb)
    
    # COMBINE
    mean_root  = np.sqrt((rg_mean**2) + (yb_mean**2))
    std_root = np.sqrt((rg_std**2) + (yb_std**2))
    
    # COLORFULNESS
    colorful = std_root + 0.3*mean_root
    return colorful


#%% COLOR VARIETY (HUE COUNT)
def color_variety(url):
    # READ IMAGE
    res = request.urlopen(url,timeout=10).read()
    img = io.imread(BytesIO(res))
    
    # CONVERT RGB TO HVS
    hsv = color.rgb2hsv(img)
    
    # HSV SHAPE
    h,w,c = hsv.shape
    
    # HSV RESHAPE 3D TO 2D
    hsv_long = hsv.reshape((h*w,c))
    
    # FILTER PIXELS
    # ONLY KEEP PIXELS WITH SATURATION >= 0.2 AND 0.15 <= V <= 0.95
    hsv_filtered = hsv_long[(hsv_long[:,1]>=0.2)&(hsv_long[:,2]>=0.15)&(hsv_long[:,2]<=0.95)]
    
    # ARRAY OF HUE
    hue_long = hsv_filtered[:,0]
    
    # BINS
    bins = np.linspace(0, np.amax(hue_long), num=20, endpoint=False)
    
    # NUMPY DIGITIZE
    digitized = np.digitize(hue_long, bins)
    # MINUS 1 BECAUSE INDICES OF DIGITIZED STARTS FROM 1 (NOT 0)
    digitized = digitized - 1
    # COUNT HUE VALUES IN EACH BIN
    count_per_bin = []
    for i in range(len(bins)):
        num_hues = len(digitized[digitized == i])
        count_per_bin.append(num_hues)
    
    # PERCENTAGES
    percentages = []
    for i in range(len(count_per_bin)):
        percentage = count_per_bin[i]/sum(count_per_bin)
        percentages.append(percentage)
    percentages = np.array(percentages)
    
    # COMPARE WITH MAXIUM OF HISTOGRAM * ALPHA, ALPHA = 0.05
    hist_max = max(percentages)
    alpha = 0.05
    # HUE COUNT
    hue_count = np.where(percentages>alpha*hist_max)[-1].shape[-1]
    return hue_count


#%% VISUAL COMPLEXITY

# IMAGE SEGMENTATION
def image_segmentation(url, n_segments=400, compactness=1, sigma=100):
    # READ IMAGE
    res = request.urlopen(url,timeout=15).read()
    img = io.imread(BytesIO(res))
    
    # SLIC SEGMENTATION (USING K-MEAN CLUSTERING)
    label_km = segmentation.slic(img, n_segments=n_segments, compactness=compactness,sigma=sigma)
    
    # REGION ADJACENCY GRAPH
    g = graph.rag_mean_color(img, label_km, mode='similarity', sigma=sigma)
    
    # NORMALIZED CUT
    label = graph.cut_normalized(label_km, g)
    
    return label

# VISUAL COMPLEXITY
def visual_complexity(url):
    label = image_segmentation(url)
    labeled_array, label_num = measure.label(label, background=99999, return_num=True)
    return label_num


#%% VISUAL BALANCE
def saliency_spectral_residual(url):
    # READ IMAGE AND CONVERT TO GRAYSCALE
    res = request.urlopen(url,timeout=15).read()
    img = Image.open(BytesIO(res))
    gray = img.convert('L')
    gray = np.array(gray)
    
    # CV2 SALIENCY
    saliency = cv.saliency.StaticSaliencySpectralResidual_create()
    success, saliency_map = saliency.computeSaliency(gray)
    saliency_map = (saliency_map * 255).astype("uint8")
    return saliency_map
    
    
def center_of_mass(url):
    saliency_map = saliency_spectral_residual(url)
    
    # IMAGE SHAPE
    h,w = saliency_map.shape
    
    # CENTER OF MASS COORDINATE
    com_x, com_y = ndimage.center_of_mass(saliency_map)
    # SCALE CENTER OF MASS
    com_x = com_x/h 
    com_y = com_y/w
    return com_x, com_y



def rule_of_thirds(url):
    com_x, com_y = center_of_mass(url)
    
    # DISTANCES TO THE 1/3 & 2/3 VERTICAL LINES
    dist1 = abs(com_x - 1/3)
    dist2 = abs(com_x - 2/3)

    # DISTANCES TO THE 1/3 & 2/3 HORIZONTAL LINES
    dist3 = abs(com_y - 1/3)
    dist4 = abs(com_y - 2/3) 
    dist_l = min(dist1, dist2, dist3, dist4)

    # DISTANCES TO THE INTERSECTIONS OF THE THIRD LINES
    dist5 = (dist1**2 + dist3**2) ** 0.5
    dist6 = (dist1**2 + dist4**2) ** 0.5  
    dist7 = (dist2**2 + dist3**2) ** 0.5  
    dist8 = (dist2**2 + dist4**2) ** 0.5  
    dist_i = min(dist5, dist6, dist7, dist8)
    
    # RULE OF THIRDS
    rot = dist_l * dist_i
    
    return rot

def visual_balance(url):
    """
    VISUAL BALANCE IS DETERMINED BY THE DEVIATION OF THE CENTER OF MASS
    (DCM)
    """
    # COMPUTE CENTER OF MASS
    com_x, com_y = center_of_mass(url)
    dcm_x = abs(com_x - 1/2)
    dcm_y = abs(com_y - 1/2)
    
    # COMPUTE DEVIATION OF THE CENTER OF MASS
    dcm = (dcm_x**2 + dcm_y**2)
    dcm = np.sqrt(dcm)
    dcm = dcm/0.5
    dcm = dcm*100
    return dcm

#%% SHARPNESS
def sharp(url, magnitude_threshold=5):
    # READ IMAGE AND CONVERT TO GRAYSCALE
    res = request.urlopen(url).read()
    img = io.imread(BytesIO(res))
    gray = color.rgb2gray(img)
    # IMAGE SHAPE
    h, w = gray.shape
    
    # FOURIER TRANSFORM
    F = np.fft.fft2(gray)
    # SHIFT
    F_shift = np.fft.fftshift(F)
    # MAGNITUDE
    S = abs(F_shift)
    
    # COUNT FREQUENCIES ()
    count_S = np.count_nonzero(S > magnitude_threshold)
    
    #
    blur = count_S / (h*w)
    return blur

def sharp_method(gray, magnitude_threshold=5):
    """
    TAKE A GRAYSCALE IMAGE (INSTEAD OF A URL)
    """
    # IMAGE SHAPE
    h, w = gray.shape
    
    # FOURIER TRANSFORM
    F = np.fft.fft2(gray)
    # SHIFT
    F_shift = np.fft.fftshift(F)
    # MAGNITUDE
    S = abs(F_shift)
    
    # COUNT FREQUENCIES
    count_S = np.count_nonzero(S > magnitude_threshold)
    
    # SHARPNESS
    blur = count_S / (h*w)
    return blur

def depth_of_field(url):
    # READ IMAGE AND CONVERT TO GRAYSCALE
    res = request.urlopen(url).read()
    img = io.imread(BytesIO(res))
    gray = color.rgb2gray(img)
    
    # DIVIDE IMAGE INTO 4 BLOCKS
    # ALONG THE AXIS 0
    gray_spl_1d = np.array_split(gray, 4, axis=0)
    gray_spl_2d = [np.array_split(i, 4, axis=1) for i in gray_spl_1d]
    windows = [j for sublist in gray_spl_2d for j in sublist]
    
    # SHARP PER BLOCK
    sharps = [sharp_method(k) for k in windows]
    sharps = np.array(sharps)
    
    # INNER BLOCKS' INDICES
    indices = np.array([5,6,9,10])
    inner_blocks = sharps[indices]

    dof = np.mean(inner_blocks)/np.mean(sharps)
    return dof

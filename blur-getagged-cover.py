# -*- coding: utf-8 -*-
"""
Created on Sat Aug 26 12:33:18 2023

@author: atanu
"""


import geopandas as gpd
import os 
from exif import Image
import glob
import pyproj
from shapely.geometry import Point
from shapely.ops import transform as sh_transform
from functools import partial
import fiona 
from exif import Image as ExifImage 


import cv2
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
#-----------------------------------------------------------------------

wgs84_globe = pyproj.Proj(proj='latlong', ellps='WGS84')

def pol_buff_on_globe(pol, radius):
    _lon, _lat = pol.centroid.coords[0]
    aeqd = pyproj.Proj(proj='aeqd', ellps='WGS84', datum='WGS84',
                       lat_0=_lat, lon_0=_lon)
    project_pol = sh_transform(partial(pyproj.transform, wgs84_globe, aeqd), pol)
    return sh_transform( partial(pyproj.transform, aeqd, wgs84_globe),
                          project_pol.buffer(radius))


def decimal_coords(coords, ref):   
    decimal_degrees = coords[0] + coords[1] / 60 + coords[2] / 3600
    if ref == 'S' or ref == 'W':        
        decimal_degrees = -decimal_degrees        
    return decimal_degrees


def image_coordinates(image_all):    
    with open(image_all, 'rb') as src:        
        img_t = ExifImage(src)        
    if img_t.has_exif:        
        try:
            img_t.gps_longitude
            coords = (decimal_coords(img_t.gps_longitude,img_t.gps_longitude_ref),decimal_coords(img_t.gps_latitude,img_t.gps_latitude_ref))
        except AttributeError:            
            print ('No Coordinates')
    else:        
        print ('The Image has no EXIF information')        
    return(coords)
    

def cover_image(main_folder):
    for path, subdirs, files in os.walk(main_folder):
        image_list = glob.glob(f'{path}/*.JPG')
        for image_all in image_list:   
            cords = image_coordinates(image_all)    
            point = Point(cords) 
            if point.within(buffer):
                return True
        return False
                    
               

    
#----------------------- kml to coords -------------------------------#


kml_path = 'E:/GIS Devolop(AT)/Drogo-Drones/Data/Boundary.shp.kml'
fiona.drvsupport.supported_drivers['KML'] = 'rw'
my_map = gpd.read_file(kml_path, driver='KML')
file_basename = os.path.basename(kml_path).split('.')[0]

    
for ind in my_map.index:
    my_poly = my_map.geometry[0]
    pol = my_poly
    radius = 100
    buffer = pol_buff_on_globe(pol, radius)


#-------------------------Blur Image Information------------------------------------------------

def blur(image_path, threshold):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    if img is None:
        print("Image not found ")
    
    laplacian_method = cv2.Laplacian(img, cv2.CV_64F).var()
    
    if laplacian_method < threshold:
        return True
    else:
        return False

def image_Main_folder(folder_path, threshold):
    total_count = 0
    blur_count = 0
    blur_images = []

    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg')):
                image_path = os.path.join(root, file)
                total_count += 1
                if blur(image_path, threshold):
                    blur_count += 1
                    blur_images.append(image_path)
    
    return total_count, blur_count, blur_images


#----------------------------------Geotagged Image Information--------------------------

def get_geotagging(exif):
    if not exif:
        print("No EXIF metadata found")

    geotagging = {}
    for (idx, tag) in TAGS.items():
        if tag == 'GPSInfo':
            if idx not in exif:
                print ("No EXIF geotagging found")
            for (key, val) in GPSTAGS.items():
                if key in exif[idx]:
                    geotagging[val] = exif[idx][key]

    return geotagging

def is_geotagged(image_path):
    image = Image.open(image_path)
    exif = image._getexif()
    
    if exif is None:
        return False
    
    geotagging = get_geotagging(exif)
    
    return bool(geotagging)

def count_ungeotagged_images(main_folder):
    ungeotagged_count = 0
    total_uncount =0
    ungeotagged_image = []

    for root, _, files in os.walk(main_folder):
        for file in files:
            if file.lower().endswith(('.png','.jpg', '.jpeg')):
                image_path = os.path.join(root, file)
                total_uncount += 1
                if not is_geotagged(image_path):
                    ungeotagged_count += 1
                    ungeotagged_image.append(image_path)
    
    return  total_uncount, ungeotagged_count, ungeotagged_image


#-----------------------------------------------------------------------------

main_folder = "E:/GIS Devolop(AT)/Drogo-Drones/Data/25-5-2022/25-5-2022/101MEDIA/BlurImage/OneDrive_1_06-09-2023"
thresold_value=5

cov=cover_image(main_folder)
total_uncount,ungeotagged_count , ungeotagged_image = count_ungeotagged_images(main_folder)
total_count, blur_count, blur_images = image_Main_folder(main_folder, thresold_value )

#--------------------------------------------------------------------------------------------

print("\n----------Image Boundary cover Information--------------\n")   


if cov:
    print('Image cover the boundary')
else:
    print('image not cover')         
        
print("\n-------------------------------------------\n")

#----------------------------------------------------------------------------------------

print('\n-----Blur Image Detection---\n')
print(f"Total images: {total_count}")
print(f"Total blurry images: {blur_count}")
print(f"Percentage of blurry images: {blur_count / total_count * 100:.2f}%")

if blur_images:
    print("Blur images information :")
    for image_path in blur_images:
        print(image_path)
else:
    print('Congratulations!!!  All Photos Quality Good')
print('\n-----Geotagged Image Information---\n')
print("Tolat Image count = ",total_count )
print("Total ungeotagged images:",ungeotagged_count)
if ungeotagged_image:
    print("Ungeotaagged Image Information :")
    for image_path in ungeotagged_image:
        print(image_path)
else:
    print("Congratulations!!!  All Photos are Geotagged")

#-------------------------------------------------------

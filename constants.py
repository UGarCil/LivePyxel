# import pygame 
import os 
import cv2 
import argparse
from os.path import join as jn
from collections import namedtuple

import random
import json 

import sys
import cv2
import numpy as np
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton,QColorDialog
import uuid
########################### ARGPARSE arguments ###################################
parser = argparse.ArgumentParser(description='Line measurement tool')
parser.add_argument("--ci", default=0,type=int,help='Index of the camera (for multiple camera devices connected)')
parser.add_argument("--res", default=0.8,type=float,help="Determine the resolution of the camera from 0.1 to 1.0")
args = parser.parse_args()

##################################################################################
# pygame.init()
# display_info = pygame.display.Info()
# define the dimensions of the screen
# W = int(display_info.current_w*args.res)
# H = int(W*cameraRatio)
# W = 1920
# H = 1080



# Determine the width and height ratio of the camera
cap = cv2.VideoCapture(args.ci)
cameraW = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
cameraH = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
cameraRatio = cameraH/cameraW #what proportion of the width is the height (e.g. for 1920 x 1080, it's 0.56)


# Make the dimensions of the window 80% of the user's screen
# W = int(display_info.current_w*args.res)
# H = int(W*cameraRatio)
W = 1920
H = 1080
# print(cameraW, cameraH)
# print(W,H)
# SCREEN = (W,H)
# display = pygame.display.set_mode(SCREEN)
# Initialize webcam


# DD LATERAL_PADDING_MENU
# LATERAL_PADDING = (int,int)
# interp. how many pixels to leave as padding to accomodate the lateral panel of the application
# Define the named tuple with fields 'x' and 'y'
Coordinate = namedtuple('Coordinate', ['x', 'y'])
LATERAL_PADDING = Coordinate(400,0)
TOP_PADDING = Coordinate(0,80)

# DD. SAVEPATH 
# savePath = str
# interp. the location of the file that will store the program's output
savePath = jn(os.path.dirname(__file__),"output.txt")

# DD. BRUSH_SETTINGS
# brush_settings = {"color":(int, int, int)}
# interp. a set of parameters represented as a mutable object to be used globally within different submodules of the program
brush_settings = {"color":(0, 255, 0), "size":20,"resize_sensitivity":5, "is_brush_mode":True}

# DD. DISPLAY_SETTINGS
# display_settings = {"image":np.array, "mask":np.array}
# interp. a set of numpy arrays representing images and masks for the program
display_settings = {"image":None, "mask":None}

cursor_settings = {"in_display":False}

os_settings = {"directory":"", "config":"", "masks_path":"","images_path":""}
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
from PyQt5.QtGui import QImage, QPixmap, QKeySequence
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton,QColorDialog,QMessageBox,QShortcut
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


# Define the dimensions of the screen
W = 1920
H = 1080


# DD LATERAL_PADDING_MENU
# LATERAL_PADDING = (int,int)
# interp. how many pixels to leave as padding to accomodate the lateral panel of the application
# Define the named tuple with fields 'x' and 'y'
Coordinate = namedtuple('Coordinate', ['x', 'y'])
LATERAL_PADDING = Coordinate(400,0)
TOP_PADDING = Coordinate(0,80)


# DD. BRUSH_MAX_MEMORY
# brush_max_memory = int
# interp. the maximum number of brush strokes that can be stored in memory
BRUSH_MAX_MEM = 3

# DD. SAVEPATH 
# savePath = str
# interp. the location of the file that will store the program's output
savePath = jn(os.path.dirname(__file__),"output.txt")

# DD. BRUSH_SETTINGS
# brush_settings = {"color":(int, int, int)}
# interp. a set of parameters represented as a mutable object to be used globally within different submodules of the program
brush_settings = {"color":(0, 255, 0), "size":20,"resize_sensitivity":5, "is_brush_mode":"brush", "brush_strokes_in_memory_counter":0,"opacity":0,"color_before_substracting_mode":None,"thickness":1}

# DD. DISPLAY_SETTINGS
# display_settings = {"image":np.array, "mask":np.array, "statusBar":QtWidgets.QStatusBar}
# interp. a set of numpy arrays representing images and masks for the program
display_settings = {"image":None, "mask":None,"list_of_mask":None, "statusBar":None}

cursor_settings = {"in_display":False}

# substractive mode turns the brush or tool into an eraser
os_settings = {"directory":"", "config":"", "masks_path":"","images_path":"","substractive_mode":False, "top_layer_edit":False, "webcam_mode":True}



# FD. merge_masks()
# purp. merge multiple image arrays where higher index images take precedence over lower index ones,
# but only if their pixel values are non-zero.
def merge_masks(list_of_masks):
        """
        Created by Claude Sonnet v.3.2 on March 6th, 2025
        Merge multiple image arrays where higher index images take precedence over lower index ones,
        but only if their pixel values are non-zero.
        
        Assumes:
        - All images in display_settings["list_of_mask"] are the same size
        - At least one image is always provided
        - The image list is stored in display_settings["list_of_mask"]
        
        Returns:
        rendered_mask: NumPy array containing the merged result
        """
        # Initialize the rendered mask with the first image
        rendered_mask = np.copy(display_settings["list_of_mask"][0])
        
       
        # Merge the images according to the specified rules
        for img in display_settings["list_of_mask"][1:]:
            # Create a mask of non-zero pixels in the current image
            non_zero_mask = np.any(img != 0, axis=-1)
            
            # Update the rendered mask with non-zero pixels from the current image
            rendered_mask[non_zero_mask] = img[non_zero_mask]
        
        return rendered_mask


# def show_status_message(message, is_success=False, is_error=False, timeout=5000):
#     """Displays a styled status message with optional icon on the status bar."""
#     statusBar = display_settings["statusBar"]
#     statusBar().showMessage(message, timeout)  # Shows for 5 seconds
                
#     # Optional: Flash the status bar for better visibility
#     palette = statusBar().palette()
#     original_color = palette.color(palette.Window)
#     palette.setColor(palette.Window, QtGui.QColor(0, 150, 0))  # Green background
#     statusBar().setPalette(palette)
    
    

def show_status_message(message, is_success=False, is_error=False, timeout=5000):
    """Displays a styled status message with optional icon on the status bar."""
    status_bar = display_settings["statusBar"]
    
    # Clear existing message
    status_bar().clearMessage()

    # Compose text with icon
    if is_success:
        icon_path = "icons/success_icon.png"
    elif is_error:
        icon_path = "icons/fail_icon.png"
    else:
        icon_path = None

    if icon_path and os.path.exists(icon_path):
        pixmap = QtGui.QPixmap(icon_path).scaled(16, 16, QtCore.Qt.KeepAspectRatio)
        icon = QtWidgets.QLabel()
        icon.setPixmap(pixmap)
        message_label = QtWidgets.QLabel(message)
        
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.addWidget(icon)
        layout.addWidget(message_label)
        status_bar().addPermanentWidget(container)

        # Remove widget after timeout
        QtCore.QTimer.singleShot(timeout, lambda: (
            status_bar().removeWidget(container),
            container.deleteLater()
        ))
    else:
        # Just show plain message
        status_bar().showMessage(message, timeout)

    # Change background color
    palette = status_bar().palette()
    if is_success:
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(220, 255, 220))  # light green
    elif is_error:
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(255, 220, 220))  # light red
    else:
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(240, 240, 240))  # neutral
    status_bar().setAutoFillBackground(True)
    status_bar().setPalette(palette)

    # Reset color after timeout
    QtCore.QTimer.singleShot(timeout, lambda: (
        status_bar().setPalette(QtWidgets.QApplication.palette()),
        status_bar().setAutoFillBackground(False)
    ))
    
def add_empty_mask():
    display_settings["list_of_mask"].append(np.zeros_like(display_settings["list_of_mask"][-1]))
    return display_settings["list_of_mask"][-1]
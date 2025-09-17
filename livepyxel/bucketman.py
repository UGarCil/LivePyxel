import numpy as np
from .constants import *

# DD. POINT
# pt = Coordinate(int,int)
# interp. a point in the scaled view of a webcam feed, scaled to fit the imageDisplay Widget of the main program
pt = Coordinate(0,0)

# DD. BUCKET_MANAGER
# bucketman = Bucketman()
# interp. a set of attributes used to define the behavior of the bucket tool
class Bucketman():
    def __init__(self, parent=None):
        # Store a reference to the parent ImageAnnotator
        self.parent = parent
    
    def onMouseEventDown(self, coor):
        """
        Implements a bucket/fill tool that changes the color of an entire annotation.
        
        Parameters:
        coor (QPoint): The coordinates where the user clicked
        """
        # Convert QPoint to a tuple of (x, y)
        x, y = coor.x, coor.y
        
        # Find which mask contains the annotation at the clicked point
        target_mask_index = None
        
        for idx, mask in enumerate(display_settings["list_of_mask"]):
            # Check if there's color at the clicked position in this mask
            if np.any(mask[y, x] != 0):
                target_mask_index = idx
                break
        
        # If no colored pixel was found at the clicked position, return
        if target_mask_index is None:
            return
        
        # Get the mask that contains the clicked annotation
        target_mask = display_settings["list_of_mask"][target_mask_index]
        
        # Create a binary mask where any non-zero pixel will be changed
        # This identifies all pixels that are part of the annotation
        binary_mask = np.any(target_mask != 0, axis=2)
        
        # Apply the new color to all non-zero pixels in the mask
        # If using subtractive mode, set to black (erase)
        if os_settings["substractive_mode"]:
            # In subtractive mode, we set the color to black (effectively removing it)
            target_mask[binary_mask] = (0, 0, 0, 0)
        else:
            # In normal mode, we set the color to the currently selected color
            # r, g, b = brush_settings["color"]
            target_mask[binary_mask] = brush_settings["color"]
        
        # Update the mask in the list
        display_settings["list_of_mask"][target_mask_index] = target_mask
        
        # # Update the display to show the changes
        # if self.parent:
        #     self.parent.update_image_display()
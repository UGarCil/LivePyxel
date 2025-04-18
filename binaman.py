from constants import *
import numpy as np

# DD. POINT
# pt = Coordinate(int,int)
# interp. a point in the scaled view of a webcam feed, scaled to fit the imageDisplay Widget of the main program
pt = Coordinate(0,0)

# DD. BINARY_MASK_MANAGER
# binman = Binman()
# interp. a set of components that define the behavior of the binary mask tool
class Binman():
    def __init__(self, parent=None):
        # Store a reference to the parent ImageAnnotator
        self.parent = parent
        self.threshold = 120 # default threshold value
        self.binary_mask = None

    def onMouseEventDown(self):
        """
        Implements a binary mask tool that creates a new mask based on the annotation upon click event
        """
        
        
        # Create a copy of the current image 
        thres_target = display_settings["image"].copy()
        
        # Convert image to grayscale
        thres = cv2.cvtColor(thres_target, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold to create binary mask
        _, self.binary_mask = cv2.threshold(thres, self.threshold, 255, cv2.THRESH_BINARY)
        # If subtractive mode is enabled, invert the mask
        if os_settings["substractive_mode"]:
            self.binary_mask = cv2.bitwise_not(self.binary_mask)

        # Convert single-channel mask to 3-channel
        self.binary_mask = cv2.merge([self.binary_mask] * 4)  # Expands grayscale mask to (H, W, 3)
        
    # # Original working version v1
    # def finish_binary_mask(self):
    #     if self.binary_mask is None:
    #         return

    #     display_settings["list_of_mask"].append(np.zeros_like(display_settings["list_of_mask"][-1]))

    #     # Convert the RGB part to grayscale to detect the drawn region
    #     binary_mask_gray = cv2.cvtColor(self.binary_mask[:, :, :3], cv2.COLOR_RGB2GRAY)
    #     _, thresh = cv2.threshold(binary_mask_gray, 1, 255, cv2.THRESH_BINARY)

    #     # Find contours from the mask
    #     contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    #     # Fill the new mask directly
    #     cv2.fillPoly(display_settings["list_of_mask"][-1], contours, color=brush_settings["color"])

    
    # Working version with enhanced gap visibility
    def finish_binary_mask(self):
        if self.binary_mask is None:
            return
        _new_mask = add_empty_mask()
        gray_mask = cv2.cvtColor(self.binary_mask[:, :, :3], cv2.COLOR_RGB2GRAY)
        _, binary_mask = cv2.threshold(gray_mask, 1, 255, cv2.THRESH_BINARY)

        # Apply opening instead of closing to emphasize gaps
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))  # try (5,5) if needed
        opened_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel)

        contours, hierarchy = cv2.findContours(opened_mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

        cv2.fillPoly(_new_mask, contours, color=brush_settings["color"])
        # display_settings["list_of_mask"].append(new_mask)
        self.binary_mask = None

    


    def display(self, image):
        if self.binary_mask is not None:
            return self.binary_mask
        return image
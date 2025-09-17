import numpy as np
from .constants import *
# DD. POINT
# pt = Coordinate(int,int)
# interp. a point in the scaled view of a webcam feed, scaled to fit the imageDisplay Widget of the main program
pt = Coordinate(0,0)

# DD. POLYGON
# polygon = {"DONE":False, "POINTS":[POINT, ...]}
# interp. a collection of POINTs to trace a polygon. Coordinates are given relative to the scaled 
# area of the mask represented in the imageDisplay Widget of the main program
polygon = {"DONE":False, "POINTS":[pt],"COLOR":None}


# DD. POLYGON_MANAGER
# polyman = PolyMan()
# interp. a set of attributes used to define the polygons that will be created on top of the mask
class Polyman():
    def __init__(self):
        # self.firstClick = True #to start a new polyong
        self.current_polygon = {"DONE":False, "POINTS":[], "COLOR":None}
        # self.lopolygon = [self.current_polygon]
        
    def updatePoly(self, coor):
        coor_x, coor_y = coor
        self.current_polygon["POINTS"].append(Coordinate(coor_x,coor_y))
        
    def finishPolygon(self):
        if not brush_settings["is_brush_mode"] == "polygon":
            return
            
        points = np.array([[p.x, p.y] for p in self.current_polygon["POINTS"]], np.int32)
        points = points.reshape((-1, 1, 2))
        
        # evaluate if there are any points to annotate
        if len(points) == 0:
            return 
        
        if os_settings["substractive_mode"]:
            _boolean_mask = np.zeros_like(display_settings["list_of_mask"][-1])
            cv2.fillPoly(_boolean_mask, [points], color=(255,255,255))
            inverted_mask = cv2.bitwise_not(_boolean_mask)
            
            if os_settings["top_layer_edit"]:
                display_settings["list_of_mask"][-1] = cv2.bitwise_and(display_settings["list_of_mask"][-1], inverted_mask)
            else:
                for idx, mask in enumerate(display_settings["list_of_mask"]):
                    display_settings["list_of_mask"][idx] = cv2.bitwise_and(mask, inverted_mask)
        else:
            # Create a temporary mask to draw the polygon
            temp_mask = np.zeros_like(display_settings["list_of_mask"][-1])
            cv2.fillPoly(temp_mask, [points], color=(255, 255, 255, 255))  # Fill with white
            
            # Create a binary mask of where the polygon was drawn (ignoring alpha channel)
            binary_mask = np.any(temp_mask[:, :, :3] > 0, axis=2)
            
            # Create a new mask with the desired color
            _mask = add_empty_mask()
            _mask[binary_mask] = brush_settings["color"]
            
            # Append the new mask
            # display_settings["list_of_mask"].append(new_mask)
        
        # Reset the current polygon
        self.current_polygon = {"DONE": False, "POINTS": [], "COLOR": None}


    def pop_last_point(self):
        if len(self.current_polygon["POINTS"])>0:
            self.current_polygon["POINTS"].pop(-1)
from constants import *
import numpy as np
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
        # if in polygon mode
        #   set the polygon as complete to draw it as a filled area
        #   add the polygon to the list
        #   create a new empty polygon
        # Make a new mask 
        points = [(pt.x, pt.y) for pt in self.current_polygon["POINTS"]]
        points = np.array([[p.x, p.y] for p in self.current_polygon["POINTS"]], np.int32)
        points = points.reshape((-1, 1, 2))
        if brush_settings["is_brush_mode"] == "polygon":
            if os_settings["substractive_mode"]:
                # create a new mask from the selected polygon
                _boolean_mask = np.zeros_like(display_settings["list_of_mask"][-1])
                # fill it with the color (255,255,255) to erase the pixels at a later stage
                cv2.fillPoly(_boolean_mask, [points], color=(255,255,255))
                # invert the boolean mask so we keep everything EXCEPT the polygon
                inverted_mask = cv2.bitwise_not(_boolean_mask)
                if os_settings["top_layer_edit"]:
                    # modify the mask on top layer only
                    display_settings["list_of_mask"][-1] = cv2.bitwise_and(display_settings["list_of_mask"][-1], inverted_mask)
                else:
                    # iterate over all masks erasing the pixels delimited by this mask
                    for idx, mask in enumerate(display_settings["list_of_mask"]):
                        display_settings["list_of_mask"][idx] = cv2.bitwise_and(mask, inverted_mask)
            else:
                _mask = add_empty_mask()
                # fill the color with the brush color selected by the user and save it, then create a new mask
                # _mask_copy = _mask.copy() !!!!!!!!!!!!!!!!!
                cv2.fillPoly(_mask, [points], color=brush_settings["color"])
            # display_settings["list_of_mask"].append(np.zeros_like(display_settings["list_of_mask"][-1]))
            self.current_polygon = {"DONE":False, "POINTS":[], "COLOR":None}
            # self.lopolygon.append(self.current_polygon)


    def pop_last_point(self):
        if len(self.current_polygon["POINTS"])>0:
            self.current_polygon["POINTS"].pop(-1)
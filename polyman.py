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
        if brush_settings["is_brush_mode"] == "polygon":
            # self.current_polygon["DONE"] = True
            self.current_polygon["COLOR"] = brush_settings["color"]
            points = [(pt.x, pt.y) for pt in self.current_polygon["POINTS"]]
            points = np.array([[p.x, p.y] for p in self.current_polygon["POINTS"]], np.int32)
            points = points.reshape((-1, 1, 2))
            cv2.fillPoly(display_settings["mask"], [points], color=brush_settings["color"])
            # if self.current_polygon not in self.lopolygon:
            #     self.lopolygon.append(self.current_polygon)
            self.current_polygon = {"DONE":False, "POINTS":[], "COLOR":None}
            # self.lopolygon.append(self.current_polygon)


    def pop_last_point(self):
        if len(self.current_polygon["POINTS"])>0:
            self.current_polygon["POINTS"].pop(-1)
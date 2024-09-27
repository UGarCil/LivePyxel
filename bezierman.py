import math
from constants import *
import numpy as np

SUBDIVS = 100 #total number of divisions in a bezier curve
SEGMENT_DISTANCE = 1/SUBDIVS #how long is a segment relative to a unit

# DD. POINT
# pt = Coordinate(int,int)
# interp. a point in the scaled view of a webcam feed, scaled to fit the imageDisplay Widget of the main program
pt = Coordinate(0,0)

# DD. BEZIER
# bezier = Bu()
# interp. an object representing a Bezier unit that contains:
# - point 1
# - point 2 (anchor)
# - point 3

# At the moment of its conception, the Bu will start at a point A
class Bu():
    def __init__(self,pA=(0,0),pG=(0,0),pB=(0,0)):
        self.pA = pA
        self.pG = pA
        self.pG_inverse = self.pG
        self.pB = self.pA #set the starting and end position of the line at the same point at the beginning
        self.ptA_Set = True
        self.ptB_Set = False #determines whether the points G and B that make the unit should change
        self.finishedBu = False
        self.draw_laterals = False #activates when the lateral lines reflecting gravity points have to show up
        self.saved_points = []
    
    def draw(self, coor, preview_image):
        # coor = Coordinate(int(coor.x()), int(coor.y()))
        if self.ptA_Set and not self.ptB_Set:
            self.pB = self.pG = coor
        # RENDER THE LINE SEGMENTS OF THE BEZIER CURVE
        self.saved_points = []
        startingX = self.pA.x
        startingY = self.pA.y
        for i in range(SUBDIVS+1):
            self.saved_points.append((Coordinate(int(startingX),int(startingY))))
            
            # Calculate the relative distance traveled in the time i starting at A
            x1 = self.pA.x + (self.pG.x - self.pA.x) * (i * SEGMENT_DISTANCE)
            y1 = self.pA.y + (self.pG.y - self.pA.y) * (i * SEGMENT_DISTANCE)

            x2 = self.pG.x + (self.pB.x - self.pG.x) * (i * SEGMENT_DISTANCE)
            y2 = self.pG.y + (self.pB.y - self.pG.y) * (i * SEGMENT_DISTANCE)

            x = x1 + (x2 - x1) * (i * SEGMENT_DISTANCE)
            y = y1 + (y2 - y1) * (i * SEGMENT_DISTANCE)

            # pygame.draw.line(display,brush_settings["color"],(startingX,startingY),(x,y),3)

            startingX = x
            startingY = y
            
        self.saved_points.append((Coordinate(int(startingX),int(startingY))))


        
        for idx,point in enumerate(self.saved_points):
            if idx < len(self.saved_points)-1:
                self.saved_points[idx+1]
                cv2.line(preview_image, point, self.saved_points[idx+1], color=brush_settings["color"], thickness=1)
            # cv2.circle(preview_image, (point.x, point.y), 2, brush_settings["color"], -1)
        
        if self.draw_laterals:
            # calculate the distance between pB and the cursor
            mx, my = coor
            a = mx - self.pB.x
            o = my - self.pB.y
            radius = (a**2 + o**2)**0.5
            # If the radius over 5, let's assume the user wants to update pG, in which case we just calculate the inverse pG_inverse
            if radius > 5:
                # get the angle between the point B and the position of the cursor
                angle = math.atan2(o,a)
                # calculate the position in x,y for the pointG and pointG_inverse, using the distance pB-cursor as radius
                x_G_inverse = self.pB[0] + (math.cos(angle) * radius)
                y_G_inverse = self.pB[1] + (math.sin(angle) * radius)
                x_G = self.pB[0] - (math.cos(angle) * radius)
                y_G = self.pB[1] - (math.sin(angle) * radius)
                self.pG = Coordinate(int(x_G),int(y_G))
                self.pG_inverse = Coordinate(int(x_G_inverse),int(y_G_inverse))
                
                
                cv2.line(preview_image, self.pB, self.pG, color=brush_settings["color"], thickness=1)
                cv2.circle(preview_image, self.pG, 2, brush_settings["color"], -1)
                
                cv2.line(preview_image, self.pB, self.pG_inverse, color=brush_settings["color"], thickness=1)
                cv2.circle(preview_image, self.pG_inverse, 2, brush_settings["color"], -1)
                

            else:
                # get the angle between the point B and the position of the pointG
                static_a = self.pB[0] - self.pG[0]
                static_o = self.pB[1] - self.pG[1]
                dist_B_G = (static_a**2 + static_o**2) ** 0.5
                angle_BG = math.atan2(static_o,static_a)
                x_G_inverse = self.pB[0] + (math.cos(angle_BG) * dist_B_G)
                y_G_inverse = self.pB[1] + (math.sin(angle_BG) * dist_B_G)
                self.pG_inverse = Coordinate(x_G_inverse,y_G_inverse)
                    

    def savePoints(self):
        self.saved_points = []
        startingX = self.pA[0]
        startingY = self.pA[1]
        # self.saved_points.append((startingX,startingY))
        for i in range(SUBDIVS):
            # Calculate the relative distance traveled in the time i starting at A
            x1 = self.pA[0] + (self.pG[0] - self.pA[0]) * (i * SEGMENT_DISTANCE)
            y1 = self.pA[1] + (self.pG[1] - self.pA[1]) * (i * SEGMENT_DISTANCE)

            x2 = self.pG[0] + (self.pB[0] - self.pG[0]) * (i * SEGMENT_DISTANCE)
            y2 = self.pG[1] + (self.pB[1] - self.pG[1]) * (i * SEGMENT_DISTANCE)

            x = x1 + (x2 - x1) * (i * SEGMENT_DISTANCE)
            y = y1 + (y2 - y1) * (i * SEGMENT_DISTANCE)

            # pygame.draw.line(display,(random.randint(0,255),random.randint(0,255),random.randint(0,255)),(startingX,startingY),(x,y),3)
            
            startingX = x
            startingY = y
            self.saved_points.append((startingX,startingY))
            
                
 
# DD. SPLINE
# spline = Spline()
# interp. the collection of Bezier units that create a spline
class Bezierman():
    def __init__(self):
        self.first_click = True
        self.lobu = []
        self.doneSpline = False
    
    def draw(self, coor, preview_image):
        ########## draw each bezier unit
        for bu in self.lobu:
            bu.draw(coor, preview_image)
        
    def onMouseEventUp(self, coor):
        # if self.first_click:
        #     self.first_click = False

        if len(self.lobu)>0:
            self.lobu[-1].finishedBu = True #THE LAST ELEMENT IS THE PREVIOUS BEZIER UNIT, that has already been finished
        else:
            bu = Bu(coor)
            self.lobu.append(bu)
                
    def onMouseEventDown(self, coor):
        if len(self.lobu)>0:
            last_bu = self.lobu[-1] #active bezier unit is last in the list
            if last_bu.ptA_Set and not last_bu.ptB_Set and not last_bu.finishedBu:
                last_bu.ptB_Set = True
        
    
    def update(self, coor):
        if len(self.lobu)>0:
            last_bu = self.lobu[-1] #the active bezier unit
            if last_bu.ptA_Set and not last_bu.ptB_Set and not last_bu.finishedBu:
                last_bu.pB = coor
            elif last_bu.ptA_Set and last_bu.ptB_Set and not last_bu.finishedBu:
                # Draw gravity lines using pointer and draw Bezier curves
                last_bu.draw_laterals = True
                # last_bu.pB = pygame.mouse.get_pos()
            elif last_bu.ptA_Set and last_bu.ptB_Set and last_bu.finishedBu:
                if not self.doneSpline:
                    last_bu.draw_laterals = False
                    bu = Bu(last_bu.pB)
                    # if there's already other Bu's, use the previous (i = -1) Bu
                    # variable lastbu.pG for this pG pos
                    bu.pG = last_bu.pG_inverse
                    self.lobu.append(bu)
    
    def finishPolygon(self):
        if brush_settings["is_brush_mode"] == "bezier":
            final_points = []
            for bu in self.lobu[:-1]:
                final_points += bu.saved_points                
            # points = [(pt.x, pt.y) for pt in self.current_polygon["POINTS"]]
            points = np.array([[p.x, p.y] for p in final_points], np.int32)
            points = points.reshape((-1, 1, 2))
            cv2.fillPoly(display_settings["mask"], [points], color=brush_settings["color"])
            self.current_polygon = {"DONE":False, "POINTS":[], "COLOR":None}
            self.lobu = []
            
    def pop_last_point(self):
        if len(self.lobu)>1:
            self.lobu = self.lobu[:-2]
   
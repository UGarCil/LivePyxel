from constants import *
import numpy as np
import math

# DD. FREEHAND_MANAGER
# freehandman = FreehandMan()
# interp. a set of attributes used to define the freehand polygons that will be created on top of the mask
class Freehandman():
    def __init__(self):
        self.current_polygon = {"DONE": False, "POINTS": [], "COLOR": None}
        self.distance_threshold = 4  # Minimum distance to add a new point
        self.started = False
        
    def updatePolyOnMove(self, coor):
        """
        Updates the polygon based on cursor movement.
        Adds a new point only if the distance from the last point is greater than threshold.
        """
        if not self.started:
            return

        coor_x, coor_y = coor
        
        # If this is the first point, add it directly
        if len(self.current_polygon["POINTS"]) == 0:
            self.current_polygon["POINTS"].append(Coordinate(coor_x, coor_y))
            return
        
        # Get the last point
        last_point = self.current_polygon["POINTS"][-1]
        
        # Calculate Pythagorean distance
        distance = math.sqrt((coor_x - last_point.x)**2 + (coor_y - last_point.y)**2)
        
        # Only add point if distance is greater than threshold
        if distance > self.distance_threshold:
            self.current_polygon["POINTS"].append(Coordinate(coor_x, coor_y))
    
    def startFreehand(self, coor):
        """
        Starts a new freehand polygon at the given coordinate.
        Call this when the user starts drawing (e.g., mouse down).
        """
        coor_x, coor_y = coor
        self.current_polygon = {"DONE": False, "POINTS": [], "COLOR": None}
        self.current_polygon["POINTS"].append(Coordinate(coor_x, coor_y))
        self.started = True
        
    def finishPolygon(self):
        """
        Finishes the current polygon and applies it to the mask.
        Call this when the user presses Enter.
        """
        if not brush_settings["is_brush_mode"] == "freehand":  # Updated condition
            return
            
        points = np.array([[p.x, p.y] for p in self.current_polygon["POINTS"]], np.int32)
        points = points.reshape((-1, 1, 2))
        
        # evaluate if there are any points to annotate
        if len(points) == 0:
            return 
        
        if os_settings["substractive_mode"]:
            _boolean_mask = np.zeros_like(display_settings["list_of_mask"][-1])
            cv2.fillPoly(_boolean_mask, [points], color=(255, 255, 255))
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
        self.started = False

    def pop_last_point(self):
        """
        Removes the last point from the current polygon.
        """
        if len(self.current_polygon["POINTS"]) > 0:
            self.current_polygon["POINTS"].pop(-1)
            
    def get_current_points(self):
        """
        Returns the current polygon points for preview/rendering purposes.
        """
        return self.current_polygon["POINTS"]
    
    def clear_current_polygon(self):
        """
        Clears the current polygon without finishing it.
        """
        self.current_polygon = {"DONE": False, "POINTS": [], "COLOR": None}
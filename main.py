from constants import *  # Replace with your constants for window size
from webcamUtils import VideoDeviceManager  # Replace with your own webcam capture function
from UIMainWindow import Ui_MainWindow
from polyman import Polyman
from bezierman import Bezierman
class ImageAnnotator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.polygon_manager = None
        self.bezier_manager = None
        self.bezier_current_pos = None
        self.mainUI = Ui_MainWindow()
        self.mainUI.setupUi(self)
        self.imageFrozen = False #image captured
        # initialize the webcam
        self.deviceManager = VideoDeviceManager()
        cursor_settings["in_display"] = False #whether the cursor is inside the image display, which is the only time painting tools should work        
        
        # Set up the main window
        # self.setGeometry(0, 0, W + LATERAL_PADDING.x, H + TOP_PADDING.y)
        # self.setWindowTitle("Micrometry v.2.0")

        # OpenCV image processing setup
        display_settings["image"] = self.deviceManager.get_image_from_webcam()
        # self.image = self.deviceManager.get_image_from_webcam()  # Load first frame from webcam
        display_settings["mask"] = np.zeros_like(display_settings["image"])  # Mask for drawing
        # self.maskImage = np.zeros_like(self.image)  # Mask for drawing
        
        # self.mainUI.mask = display_settings["mask"]
        self.brush_preview_color = (0, 150, 0)  # Darker green for preview
        self.mainUI.brush_slider.setValue(70)
        self.maskStrength = self.mainUI.brush_slider.value()
        

        # Button webcam
        self.mainUI.btn_switch_webcam.clicked.connect(lambda: self.deviceManager.change_video_device(self))
        self.mainUI.brush_slider.valueChanged.connect(self.updateSliderBrushStrength)
        self.mainUI.btn_annotate.clicked.connect(lambda: self.deviceManager.save_image(display_settings["image"], display_settings["mask"]))
        self.mainUI.btn_add.clicked.connect(lambda: self.mainUI.add_btn_block(label_text="New Label"))
        self.mainUI.btn_capture.clicked.connect(self.captureManager)
        self.mainUI.polygon_button.clicked.connect(lambda: self.update_paint_mode("polygon"))
        self.mainUI.brush_button.clicked.connect(lambda: self.update_paint_mode("brush"))
        self.mainUI.bezier_button.clicked.connect(lambda: self.update_paint_mode("bezier"))

        # Enable mouse tracking for the window and image display label
        self.setMouseTracking(True)
        self.mainUI.centralwidget.setMouseTracking(True)
        self.mainUI.imageDisplay.setMouseTracking(True)

        # Mouse tracking and drawing setup
        self.drawing = False  # Track if drawing
        self.last_point = QPoint()  # Track the last mouse point
        self.current_pos = QPoint()  # Track current mouse position for brush preview

        # Timer for updating webcam feed
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_webcam_feed)
        self.timer.start(30)  # Update every 30 milliseconds (~33 FPS)

        # Create a container for the edit button blocks and add the first buttonblock
        self.mainUI.add_btn_block(label_text="New Label")
        
        # Add Ctrl+Z behaviour
        # Create a shortcut for Ctrl+Z and connect it to a custom function
        self.shortcut_undo = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.shortcut_undo.activated.connect(self.handle_undo)
        
        # Add ESC behaviour
        # Create a shortcut for Escape and connect it to a custom function
        self.shortcut_undo = QShortcut(QKeySequence("Escape"), self)
        self.shortcut_undo.activated.connect(self.reset_tool)
        
        # show application in fullscreen
        # self.showFullScreen()
        self.showMaximized()

        self.update_image_display()

    def reset_tool(self):
        # if polygon mode
        if brush_settings["is_brush_mode"] == "polygon":
            self.polygon_manager = Polyman()
        elif brush_settings["is_brush_mode"] == "bezier":
            self.bezier_manager = Bezierman()

    def handle_undo(self):
        # if polygon mode
        if brush_settings["is_brush_mode"] == "polygon":
            self.polygon_manager.pop_last_point()
        elif brush_settings["is_brush_mode"] == "bezier":
            self.bezier_manager.pop_last_point()

    # Update the tool MODE
    def update_paint_mode(self,mode:str):
        brush_settings["is_brush_mode"] = mode
        if brush_settings["is_brush_mode"] == "polygon":
            self.polygon_manager = Polyman()
        elif brush_settings["is_brush_mode"] == "bezier":
            self.bezier_manager = Bezierman()
            
        

    def captureManager(self):
        self.imageFrozen = not self.imageFrozen
        if self.imageFrozen:
            self.mainUI.btn_capture.setText("Release \n(Spacebar)")
        else:
            self.mainUI.btn_capture.setText("Capture \n(Spacebar)")

    def updateSliderBrushStrength(self):
        """Handle the slider value change and update the brush size."""
        # Get the new value of the slider
        self.maskStrength = self.mainUI.brush_slider.value()

        # Optionally, update the UI or take other actions
        # print(f"New brush size: {brush_settings["size"]}")
        self.update_image_display()  # Update the image to reflect the new brush size
    

    def update_webcam_feed(self):
        """Capture and display a new frame from the webcam."""
        if not self.imageFrozen:
            display_settings["image"] = self.deviceManager.get_image_from_webcam()  # Load first frame from webcam
            # display_settings["image"] = cv2.resize(display_settings["image"], (W, H))  # Resize image to fit the window
        self.update_image_display()

    def update_image_display(self):  
        """Overlay the mask on top of the image using the mask's values wherever they are non-zero."""
        # Create a copy of the original image
        rendered_image = display_settings["image"].copy()

        # make a copy of the mask RENDERED_MASK to avoid modifing the original, allowing felixibility in visualizations
        rendered_mask = display_settings["mask"].copy()
        
        
        
        # MASK_PIXELS_FILTER = Identify the color pixels that have some color in the RENDERED_MASK
        mask_pixels_filter = rendered_mask[...,:3] 
        mask_pixels_filter = np.any(mask_pixels_filter != 0, axis = -1)
        
        new_brush_intensity = self.maskStrength/100
        # Blend the mask with the image
        # Blend the mask's RGB channels with the original image
        rendered_image[mask_pixels_filter, :3] = (
            new_brush_intensity * rendered_mask[mask_pixels_filter, :3] +  # Mask color contribution
            (1 - new_brush_intensity) * rendered_image[mask_pixels_filter, :3]  # Original image contribution
        ).astype(np.uint8)  # Ensure the result stays within valid RGB values


        if brush_settings["is_brush_mode"] == "brush":
            # Handle brush preview (if not drawing)
            if not self.drawing:
                preview_image = rendered_image.copy()
                if not self.current_pos.isNull():
                    # Draw the brush preview circle
                    cv2.circle(preview_image, (self.current_pos.x(), self.current_pos.y()), brush_settings["size"] // 2,
                            self.brush_preview_color, 2)
                qimage = self.convert_cv_qt(preview_image)
            else:
                qimage = self.convert_cv_qt(rendered_image)

            # Set the QPixmap on the QLabel
            self.mainUI.imageDisplay.setPixmap(QPixmap.fromImage(qimage))
            
        # POLYGON MODE 
        elif brush_settings["is_brush_mode"] == "polygon":
            polygon = self.polygon_manager.current_polygon
            preview_image = rendered_image.copy()
            # Convert the list of namedtuples to a NumPy array of shape (n_points, 1, 2)
            # points_array = np.array([[p.x, p.y] for p in polygon["POINTS"]], np.int32)
            # points_array = points_array.reshape((-1, 1, 2))
            
            # if polygon["DONE"]:
            #     if polygon == self.polygon_manager.lopolygon[-1]:
            #         # Draw the filled polygon on the mask
            #         cv2.fillPoly(display_settings["mask"], [points_array], color=brush_settings["color"])
            #     else:
            #         cv2.fillPoly(display_settings["mask"], [points_array], polygon["COLOR"])
                # Draw the polygon on the mask
                # cv2.polylines(preview_image, [points_array], isClosed=True, color=brush_settings["color"], thickness=4)    
                # Draw a circle on each point (vertex)
            for idx,point in enumerate(polygon["POINTS"]):
                if idx < len(polygon["POINTS"])-1:
                    cv2.line(preview_image, point, polygon["POINTS"][idx+1], color=brush_settings["color"], thickness=1)
                cv2.circle(preview_image, (point.x, point.y), 2, brush_settings["color"], -1)
                        

            qimage = self.convert_cv_qt(preview_image)

            # Set the QPixmap on the QLabel
            self.mainUI.imageDisplay.setPixmap(QPixmap.fromImage(qimage))
        
        # BEZIER mode
        elif brush_settings["is_brush_mode"] == "bezier":
            preview_image = rendered_image.copy()
            if not self.bezier_manager is None and len(self.bezier_manager.lobu) >0:
                self.bezier_manager.draw(self.bezier_current_pos,preview_image)
                # bu = self.bezier_manager.lobu[-1]
                
                # Convert the list of namedtuples to a NumPy array of shape (n_points, 1, 2)
                # points_array = np.array([[p.x, p.y] for p in bu.points], np.int32)
                # points_array = points_array.reshape((-1, 1, 2))
                
                # if polygon["DONE"]:
                #     if polygon == self.polygon_manager.lopolygon[-1]:
                #         # Draw the filled polygon on the mask
                #         cv2.fillPoly(display_settings["mask"], [points_array], color=brush_settings["color"])
                #     else:
                #         cv2.fillPoly(display_settings["mask"], [points_array], polygon["COLOR"])
                    # Draw the polygon on the mask
                    # cv2.polylines(preview_image, [points_array], isClosed=True, color=brush_settings["color"], thickness=4)    
                    # Draw a circle on each point (vertex)
                # for idx,point in enumerate(polygon["POINTS"]):
                #     if idx < len(polygon["POINTS"])-1:
                #         cv2.line(preview_image, point, polygon["POINTS"][idx+1], color=brush_settings["color"], thickness=1)
                #     cv2.circle(preview_image, (point.x, point.y), 2, brush_settings["color"], -1)
                            

                qimage = self.convert_cv_qt(preview_image)

                # Set the QPixmap on the QLabel
                self.mainUI.imageDisplay.setPixmap(QPixmap.fromImage(qimage))
            else:
                qimage = self.convert_cv_qt(preview_image)
                self.mainUI.imageDisplay.setPixmap(QPixmap.fromImage(qimage))
            
            
    def convert_cv_qt(self, cv_img):
        """Convert from an OpenCV image to QImage."""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        return QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)

    def map_to_image_display(self, global_pos):
        """Convert global mouse position to position relative to image display, considering potential scaling."""
        # Map global position to the image display's local coordinates
        local_pos = self.mainUI.imageDisplay.mapFromGlobal(global_pos)
        label_width = self.mainUI.imageDisplay.width()
        label_height = self.mainUI.imageDisplay.height()
        image_height, image_width = display_settings["image"].shape[:2]
        
        # Scale mouse position based on how the image is resized
        tx = local_pos.x()/label_width
        ty = local_pos.y()/label_height
        mapped_x = int(tx * label_width)
        mapped_y = int(ty * label_height)
        
        
        # scale_w = image_width / label_width
        # scale_h = image_height / label_height

        # mapped_x = int(local_pos.x() * 1)
        # mapped_y = int(local_pos.y() * 1)

        # Ensure the position is within the image bounds
        mapped_x = max(0, min(mapped_x, image_width - 1))
        mapped_y = max(0, min(mapped_y, image_height - 1))


        return QPoint(mapped_x, mapped_y)

    def mousePressEvent(self, event):
        """Start drawing when the mouse is pressed."""
        if cursor_settings["in_display"]:
            if brush_settings["is_brush_mode"] == "brush":
                if event.button() == Qt.LeftButton:
                    self.drawing = True
                    self.erasing = False
                    global_pos = event.globalPos()  # Get global position
                    self.last_point = self.map_to_image_display(global_pos)
                    cv2.circle(display_settings["mask"], (self.last_point.x(), self.current_pos.y()), brush_settings["size"] // 2,
                                brush_settings["color"],-1)

                if event.button() == Qt.RightButton:
                    self.erasing = True
                    self.drawing = False
                    global_pos = event.globalPos()  # Get global position
                    self.last_point = self.map_to_image_display(global_pos)
                    
            # if polygon mode
            elif brush_settings["is_brush_mode"] == "polygon":
                global_pos = event.globalPos()  # Get global position
                self.last_point = self.map_to_image_display(global_pos)
                local_pos = Coordinate(self.last_point.x(), self.last_point.y())
                self.polygon_manager.current_polygon["POINTS"].append(local_pos)
                
            elif brush_settings["is_brush_mode"] == "bezier":
                self.bezier_manager.onMouseEventDown(self.bezier_current_pos)
                
    def mouseMoveEvent(self, event):
        """Track mouse movement and update the brush preview."""
        if cursor_settings["in_display"]:
            if brush_settings["is_brush_mode"] == "brush":
                global_pos = event.globalPos()  # Get global position of the mouse
                self.current_pos = self.map_to_image_display(global_pos)

                if event.buttons() & Qt.LeftButton and self.drawing:
                    # Update the mask with the brush stroke in OpenCV
                    cv2.line(display_settings["mask"], (self.last_point.x(), self.last_point.y()), 
                            (self.current_pos.x(), self.current_pos.y()), brush_settings["color"], brush_settings["size"])
                    self.last_point = self.current_pos

                elif event.buttons() & Qt.RightButton and self.erasing:
                    # Erase by drawing over the mask with a transparent color
                    cv2.line(display_settings["mask"], (self.last_point.x(), self.last_point.y()), 
                            (self.current_pos.x(), self.current_pos.y()), (0, 0, 0, 0), brush_settings["size"])  # Assuming (0, 0, 0, 0) is transparent
                    self.last_point = self.current_pos
                
            elif cursor_settings["in_display"] and brush_settings["is_brush_mode"] == "bezier":
                global_pos = event.globalPos()  # Get global position
                self.last_point = self.map_to_image_display(global_pos)
                self.bezier_current_pos = Coordinate(self.last_point.x(), self.last_point.y())
                self.bezier_manager.update(self.bezier_current_pos)
            
            self.update_image_display()
            
        
        

    def mouseReleaseEvent(self, event):
        """Finish drawing when the mouse is released."""
        if cursor_settings["in_display"]:
            if brush_settings["is_brush_mode"] == "brush":                
                if event.button() == Qt.LeftButton:
                    self.drawing = False
            if brush_settings["is_brush_mode"] == "bezier":
                self.bezier_manager.onMouseEventUp(self.bezier_current_pos)

    def wheelEvent(self, event):
        """Handle mouse scroll events."""
        if cursor_settings["in_display"] and brush_settings["is_brush_mode"]=="brush":
            delta = event.angleDelta().y()  # Get the vertical scroll amount
            if delta > 0:
                brush_settings["size"] += brush_settings["resize_sensitivity"]
            elif delta < 0:
                brush_settings["size"] -= 3
                brush_settings["size"] = 1 if brush_settings["size"] <= 1 else brush_settings["size"]

            self.update_image_display()  # Update the display to reflect the new brush size
        
    def keyReleaseEvent(self, event):
        if brush_settings["is_brush_mode"] == "polygon":
            # Check if the Enter key was pressed
            if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
                self.polygon_manager.finishPolygon()
                
        elif brush_settings["is_brush_mode"] == "bezier":
            if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
                self.bezier_manager.finishPolygon()
            
            # else:
            #     super().keyPressEvent(event)  # Pass the event to the parent class for default behavior

    def closeEvent(self, event):
        # This function is triggered when the window is about to close
        reply = QMessageBox.question(self, 'Window Close', 
                                    'Would you like to save the project before closing the window?',
                                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, 
                                    QMessageBox.Cancel)

        if reply == QMessageBox.Yes:
            # Save the project and close the window
            self.mainUI.save_json_file()
            event.accept()  # Accept the event to close the window
        elif reply == QMessageBox.No:
            # Do not save, just close the window
            event.accept()  # Accept the event to close the window
        else:
            # Cancel the close action
            event.ignore()  # Ignore the close event, keeping the window open
        
    # def enterEvent(self, event):
        
    #     """Hide the cursor when it enters the imageDisplay area."""
    #     if self.mainUI.imageDisplay.underMouse():
    #         print("cursor in image display!")
    #         cursor_settings["in_display"] = True
    #         self.mainUI.imageDisplay.setCursor(Qt.BlankCursor)
        
            
    # def leaveEvent(self, event):
    #     """Restore the cursor when it leaves the imageDisplay area."""
    #     self.mainUI.imageDisplay.setCursor(Qt.ArrowCursor)  # or any other cursor type you want
    #     print("cursor not in image display!")
    #     cursor_settings["in_display"] = False

if __name__ == "__main__":
    # Enable High DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    # Use the high-resolution icons and fonts
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    window = ImageAnnotator()
    window.show()
    sys.exit(app.exec_())
from .constants import *  
from .video_device_manager import VideoDeviceManager, ImageEditor
from .ui_main_window import Ui_MainWindow
from .polyman import Polyman
from .bezierman import Bezierman
from .bucketman import Bucketman
from .binaman import Binman
from .freehandman import Freehandman
import platform, subprocess
# C.D. IMAGE_ANNOTATOR
# This is the main class that handles the image annotation tool. It is responsible for the following:
# 1. Handling the annotation tools (brush, polygon, bezier)
# 2. Handling the mouse events for drawing 
# 3. Handling the webcam integration >>> VideoDeviceManager()
# 4. Handling the image display >>> VideoDeviceManager()
# 5. Handling the UI components >>> Ui_MainWindow()
class ImageAnnotator(QMainWindow):
    def __init__(self):
        super().__init__()
        display_settings["statusBar"] = self.statusBar
        display_settings["statusBar"]().showMessage("ready")  # Initial message
        # Tools init
        self.polygon_manager = None
        self.bezier_manager = None
        self.bezier_current_pos = None
        self.freehand_current_pos = None
        self.binary_mask = None
        self.mainUI = Ui_MainWindow()
        self.bucket_manager = None
        self.mainUI.setupUi(self)
        self.imageFrozen = False #image captured

        # Webcam init
        self.deviceManager = VideoDeviceManager()
        cursor_settings["in_display"] = False #whether the cursor is inside the image display, which is the only time painting tools should work        

        # Image annotation init starts None because needs to know which folder to load
        self.editorManager = None
        # OpenCV image processing setup
        
        display_settings["image"] = self.deviceManager.get_image_from_webcam()
        display_settings["list_of_mask"] = [np.zeros_like(display_settings["image"])]
        
        # initialize the brush settings
        self.brush_preview_color = (0, 150, 0)  # Darker green for preview
        self.mainUI.brush_slider.setValue(70)
        self.mainUI.binarythres_slider.setValue(127) #min 0 and max 255
        brush_settings["opacity"] = self.mainUI.brush_slider.value()
        brush_settings["binary_mask_thres"] = self.mainUI.binarythres_slider.value()
        

        # Button webcam
        self.mainUI.btn_switch_webcam.clicked.connect(lambda: self.deviceManager.change_video_device(self))
        self.mainUI.brush_slider.valueChanged.connect(self.updateSliderBrushStrength)
        self.mainUI.binarythres_slider.valueChanged.connect(self.updateSliderBinaryThreshold)
        self.mainUI.btn_annotate.clicked.connect(self.save_image_handler)
        self.mainUI.btn_add.clicked.connect(lambda: self.mainUI.add_btn_block(label_text="New Label"))
        self.mainUI.btn_capture.clicked.connect(self.captureManager)
        self.mainUI.polygon_button.clicked.connect(lambda: self.update_paint_mode("polygon"))
        self.mainUI.brush_button.clicked.connect(lambda: self.update_paint_mode("brush"))
        self.mainUI.bezier_button.clicked.connect(lambda: self.update_paint_mode("bezier"))
        self.mainUI.bucket_button.clicked.connect(lambda: self.update_paint_mode("bucket"))
        self.mainUI.binmask_button.clicked.connect(lambda: self.update_paint_mode("binmask"))
        self.mainUI.freehand_button.clicked.connect(lambda: self.update_paint_mode("freehand"))
        self.mainUI.isAdditive_button.clicked.connect(self.update_isAdditive_mode)
        self.mainUI.isTopLayerOnly_button.clicked.connect(self.update_isTopLayerOnly_button_mode)
        self.mainUI.openFolder_button.clicked.connect(self.openFolder)
        self.mainUI.editMode_button.clicked.connect(self.openFolderForAnnotations)
        self.mainUI.next_btn.clicked.connect(lambda: self.updateImageInEditorMode("next", self.mainUI.number_input))
        self.mainUI.prev_btn.clicked.connect(lambda: self.updateImageInEditorMode("prev", self.mainUI.number_input))
        self.mainUI.number_input.returnPressed.connect(lambda: self.number_input_handler(self.mainUI.number_input))


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
        
    def number_input_handler(self, number_input):
        # Get the text from the input
        text = number_input.text()
        
        # Convert to integer (since we're using QIntValidator)
        if text:  # Check if the input is not empty
            try:
                number = int(text)
                if os_settings["config"] != "" and self.editorManager is not None:
                    update_text = self.editorManager.set_current_image_index(number)  # text updated after clamping to max index
                    number_input.setText(str(update_text))  # Update the input field with the clamped value
                # self.update_index_image(number)  # Call your helper method
            except ValueError:
                # This shouldn't happen because of QIntValidator, but just in case
                pass 
        
    def save_image_handler(self):
        '''
        Handle the right saving method depending upon the mode of the application
        '''
        if os_settings["webcam_mode"]:
            self.deviceManager.save_image()
        else:
            self.editorManager.save_image()
        
            
            
    def updateImageInEditorMode(self, direction, number_input):
        '''
        Update the image in editor mode
        '''
        if self.editorManager is not None:
            if direction == "next":
                self.editorManager.next_image()
                number_input.setText(str(self.editorManager.index_image))  # Update the input field with the current image index
            elif direction == "prev":
                self.editorManager.prev_image()
                number_input.setText(str(self.editorManager.index_image))  # Update the input field with the current image index
            
            # # Update the image display with the new image
            # self.update_image_display()
        
    def openFolderForAnnotations(self):
        '''
        Access the images and files for annotation
        '''
        # There are two main cases: User followed LivePyxel structure or has only images folder
        if os_settings["config"] != "":
            if os_settings["webcam_mode"]:                
                # path = os.path.normpath(os_settings["images_path"])  # Normalize the path format
                os_settings["webcam_mode"] = False
                # Pause the webcam feed
                self.deviceManager.in_pause = True
                # If there no ImageEditor instance, create one, which also automates finding the files
                if self.editorManager is None and os_settings["config"] != "":
                    self.editorManager = ImageEditor()
            else:
                # Reset the masks
                _msk = np.zeros_like(display_settings["list_of_mask"][-1])
                display_settings["list_of_mask"] = [_msk]
                # self.deviceManager.read_new_VideoDevice(0)  # Read the new video device
                self.deviceManager.in_pause = False
                os_settings["webcam_mode"] = True
                self.editorManager = None
        else:
            QMessageBox.warning(self, "Warning", "No directory has been set yet. Please open or create a new project")

    # Open the folder containing the images and masks
    def openFolder(self):
        """
        Open a folder in the default file explorer
        Works across Windows, macOS, and Linux
        """
        
        if os_settings["config"] != "":
            path = os.path.normpath(os_settings["images_path"])  # Normalize the path format
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", path])
            else:  # Linux
                subprocess.run(["xdg-open", path])
        else:
            QMessageBox.warning(self, "Warning", "No directory has been set yet. Please open or create a new project")

    # Change the status of the isAdditive button
    def update_isAdditive_mode(self):
        os_settings["substractive_mode"] = not os_settings["substractive_mode"]
        if os_settings["substractive_mode"]:
            self.mainUI.isAdditive_button.setIcon(self.mainUI.isAdditive_button_off_icon)
            
            brush_settings["color_before_substracting_mode"] = tuple(brush_settings["color"])
            if brush_settings["is_brush_mode"] != "binmask":
                brush_settings["color"] = (255, 255, 255)
            brush_settings["thickness"] = 2
        else:
            self.mainUI.isAdditive_button.setIcon(self.mainUI.isAdditive_button_on_icon)
            brush_settings["color"] = tuple(brush_settings["color_before_substracting_mode"])
            brush_settings["thickness"] = 1
    
    # Change the status of the isAdditive button
    def update_isTopLayerOnly_button_mode(self):
        os_settings["top_layer_edit"] = not os_settings["top_layer_edit"]
        if os_settings["top_layer_edit"]:
            self.mainUI.isTopLayerOnly_button.setIcon(self.mainUI.isTopLayerOnly_button_off_icon)
        else:
            self.mainUI.isTopLayerOnly_button.setIcon(self.mainUI.isTopLayerOnly_button_on_icon)
                

    def reset_tool(self):
        # if polygon mode
        if brush_settings["is_brush_mode"] == "polygon":
            self.polygon_manager = Polyman()
        elif brush_settings["is_brush_mode"] == "bezier":
            self.bezier_manager = Bezierman()
        elif brush_settings["is_brush_mode"] == "freeman":
            self.freehand_manager = Freehandman()
        

    def handle_undo(self):
        # if polygon mode
        if brush_settings["is_brush_mode"] == "polygon":
            self.polygon_manager.pop_last_point()
        elif brush_settings["is_brush_mode"] == "bezier":
            self.bezier_manager.pop_last_point()
        elif brush_settings["is_brush_mode"] == "freehand":
            self.freehand_manager.pop_last_point()

    # Update the tool MODE
    def update_paint_mode(self,mode:str):
        brush_settings["is_brush_mode"] = mode
        if brush_settings["is_brush_mode"] == "polygon":
            self.polygon_manager = Polyman()
        elif brush_settings["is_brush_mode"] == "freehand":
            self.freehand_manager = Freehandman()
        elif brush_settings["is_brush_mode"] == "bezier":
            self.bezier_manager = Bezierman()
        elif brush_settings["is_brush_mode"] == "bucket":
            self.bucket_manager = Bucketman(self)
        elif brush_settings["is_brush_mode"] == "binmask":
            self.binary_mask = Binman(self)
        elif brush_settings["is_brush_mode"] == "brush":
            _ = add_empty_mask()
        # iterate over the masks and erase any mask where the maximum value of RGB (without considering alpha) is 0
        # if len(display_settings["list_of_mask"])>1:
        #     for idx, mask in enumerate(display_settings["list_of_mask"]):
        #         if np.max(mask[...,:3]) == 0:
        #             display_settings["list_of_mask"].pop(idx)

    def captureManager(self):
        self.imageFrozen = not self.imageFrozen
        if self.imageFrozen:
            self.mainUI.btn_capture.setText("Release \n(Spacebar)")
            self.deviceManager.image_captured_paused = True
        else:
            self.mainUI.btn_capture.setText("Capture \n(Spacebar)")
            self.deviceManager.image_captured_paused = False

    def updateSliderBrushStrength(self):
        """Handle the slider value change and update the brush size."""
        # Get the new value of the slider
        brush_settings["opacity"] = self.mainUI.brush_slider.value()

        # Optionally, update the UI or take other actions
        # print(f"New brush size: {brush_settings["size"]}")
        self.update_image_display()  # Update the image to reflect the new brush size

    def updateSliderBinaryThreshold(self):
        """Handle the slider value change and update the binary mask threshold."""
        # Get the new value of the slider
        _thres = self.mainUI.binarythres_slider.value()
        # remap the value from 0-99 into an integer between 0-255
        brush_settings["binary_mask_thres"] = int(_thres * 2.55)
        if self.binary_mask is not None:
            self.binary_mask.threshold = brush_settings["binary_mask_thres"]
            

        # Optionally, update the UI or take other actions

    def update_webcam_feed(self):
        """Capture and display a new frame from the webcam."""
        if os_settings["webcam_mode"]:
            if not self.imageFrozen:
                display_settings["image"] = self.deviceManager.get_image_from_webcam()  # Load first frame from webcam
                # display_settings["image"] = cv2.resize(display_settings["image"], (W, H))  # Resize image to fit the window
        else:
            display_settings["image"] = self.editorManager.get_image_from_folder()  # Load first frame from webcam
        self.update_image_display()

    
    def update_image_display(self):  
        """Overlay the mask on top of the image using the mask's values wherever they are non-zero."""
        # Create a copy of the original image
        rendered_image = display_settings["image"].copy()

        # create a merged copy of all the masks to avoid modifying the original, allowing felixibility in visualizations
        rendered_mask = merge_masks(display_settings["list_of_mask"])
        
        # MASK_PIXELS_FILTER = Identify the color pixels that have some color in the RENDERED_MASK
        # Blend the mask's RGB channels with the original image
        # handle brush preview 
        
        # MASK_PIXELS_FILTER = Identify the color pixels that have some color in the RENDERED_MASK
        mask_pixels_filter = rendered_mask[...,:3] 
        mask_pixels_filter = np.any(mask_pixels_filter != 0, axis = -1)
        
        new_brush_intensity = brush_settings["opacity"]/100
        # Blend the mask with the image
        # Blend the mask's RGB channels with the original image
        rendered_image[mask_pixels_filter, :3] = (
            new_brush_intensity * rendered_mask[mask_pixels_filter, :3] +  # Mask color contribution
            (1 - new_brush_intensity) * rendered_image[mask_pixels_filter, :3]  # Original image contribution
        ).astype(np.uint8)  # Ensure the result stays within valid RGB values

        # BRUSH MODE
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
            for idx,point in enumerate(polygon["POINTS"]):
                if idx < len(polygon["POINTS"])-1:
                    cv2.line(preview_image, point, polygon["POINTS"][idx+1], color=brush_settings["color"], thickness=brush_settings["thickness"])
                cv2.circle(preview_image, (point.x, point.y), 2, brush_settings["color"], -1)
                        

            qimage = self.convert_cv_qt(preview_image)

            # Set the QPixmap on the QLabel
            self.mainUI.imageDisplay.setPixmap(QPixmap.fromImage(qimage))
        
        
        # FREEHAND MODE
        elif brush_settings["is_brush_mode"] == "freehand":
            polygon = self.freehand_manager.current_polygon
            preview_image = rendered_image.copy()
            for idx,point in enumerate(polygon["POINTS"]):
                if idx < len(polygon["POINTS"])-1:
                    cv2.line(preview_image, point, polygon["POINTS"][idx+1], color=brush_settings["color"], thickness=brush_settings["thickness"])
                cv2.circle(preview_image, (point.x, point.y), 2, brush_settings["color"], -1)
                        

            qimage = self.convert_cv_qt(preview_image)

            # Set the QPixmap on the QLabel
            self.mainUI.imageDisplay.setPixmap(QPixmap.fromImage(qimage))
        
        # BEZIER mode
        elif brush_settings["is_brush_mode"] == "bezier":
            preview_image = rendered_image.copy()
            if not self.bezier_manager is None and len(self.bezier_manager.lobu) >0:
                self.bezier_manager.draw(self.bezier_current_pos,preview_image)       

                qimage = self.convert_cv_qt(preview_image)

                # Set the QPixmap on the QLabel
                self.mainUI.imageDisplay.setPixmap(QPixmap.fromImage(qimage))
            else:
                qimage = self.convert_cv_qt(preview_image)
                self.mainUI.imageDisplay.setPixmap(QPixmap.fromImage(qimage))
        
        elif brush_settings["is_brush_mode"] == "bucket":
            qimage = self.convert_cv_qt(rendered_image)
            self.mainUI.imageDisplay.setPixmap(QPixmap.fromImage(qimage))
        elif brush_settings["is_brush_mode"] == "binmask":
            # pass the preview image to the binary mask manager
            preview_image = self.binary_mask.display(rendered_image.copy())
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


        # Ensure the position is within the image bounds
        mapped_x = max(0, min(mapped_x, image_width - 1))
        mapped_y = max(0, min(mapped_y, image_height - 1))


        return QPoint(mapped_x, mapped_y)

    def mousePressEvent(self, event):
        """Start drawing when the mouse is pressed."""
        if cursor_settings["in_display"]:
            if brush_settings["is_brush_mode"] == "brush":
                # ################## <BRUSH MOUSE PRESS ENTER EVENT> #######################
                
                if event.button() == Qt.LeftButton:
                    global_pos = event.globalPos()  # Get global position
                    self.last_point = self.map_to_image_display(global_pos)
                    if not os_settings["substractive_mode"]:
                        cv2.circle(display_settings["list_of_mask"][-1], (self.last_point.x(), self.current_pos.y()), brush_settings["size"] // 2,
                                    brush_settings["color"],-1)
                    else:
                        cv2.circle(display_settings["list_of_mask"][-1], (self.last_point.x(), self.current_pos.y()), brush_settings["size"] // 2,
                                    (0,0,0,0),-1)
                # ################## </BRUSH MOUSE PRESS ENTER EVENT> #######################
            # if polygon mode
            elif brush_settings["is_brush_mode"] == "polygon":
                global_pos = event.globalPos()  # Get global position
                self.last_point = self.map_to_image_display(global_pos)
                local_pos = Coordinate(self.last_point.x(), self.last_point.y())
                self.polygon_manager.current_polygon["POINTS"].append(local_pos)
                
            elif brush_settings["is_brush_mode"] == "freehand":
                global_pos = event.globalPos()  # Get global position
                self.last_point = self.map_to_image_display(global_pos)
                local_pos = Coordinate(self.last_point.x(), self.last_point.y())
                self.freehand_manager.startFreehand(local_pos)
                
            elif brush_settings["is_brush_mode"] == "bezier":
                self.bezier_manager.onMouseEventDown(self.bezier_current_pos)
                
            elif brush_settings["is_brush_mode"] == "bucket":
                global_pos = event.globalPos()  # Get global position
                self.last_point = self.map_to_image_display(global_pos)
                local_pos = Coordinate(self.last_point.x(), self.last_point.y())
                self.bucket_manager.onMouseEventDown(local_pos)
            
            elif brush_settings["is_brush_mode"] == "binmask":
                self.binary_mask.onMouseEventDown()
                
    def mouseMoveEvent(self, event):
        """Track mouse movement and update the brush preview."""
        if cursor_settings["in_display"]:
            if brush_settings["is_brush_mode"] == "brush":
                global_pos = event.globalPos()  # Get global position of the mouse
                self.current_pos = self.map_to_image_display(global_pos)
                ############# TODO: ENCAPSULATE BRUSH INTO OBJECT ###################
                if event.buttons() & Qt.LeftButton and not os_settings["substractive_mode"]:
                    # Update the mask with the brush stroke in OpenCV
                    cv2.line(display_settings["list_of_mask"][-1], (self.last_point.x(), self.last_point.y()), 
                            (self.current_pos.x(), self.current_pos.y()), brush_settings["color"], brush_settings["size"])
                    self.last_point = self.current_pos
                    # display_settings["list_of_mask"].append(np.zeros_like(display_settings["list_of_mask"][-1]))

                elif event.buttons() & Qt.LeftButton and os_settings["substractive_mode"]:
                    # Erase by drawing over the mask with a transparent color
                    cv2.line(display_settings["list_of_mask"][-1], (self.last_point.x(), self.last_point.y()), 
                            (self.current_pos.x(), self.current_pos.y()), (255,255,255,255), brush_settings["size"])
                    self.last_point = self.current_pos
                    # display_settings["list_of_mask"].append(np.zeros_like(display_settings["list_of_mask"][-1]))
                ############# END: ENCAPSULATE BRUSH INTO OBJECT ###################
                
            elif cursor_settings["in_display"] and brush_settings["is_brush_mode"] == "bezier":
                global_pos = event.globalPos()  # Get global position
                self.last_point = self.map_to_image_display(global_pos)
                self.bezier_current_pos = Coordinate(self.last_point.x(), self.last_point.y())
                self.bezier_manager.update(self.bezier_current_pos)
            
            elif cursor_settings["in_display"] and brush_settings["is_brush_mode"] == "freehand":
                global_pos = event.globalPos()  # Get global position
                self.last_point = self.map_to_image_display(global_pos)
                self.freehand_current_pos = Coordinate(self.last_point.x(), self.last_point.y())
                self.freehand_manager.updatePolyOnMove(self.freehand_current_pos)
            
            self.update_image_display()
            
        
        

    def mouseReleaseEvent(self, event):
        """Finish drawing when the mouse is released."""
        if cursor_settings["in_display"]:
            if brush_settings["is_brush_mode"] == "brush":                
                if event.button() == Qt.LeftButton:
                    self.drawing = False
                    ############# TODO: ENCAPSULATE BRUSH INTO OBJECT ###################
                    if os_settings["substractive_mode"]:
                        # create a new mask from the selected blob
                        _boolean_mask = np.copy(display_settings["list_of_mask"][-1])
                        # invert the boolean mask so we keep everything EXCEPT the polygon
                        inverted_mask = cv2.bitwise_not(_boolean_mask)      
                        
                        if os_settings["top_layer_edit"]:
                            # Modify the mask on the top layer only (second to last because we added a new layer)
                            display_settings["list_of_mask"][-2] = cv2.bitwise_and(display_settings["list_of_mask"][-2], inverted_mask)
                            display_settings["list_of_mask"].pop(-1)  # Remove the last mask
                            _ = add_empty_mask()  # Add a new empty mask to the list
                            
                        else:
                            # iterate over all masks erasing the pixels delimited by this mask
                            for idx, mask in enumerate(display_settings["list_of_mask"]):
                                display_settings["list_of_mask"][idx] = cv2.bitwise_and(mask, inverted_mask)
                        
                    ############# END: ENCAPSULATE BRUSH INTO OBJECT ###################

            if brush_settings["is_brush_mode"] == "bezier":
                self.bezier_manager.onMouseEventUp(self.bezier_current_pos)
                global_pos = event.globalPos()  # Get global position
                self.last_point = self.map_to_image_display(global_pos)
                self.bezier_current_pos = Coordinate(self.last_point.x(), self.last_point.y())
                self.bezier_manager.update(self.bezier_current_pos)
            if brush_settings["is_brush_mode"] == "freehand":
                if event.button() == Qt.LeftButton:
                    self.freehand_manager.finishPolygon()
                    
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
                self.bezier_manager.finishBezier()
            
            # else:
            #     super().keyPressEvent(event)  # Pass the event to the parent class for default behavior
        elif brush_settings["is_brush_mode"] == "binmask":
            if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
                self.binary_mask.finish_binary_mask()

    def closeEvent(self, event):
        # This function is triggered when the window is about to close
        reply = QMessageBox.question(self, 'Window Close', 
                                    'Would you like to save the project before closing the window?',
                                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, 
                                    QMessageBox.Cancel)

        if reply == QMessageBox.Yes:
            # Save the project and close the window
            self.mainUI.save_json_file()
            self.videoDeviceManager.release_video_device()
            event.accept()  # Accept the event to close the window
        elif reply == QMessageBox.No:
            # Do not save, just close the window
            event.accept()  # Accept the event to close the window
        else:
            # Cancel the close action
            event.ignore()  # Ignore the close event, keeping the window open


# wrapping everything into a main function to allow for easier integration via PyPI and CLI
def main(argv=None):
    """Entry point for CLI and `python -m livepyxel`."""
    argv = argv or sys.argv

    # High-DPI settings (must be set before QApplication is created)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(argv)

    # Construct and show your main window
    window = ImageAnnotator()
    window.show()

    return app.exec_()
        

if __name__ == "__main__":
    raise SystemExit(main())
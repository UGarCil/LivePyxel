from .constants import *

# CD. VideoDeviceManager()
# purp. manage the video device (webcam) and its properties
class VideoDeviceManager():
    def __init__(self):
        # Determine the width and height ratio of the camera
        self.webcam_idx = 0 #the initial index of the webcam
        self.get_avail_devices()
        self.read_new_VideoDevice(self.webcam_idx)
        self.in_pause = False # Whether to return empty frames or not
        self.image_captured_pause = False # Whether to return empty frames or not
        
    def get_avail_devices(self):
    #     print("""      
    #           Finding video devices available...
    #   .-------------------.
    #  /--_--.------.------/|
    #  |     |__||__| [==] ||
    #  |     | .--. | '''' ||
    #  |     || () ||      ||
    #  |     | `--' |      |/
    #  `-----'------'------'  Art by Joan Stark
    #  """)
        print("""
    ##     #####################     
    #      #######     ##########   ##
###     ##########         ###### #### 
           ####### LIVE PYXEL ### #### 
    ##     #######         ###### #### 
           #######     ##########   ##
 ##     ########################   

              """)
        available_cameras = []
        for device_index in range(4):
            cap = cv2.VideoCapture(device_index)
            if cap.isOpened():
                available_cameras.append(device_index)
                cap.release()  # Release the camera once checked
        self.avail_devices = available_cameras

    def release_video_device(self):
        '''
        Triggered when user ends the application, it terminates and releases all cameras that were opened.
        '''
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
            self.cap = None
    
    def change_video_device(self, image_annotator):
        if bool(len(self.avail_devices)):
            self.webcam_idx = (self.webcam_idx + 1)%len(self.avail_devices)
        self.read_new_VideoDevice(self.webcam_idx)
        # OpenCV image processing setup
        image_annotator.image = self.get_image_from_webcam()  # Load first frame from webcam
        # self.image = cv2.resize(self.image, (W, H))  # Resize image to fit the window
        image_annotator.maskImage = np.zeros_like(image_annotator.image)  # Mask for drawing
            
    def read_new_VideoDevice(self,idx):
        global W, H
        self.cap = cv2.VideoCapture(idx)
        
        # Get the width and height of the frame
        W = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        H = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        print(f"Webcam resolution: {W}x{H}")


    # FD. get_image_from_webcam()
    # purp. create a surface class object with the feed from the webcam
    def get_image_from_webcam(self):
        _inf,frame = self.cap.read()
        if self.in_pause or self.image_captured_pause:
            return np.zeros((480, 720, 4), dtype=np.uint8)  # Return a blank image if frame is None
        surface = cv2.cvtColor(frame,0)
        # surface = cv2.rotate(surface, cv2.ROTATE_90_COUNTERCLOCKWISE)
        # surface = cv2.flip(surface,0)
        surface = cv2.resize(surface, (720,480))  #HEIGHT AND WIDTH get flipped because or the counterclockwise rotation
        return surface

    def save_image(self):
        final_mask = merge_masks(display_settings["list_of_mask"])
        final_mask[:, :, 3] = 255

        if not os_settings["images_path"]:
            QtWidgets.QMessageBox.critical(None, "Annotation aborted!", "A directory path couldn't be determined. Please create or load a project and try again")
        else:
            if np.max(final_mask[:, :, 0:3]) != 0:
                # Get the list of existing image files in the directory
                image_files = [f for f in os.listdir(os_settings["images_path"]) if f.startswith("img_") and f.endswith(".png")]
                
                # Find the highest numbered image
                max_num = 0
                for image_file in image_files:
                    try:
                        num = int(image_file.split("_")[1].split(".")[0])
                        if num > max_num:
                            max_num = num
                    except ValueError:
                        continue
                
                # Increment the number for the new image and mask
                new_num = max_num + 1
                image_name = f"img_{new_num:06d}.png"
                mask_name = f"msk_{new_num:06d}.png"
                
                # Save the new image and mask
                image_path = jn(os_settings["images_path"], image_name)
                mask_path = jn(os_settings["masks_path"], mask_name)
                cv2.imwrite(image_path, display_settings["image"])
                cv2.imwrite(mask_path, final_mask)
                
                # Restart the process with a new mask making the first element in the mask set
                _new_mask0 = np.zeros_like(self.get_image_from_webcam())
                display_settings["list_of_mask"] = [_new_mask0]
                
            else:
                QtWidgets.QMessageBox.critical(None, "Annotation aborted!", "Please draw a mask before saving the image")

class ImageEditor():
    '''
    Class to manage an image editor. Used to load images and masks from an already existing directory, throws a warning 
    if the directory is not set. The class also manages the image and mask lists, and the index of the current image.
    '''
    def __init__(self):
        self.index_image = 0
        # Storing the actual arrays avoids having to read the image and mask from the disk every time
        self.current_image = None 
        self.current_mask = None
        self.images_loaded = False # Refreshed when updating index, it flags if an image at index_image has been loaded
        # A list of dictionaries that store an image and a mask
        self.get_files()
    
    def next_image(self):
        self.index_image = (self.index_image + 1) % len(self.files)
        self.images_loaded = False
        self.get_files()
        display_settings["list_of_mask"] = [np.zeros_like(display_settings["list_of_mask"][-1])]
        self.get_image_from_folder()
    
    def prev_image(self):
        self.index_image = (self.index_image - 1) % len(self.files)
        self.images_loaded = False
        self.requires_resize = False
        self.original_height = None 
        self.original_width = None
        self.get_files()
        display_settings["list_of_mask"] = [np.zeros_like(display_settings["list_of_mask"][-1])]
        self.get_image_from_folder()
    
    
    def get_image_from_folder(self):
        '''
        Get the image from the folder specified by the user. The image is then resized to fit the window.
        '''
        if not os_settings["images_path"]:
            QtWidgets.QMessageBox.critical(None, "Annotation aborted!", 
                "A directory path couldn't be determined. Please create or load a project and try again\n"
                "You may have encountered a bug. Please contact author at garcilau@mcmaster.ca")
            return None
        
        if not self.images_loaded:
            try:
                # Read the image from the specified path
                _target_file = self.files[self.index_image]
                frame = cv2.imread(_target_file["imagePath"])
                if frame.ndim == 2:  # If grayscale
                    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGRA)
                elif frame.shape[2] == 3:  # If BGR
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
                
                if frame is None:
                    raise ValueError(f"Could not read image from path: {_target_file['imagePath']}")
                
                # Get the expected dimensions from the first frame
                expected_height, expected_width = display_settings["image"].shape[:2]
                self.original_height, self.original_width = frame.shape[:2]

                
                self.requires_resize = False
                # Resize image (frame) if dimensions don't match
                if frame.shape[:2] != (expected_height, expected_width):
                    # print(f"Resizing mask from {frame.shape} to {(expected_height, expected_width)}")
                    frame = cv2.resize(frame, (expected_width, expected_height))
                    self.requires_resize = True
                
                # Clear and initialize the mask list
                # display_settings["list_of_mask"] = [zero_mask.copy()]
                
                # Load existing mask if available
                if os.path.exists(_target_file["maskPath"]):
                    _mask = cv2.imread(_target_file["maskPath"], cv2.IMREAD_UNCHANGED)  # Preserve original channels
                    if _mask.ndim == 2:  # If grayscale
                        _mask = cv2.cvtColor(_mask, cv2.COLOR_GRAY2BGRA)
                    elif _mask.shape[2] == 3:  # If BGR
                        _mask = cv2.cvtColor(_mask, cv2.COLOR_BGR2BGRA)
                    
                    # Resize mask if dimensions don't match
                    if _mask.shape[:2] != (expected_height, expected_width):
                        # print(f"Resizing mask from {_mask.shape} to {(expected_height, expected_width)}")
                        _mask = cv2.resize(_mask, (expected_width, expected_height))
                    
                    # Replace the zero mask with the loaded mask
                    display_settings["list_of_mask"][-1] = _mask
                else:
                    zero_mask = np.zeros((expected_height, expected_width, 4), dtype=np.uint8)  # 4-channel
                    display_settings["list_of_mask"][-1] = zero_mask.copy()

                self.images_loaded = True
                self.current_image = frame.copy()
                # self.current_mask = display_settings["list_of_mask"][-1].copy()
                return cv2.cvtColor(frame, 0)
            
            except Exception as e:
                QtWidgets.QMessageBox.critical(None, "Error loading image", 
                    f"An error occurred while loading the image:\n{str(e)}")
                return None
        else:
            # If the image is already loaded, just return it
            return self.current_image
    
    def save_image(self):
        '''
        Take the current image and mask. Save only the new mask under the same name as it previously had
        '''
        # statusBar = display_settings["statusBar"]
        final_mask = merge_masks(display_settings["list_of_mask"])
        final_mask[:, :, 3] = 255

        if not os_settings["images_path"]:
            QtWidgets.QMessageBox.critical(None, "Annotation aborted!", "A directory path couldn't be determined. Please create or load a project and try again")
        else:
            if np.max(final_mask[:, :, 0:3]) != 0:
                # # Get the list of existing image files in the directory
                # image_files = [f for f in os.listdir(os_settings["images_path"]) if f.startswith("img_") and f.endswith(".png")]
                
                # # Find the highest numbered image
                # max_num = 0
                # for image_file in image_files:
                #     try:
                #         num = int(image_file.split("_")[1].split(".")[0])
                #         if num > max_num:
                #             max_num = num
                #     except ValueError:
                #         continue
                
                # Increment the number for the new image and mask
                # new_num = max_num + 1
                # image_name = f"img_{new_num:06d}.png"
                # mask_name = f"msk_{new_num:06d}.png"
                
                # Save the new image and mask
                image_path = self.files[self.index_image]["imagePath"] 
                mask_path = self.files[self.index_image]["maskPath"]
                if self.requires_resize:
                    final_img = cv2.resize(display_settings["image"], (self.original_width, self.original_height))
                    final_mask = cv2.resize(final_mask, (self.original_width, self.original_height))
                else:
                    final_img = display_settings["image"]
                    final_mask = final_mask
                cv2.imwrite(image_path, final_img)
                cv2.imwrite(mask_path, final_mask)
                
                # Restart the process with a new mask making the first element in the mask set
                # new_zero_mask = np.zeros_like(display_settings["list_of_mask"][-1])
                # display_settings["list_of_mask"] = []
                # display_settings["list_of_mask"].append(new_zero_mask)
                # Show success message
                
                # Notify the user the image was successfully updated
                success_msg = f"Successfully saved mask to {os.path.basename(mask_path)}"
                show_status_message(success_msg, is_success=True)
                
            else:
                QtWidgets.QMessageBox.critical(None, "Annotation aborted!", "Please draw a mask before saving the image")

    
    def get_files(self):
        '''
        Use the directory specified by the user to gather all the images and masks, and turn them into a list of dictionaries.
        input: None
        output: None
        '''
        self.files = []
        if not os_settings["images_path"]:
            QtWidgets.QMessageBox.critical(None, "Process aborted!", "A directory path couldn't be determined. You may have encountered a bug. Please contact the author at garcilau@mcmaster.ca")
        else:
            # Get the list of image files in the directory
            image_files = [f for f in os.listdir(os_settings["images_path"]) if f.endswith(".png")]
            
            # Create a list of dictionaries with image and mask paths
            for image_file in image_files:
                mask_file = image_file.replace("img_", "msk_")
                # if nothing was changed, add msk_ to the name of the image
                mask_file = "msk_" + image_file if "msk_" not in mask_file else mask_file
                self.files.append({
                    "imagePath": jn(os_settings["images_path"], image_file),
                    "maskPath": jn(os_settings["masks_path"], mask_file)
                })
    
    def set_current_image_index(self,index):
        '''
        Set the current index of the image and mask to be loaded.
        input: index (int) - the index of the image and mask to be loaded
        output: None
        '''
        self.index_image = index
        self.images_loaded = False
        self.get_files()
        # find the maximum index of the files list
        max_index = len(self.files) - 1
        # if index is greater than the maximum index, set it to the maximum index
        if self.index_image > max_index:
            self.index_image = max_index
        self.get_image_from_folder()
        
        return self.index_image
# if __name__ == "__main__":
#     get_image_from_webcam()
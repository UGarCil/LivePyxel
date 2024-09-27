from constants import *


class VideoDeviceManager():
    def __init__(self):
        # Determine the width and height ratio of the camera
        self.webcam_idx = 0 #the initial index of the webcam
        self.read_new_VideoDevice(self.webcam_idx)
        self.get_avail_devices()
        
    def get_avail_devices(self):
        print("""      
              Finding video devices available...
      .-------------------.
     /--_--.------.------/|
     |     |__||__| [==] ||
     |     | .--. | '''' ||
     |     || () ||      ||
     |     | `--' |      |/
     `-----'------'------'  Art by Joan Stark
     """)
        available_cameras = []
        for device_index in range(4):
            cap = cv2.VideoCapture(device_index)
            if cap.isOpened():
                available_cameras.append(device_index)
                cap.release()  # Release the camera once checked
        self.avail_devices = available_cameras

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
        # self.cameraW = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        # self.cameraH = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        # self.cameraRatio = cameraH/cameraW #what proportion of the width is the height (e.g. for 1920 x 1080, it's 0.56)
        # W = 1920
        # H = 1080

    # FD. get_image_from_webcam()
    # purp. create a surface class object with the feed from the webcam
    def get_image_from_webcam(self):
        _,frame = self.cap.read()
        surface = cv2.cvtColor(frame,0)
        # surface = cv2.rotate(surface, cv2.ROTATE_90_COUNTERCLOCKWISE)
        # surface = cv2.flip(surface,0)
        surface = cv2.resize(surface, (720,480))  #HEIGHT AND WIDTH get flipped because or the counterclockwise rotation
        return surface

    def save_image(self, img, mask):
        copy_mask = mask.copy()
        copy_mask[:, :, 3] = 255
        if not os_settings["images_path"]:
            QtWidgets.QMessageBox.critical(None, "Annotation aborted!", f"A directory path couldn't determined. Please create or load a project and try again")
        else:
            uuid_ext = str(uuid.uuid4())[:8]
            image_name = "img_"+uuid_ext+".png"
            image_name = jn(os_settings["images_path"],image_name)
            mask_name = "msk_"+uuid_ext+".png"
            mask_name = jn(os_settings["masks_path"],mask_name)
            cv2.imwrite(image_name,img)
            cv2.imwrite(mask_name,copy_mask)
            display_settings["mask"] = np.zeros_like(display_settings["mask"])

# if __name__ == "__main__":
#     get_image_from_webcam()
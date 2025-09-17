'''
Receive a set of images,
generate a dataset, then load the model and predict the masks.
'''

from UNetDataset import UNetDataset
from UNetVgg19_4downsamples import UNetVgg19
import numpy as np 
from torchvision import transforms 
from PIL import Image
import torch 
import json

def categorize_mask(self, mask):
    """
    Converts the RGB values in the mask to their corresponding category indices.
    Any pixel not matching a category color is set to 0.
    """
    mask = np.array(mask)  # Convert the mask to a NumPy array
    categorized_mask = np.zeros(mask.shape[:2], dtype=np.uint8)  # Initialize the output mask

    for category in self.categories_record:
        # print(category)
        color = category["COLOR"]
        idx = category["IDX"]
        # Find pixels matching the category color
        matches = np.all(np.abs(mask - color) < 4, axis=-1)  # Allow ±10 per channel
        categorized_mask[matches] = idx
        # print(np.max(matches))

    return categorized_mask  # Return as NumPy array (H, W)
    # return Image.fromarray(categorized_mask, mode='L')


def retrieve_categories(config_file):
    '''
    Read the config file and use the labels and colors to generate a list of categories for 
    later use in pixel categorization (i.e. changing an rgb value to a numerical label)
    '''
    list_of_categories = []
    with open(config_file, 'r') as file:
        config = json.load(file)
    
    labels = config.get("labels", [])
    colors = config.get("colors", [])
    
    for idx, label in enumerate(labels):
        category = {
            "LABEL": label,
            "COLOR": tuple(colors[idx]) if idx < len(colors) else (0, 0, 0),
            "IDX": idx
        }
        list_of_categories.append(category)
    
    return list_of_categories


def make_prediction(image_path):
    # Image will be resized and transformed to tensor
    img_transform = transforms.Compose([
                transforms.Resize((512,512)),
                transforms.ToTensor()
            ])

    # We need the categorization to remap indexes to colors
    img = Image.open(image_path).convert("RGB")
    # Process image
    img = img_transform(img)  # Shape: (3, H, W)
    img = img.float().to(device)
    # Add one dimension to the image tensor to simulate batch size
    img = img.unsqueeze(0)  # Shape: (1, 3, H, W)
    
    
    # Forward pass
    with torch.no_grad():
        raw_output = model(img)  # # shape: (B, C, H, W) 
    # y_pred = model(img)  
    # Get predicted class indices (argmax over class dimension)
    pred_mask = torch.argmax(raw_output, dim=1)  # Shape: [1, 512, 512]    
    # remove batch dimension
    pred_mask = pred_mask.squeeze(0)  # Shape: [512, 512]

    return pred_mask

def map_mask_to_image(pred_mask, categories_record):
    """
    Map the predicted mask to the original image size and save it.
    """
    # Convert the predicted mask to a NumPy array
    pred_mask = pred_mask.cpu().numpy()  # Shape: (H, W)
    
    # Create a color map for visualization
    color_map = np.zeros((pred_mask.shape[0], pred_mask.shape[1], 3), dtype=np.uint8)
    # color_map = np.full((pred_mask.shape[0], pred_mask.shape[1], 3), 255, dtype=np.uint8)
    # categorized_mask = np.full(pred_mask.shape[:2], 255, dtype=np.uint8)  # 255 = unlabeled
        
    for category in categories_record:
        idx = category["IDX"] + 1  # Start from 1 to avoid 0 for unlabeled
        color = category["COLOR"]
        color_map[pred_mask == idx] = color
    
    # Convert to PIL Image and save
    pred_image = Image.fromarray(color_map, mode='RGB')
    pred_image.save("predicted_mask.png")
    print("Predicted mask saved as 'predicted_mask.png'")


if __name__ == "__main__":
    MODEL_PATH = "./trained_models/June_10_2025_EMicroorgDataset/UNET_model_VGG19UNet_84_120.pth"
    image_path = "../../../dataset_00/images/img_000178.png"
    config_file = "../../../EnvMic_June2025/config.json"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    model = UNetVgg19(in_channels=3,num_classes=10).to(device)
    model = torch.nn.DataParallel(model)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device(device)))
    model.eval()
    categories_record = retrieve_categories(config_file)

    pred_mask = make_prediction(image_path)
    
    map_mask_to_image(pred_mask, categories_record)
from torch.utils.data.dataset import Dataset
from torch.utils.data import DataLoader, random_split
from torchvision import transforms 
from PIL import Image
from os.path import join as jn
import os
import numpy as np
import json
import torch
import torch.nn.functional as F
from tqdm import tqdm
import torchvision.transforms.functional as TF
import random

# DD. UNETDATASET
# unetDataset = UNetDataset()
# interp. an object that contains a representation of the images and masks to enter the dataset
class UNetDataset(Dataset):
    def __init__(self,path_images,path_masks, config_file, augment=False, weights=None):
        self.augment = augment
        # self.root = path 
        self.imagesPath = path_images
        self.masksPath = path_masks
        self.images = sorted([jn(self.imagesPath,i) for i in os.listdir(self.imagesPath)])
        self.masks = sorted([jn(self.masksPath,i) for i in os.listdir(self.masksPath)])
        self.img_transform = transforms.Compose([
            transforms.Resize((512,512)),
            transforms.ToTensor()
        ])
        self.categories_record = self.retrieve_categories(config_file) 
        if weights is None:
            self.weights = self._calculate_class_weights()
        else:
            self.weights = torch.tensor(weights,dtype=torch.float32)
    
    def augment_image_and_mask(self, img, mask):
        # Random flip
        if random.random() > 0.5:
            img = TF.hflip(img)
            mask = TF.hflip(mask)

        if random.random() > 0.5:
            img = TF.vflip(img)
            mask = TF.vflip(mask)

        # Random exact rotation
        angle = random.choice([0, 90, 180, 270])
        img = TF.rotate(img, angle)
        mask = TF.rotate(mask, angle)

        # Optional: Stretching (random scaling along one axis)
        if random.random() > 0.5:
            scale_x = random.uniform(0.9, 1.1)
            scale_y = random.uniform(0.9, 1.1)
            img = TF.resize(img, [int(512 * scale_y), int(512 * scale_x)])
            mask = TF.resize(mask, [int(512 * scale_y), int(512 * scale_x)], interpolation=Image.NEAREST)

        return img, mask

    
    def _calculate_class_weights(self, method='balanced'):
        """
        Calculate class weights based on pixel frequency in the dataset.
        
        Args:
            method: 'balanced', 'inverse_freq', or 'inverse_sqrt'
            
        Returns:
            torch.Tensor: Class weights of shape (num_classes,)
        """
        print(self.num_classes)
        class_counts = np.zeros(self.num_classes, dtype=np.int64)
        total_pixels = 0
        
        print(f"Processing {len(self.masks)} masks for class weight calculation...")
        
        # Count pixels for each class across all masks
        for mask_path in tqdm(self.masks, desc="Analyzing masks"):
            mask_rgb = Image.open(mask_path).convert("RGB")
            mask_categorical = self.categorize_mask(mask_rgb)
            
            # Count pixels for each class
            unique_classes, counts = np.unique(mask_categorical, return_counts=True)
            
            for class_id, count in zip(unique_classes, counts):
                if 0 <= class_id < self.num_classes:
                    class_counts[class_id] += count
                    total_pixels += count
        
        # Calculate frequencies
        self.class_frequencies = class_counts / total_pixels
        
        # Calculate weights based on method
        if method == 'balanced':
            # Sklearn-style balanced weights
            weights = total_pixels / (self.num_classes * (class_counts + 1e-8))
        elif method == 'inverse_freq':
            weights = 1.0 / (self.class_frequencies + 1e-8)
        elif method == 'inverse_sqrt':
            weights = 1.0 / (np.sqrt(self.class_frequencies) + 1e-8)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Normalize weights
        weights = weights / np.mean(weights)
        

        # Print summary
        print(self.class_frequencies)
        
        return torch.tensor(weights, dtype=torch.float32)
    
    def retrieve_categories(self, config_file):
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
                "IDX": idx + 1  # Start indices from 1 for the first category leaving 0 for unlabeled
            }
            list_of_categories.append(category)
        # add a category for unlabeled pixels
        list_of_categories.insert(0, {"LABEL": "background", "COLOR": (0, 0, 0), "IDX": 0})
        self.num_classes = len(list_of_categories)
        return list_of_categories
    
    def categorize_mask(self, mask):
        """
        Converts the RGB values in the mask to their corresponding category indices.
        Any pixel not matching a category color is set to 0.
        """
        mask = np.array(mask)  # Convert the mask to a NumPy array
        categorized_mask = np.zeros(mask.shape[:2], dtype=np.uint8)  # Initialize the output mask
        # categorized_mask = np.full(mask.shape[:2], 255, dtype=np.uint8)  # 255 = unlabeled
        
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
        
    def __getitem__(self, index):
        img = Image.open(self.images[index]).convert("RGB")
        mask = Image.open(self.masks[index]).convert("RGB")

        if self.augment:
            img, mask = self.augment_image_and_mask(img, mask)

        # Resize both image and mask
        resize = transforms.Resize((512, 512))
        img = resize(img)
        mask = resize(mask)

        # Convert image to tensor
        img = transforms.ToTensor()(img)

        # Convert mask from RGB to class indices
        mask = self.categorize_mask(mask)  # NumPy array, shape: (H, W)
        mask = torch.from_numpy(mask).long()  # Tensor, shape: (H, W)

        return img, mask  # Final shapes: (3, 512, 512), (512, 512)

    def __len__(self):
        return len(self.images)
    
        
        


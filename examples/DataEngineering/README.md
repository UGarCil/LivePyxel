
# Data Engineering Scripts

This folder contains scripts for preprocessing and augmenting image datasets, typically used in segmentation and annotation workflows. **Use generate_transparencies.py** to create transparency masks or overlays from images, and afterwards **mixer.py** to combine or mix multiple images or masks.

---

## How to Run `generate_transparencies.py`

This script generates transparency masks or overlays from a set of input images. Use it for preparing datasets for segmentation or annotation tasks.

1. **Open a terminal** and navigate to this folder (`examples/DataEngineering`).
2. **Ensure your Python environment is activated** and all dependencies are installed (see project root for environment setup).
3. **Run the script** with the following command:

```powershell
python generate_transparencies.py
```

You may need to specify input/output directories or other options depending on your dataset. Refer to the script or its comments for available arguments.

---

## How to Run `mixer.py`

This script combines or mixes multiple images, masks, or data sources. Use it for data augmentation, creating composite images, or merging annotation layers.

1. **Open a terminal** and navigate to this folder (`examples/DataEngineering`).
2. **Ensure your Python environment is activated** and all dependencies are installed.
3. **Run the script** with the following command:

```powershell
python mixer.py
```

Check the script for any required arguments or configuration options. You may need to provide paths to the images or masks you wish to mix.

---

## Folder Structure

The typical folder structure for data engineering scripts is:

```
examples/DataEngineering/
├── generate_transparencies.py
├── mixer.py
├── README.md
```

---

## Additional Notes

- Both scripts are intended for preprocessing and augmenting image datasets.
- Make sure your input data is organized and accessible to the scripts.
- For more details on script functionality, refer to the comments within each Python file.

This script generates transparency masks or overlays from a set of input images. Use it for preparing datasets for segmentation or annotation tasks.

1. **Open a terminal** and navigate to this folder (`examples/DataEngineering`).
2. **Ensure your Python environment is activated** and all dependencies are installed (see project root for environment setup).
3. **Run the script** with the following command:

```powershell
python generate_transparencies.py
```

You may need to specify input/output directories or other options depending on your dataset. Refer to the script or its comments for available arguments.

---

## How to Run `mixer.py`

This script combines or mixes multiple images, masks, or data sources. Use it for data augmentation, creating composite images, or merging annotation layers.

1. **Open a terminal** and navigate to this folder (`examples/DataEngineering`).
2. **Ensure your Python environment is activated** and all dependencies are installed.
3. **Run the script** with the following command:

```powershell
python mixer.py
```

Check the script for any required arguments or configuration options. You may need to provide paths to the images or masks you wish to mix.

---

## Folder Structure

The typical folder structure for data engineering scripts is:

```
examples/DataEngineering/
├── generate_transparencies.py
├── mixer.py
├── README.md
```

---

## Additional Notes

- Both scripts are intended for preprocessing and augmenting image datasets.
- Make sure your input data is organized and accessible to the scripts.
- For more details on script functionality, refer to the comments within each Python file.
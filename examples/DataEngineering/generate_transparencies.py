import cv2
import numpy as np
import shutil
from pathlib import Path
import json

def load_config(config_path: str) -> dict:
    with open(config_path, "r") as f:
        return json.load(f)
    
def identify_class_color(msk: np.array, config_colors: list, tolerance: int = 5) -> str:
    reshaped = msk.reshape(-1, 3)
    reshaped = reshaped[np.any(reshaped != [0, 0, 0], axis=1)]
    if reshaped.size == 0:
        return None
    unique_colors = np.unique(reshaped, axis=0)
    for color in unique_colors:
        for ref_color in config_colors:
            if all(abs(int(c1) - int(c2)) <= tolerance for c1, c2 in zip(color, ref_color)):
                return f"{ref_color[0]}_{ref_color[1]}_{ref_color[2]}"
    return None

def extract_pixels_from_masks(image_dir: str, mask_dir: str, config_path: str, output_root: str = "augmented"):
    config = load_config(config_path)
    color_map = {tuple(color): label for color, label in zip(config["colors"], config["labels"])}

    image_files = sorted(Path(image_dir).glob("img_*.png"))
    for image_path in image_files:
        img_name = image_path.name
        mask_name = "msk_" + img_name[4:]
        mask_path = Path(mask_dir) / mask_name

        if not mask_path.exists():
            continue

        image = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
        mask = cv2.imread(str(mask_path), cv2.IMREAD_COLOR)
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2RGB)  # Convert for RGB matching

        class_color_str = identify_class_color(mask, config["colors"])
        if class_color_str is None:
            continue
        class_color = tuple(map(int, class_color_str.split("_")))
        label = color_map.get(class_color, None)
        if label is None:
            continue

        out_img_dir = Path(output_root) / label / "images"
        out_msk_dir = Path(output_root) / label / "masks"
        out_img_dir.mkdir(parents=True, exist_ok=True)
        out_msk_dir.mkdir(parents=True, exist_ok=True)

        match_mask = np.all(mask == class_color, axis=-1).astype(np.uint8) * 255

        if image.shape[2] == 4:
            image = image[:, :, :3]

        b, g, r = cv2.split(image)
        rgba = cv2.merge((b, g, r, match_mask))

        trimmed_name = img_name.replace("img_", "")
        cv2.imwrite(str(out_img_dir / f"img_{trimmed_name}"), rgba)
        shutil.copy(mask_path, out_msk_dir / f"msk_{trimmed_name}")

############################ USAGE ###########################
# extract_pixels_from_masks(
#     image_dir="./images",
#     mask_dir="./masks",
#     config_path="config.json",
#     output_root="augmented"
# )
##############################################################

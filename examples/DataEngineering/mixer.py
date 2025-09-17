
import cv2
import numpy as np
import random
import json
from pathlib import Path



def load_config(config_path):
    with open(config_path, "r") as f:
        config = json.load(f)
    labels = config["labels"]
    colors = config["colors"]
    # Convert each RGB color to BGR for OpenCV usage
    colors_bgr = [(c[2], c[1], c[0]) for c in colors]
    return dict(zip(labels, colors_bgr))

def mixer(samples: int = 10, config_path: str = "config.json", augmented_dir: str = "augmented", output_dir: str = "aug_dataset", background_reference: str = "background.png"):
    label_color_map = load_config(config_path)

    out_img_dir = Path(output_dir) / "images"
    out_msk_dir = Path(output_dir) / "masks"
    out_img_dir.mkdir(parents=True, exist_ok=True)
    out_msk_dir.mkdir(parents=True, exist_ok=True)

    base_bg = cv2.imread(background_reference, cv2.IMREAD_COLOR)
    height, width, _ = base_bg.shape
    class_dirs = sorted((Path(augmented_dir)).iterdir())

    for sample_idx in range(samples):
        composite_img = base_bg.copy()
        composite_mask = np.zeros((height, width, 3), dtype=np.uint8)
        n_classes_in_sample = random.randint(1, len(class_dirs))
        shuffled_idx_classes = random.sample(range(len(class_dirs)), len(class_dirs))

        for i in range(n_classes_in_sample):
            class_path = class_dirs[shuffled_idx_classes[i]]
            label = class_path.name
            color = label_color_map.get(label)
            img_dir = class_path / "images"
            msk_dir = class_path / "masks"
            all_imgs = sorted(img_dir.glob("*.png"))
            
            if not all_imgs:
                continue

            selected_img_path = random.choice(all_imgs)
            selected_name = selected_img_path.name.replace("img_", "")
            selected_msk_path = msk_dir / f"msk_{selected_name}"
            
            if not selected_msk_path.exists():
                continue

            snail_img = cv2.imread(str(selected_img_path), cv2.IMREAD_UNCHANGED)
            snail_msk = cv2.imread(str(selected_msk_path), cv2.IMREAD_COLOR)
            
            if snail_img is None or snail_img.shape[2] != 4:
                continue

            snail_h, snail_w = snail_img.shape[:2]
            max_y = height - snail_h
            max_x = width - snail_w
            if max_y <= 0 or max_x <= 0:
                top, left = 0, 0
            else:
                top = random.randint(0, max_y)
                left = random.randint(0, max_x)
            
            # Random flip
            if random.random() < 0.5:
                snail_img = cv2.flip(snail_img, 1)
                snail_msk = cv2.flip(snail_msk, 1)
            if random.random() < 0.5:
                snail_img = cv2.flip(snail_img, 0)
                snail_msk = cv2.flip(snail_msk, 0)

            # Random rotation
            angle = random.choice([0, 90, 180, 270])
            if angle != 0:
                center = (snail_img.shape[1] // 2, snail_img.shape[0] // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                snail_img = cv2.warpAffine(snail_img, M, (snail_img.shape[1], snail_img.shape[0]), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT)
                snail_msk = cv2.warpAffine(snail_msk, M, (snail_msk.shape[1], snail_msk.shape[0]), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT)

            alpha = snail_img[:, :, 3] / 255.0
            for c in range(3):
                composite_img[top:top+snail_h, left:left+snail_w, c] = (
                    (1 - alpha) * composite_img[top:top+snail_h, left:left+snail_w, c] +
                    alpha * snail_img[:, :, c]
                ).astype(np.uint8)

            mask_region = np.any(snail_msk != [0, 0, 0], axis=-1)
            for c in range(3):
                composite_mask[top:top+snail_h, left:left+snail_w, c][mask_region] = color[c]

            output_name = selected_name.replace(".png", f"_{sample_idx:05}.png")
            cv2.imwrite(str(out_img_dir / f"img_{output_name}"), composite_img)
            cv2.imwrite(str(out_msk_dir / f"msk_{output_name}"), composite_mask)

if __name__ == "__main__":
    mixer(samples=20)

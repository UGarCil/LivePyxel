# MODULES
from constants import *
from UNetDataset import UNetDataset
from UNetVgg19_4downsamples import UNetVgg19
from torch import optim
from torch.nn import DataParallel
from torch.utils.data import DataLoader
import numpy as np
from sklearn.metrics import f1_score
import matplotlib.pyplot as plt
import os
from tqdm import tqdm
import torch.nn as nn
import torch
from torch.utils.data import random_split
from os.path import join as jn 

##################### <HYPERPARAMETERS> #####################
LEARNING_RATE = 3e-4
BATCH_SIZE = 32
EPOCHS = 100
device = "cuda" if torch.cuda.is_available() else "cpu"

output_name = "output_SNAILS_trainAndVal_100e_aug"
os.makedirs(output_name, exist_ok=True)
dataset_name = "./00_snails_aug_dataset_10K"
PATH_IMAGES_TRAIN = jn(dataset_name, "images")
PATH_MASKS_TRAIN = jn(dataset_name, "masks")
CONFIG_PATH = jn(dataset_name, "config.json")
##################### </HYPERPARAMETERS> #####################


# CLEAN OLD LOGS
with open(jn(output_name, "training_loss_VGG19.txt"), "w") as file:
    file.close()
with open(jn(output_name, "validation_loss_VGG19.txt"), "w") as file:
    file.close()
with open(jn(output_name, "f1_scores_VGG19_train.txt"), "w") as file:
    file.close()
with open(jn(output_name, "f1_scores_VGG19_test.txt"), "w") as file:
    file.close()


def compute_f1_score(y_pred_logits, y_true, num_classes):
    '''Compute per-class F1 score from model logits and true labels.'''
    with torch.no_grad():
        y_pred = torch.argmax(y_pred_logits, dim=1).cpu().numpy().flatten()
        y_true = y_true.cpu().numpy().flatten()
        f1_scores = f1_score(y_true, y_pred, average=None, labels=list(range(num_classes)),zero_division=0)

        return f1_scores

############################# <DATASET> #############################

# DATASET
# Example weights (calculated from dataset) for 5 classes
# weights = torch.tensor([0.67887981, 0.09987094, 0.11088905, 0.05902655, 0.05133365],dtype=torch.float32)
# If you don't know the weights, call UNetDataset without weights and it will compute them for you

full_dataset = UNetDataset(PATH_IMAGES_TRAIN, PATH_MASKS_TRAIN, CONFIG_PATH, augment=True)
num_classes = full_dataset.num_classes # Keep a record of number of classes

train_len = int(0.9 * len(full_dataset))
val_len = len(full_dataset) - train_len
train_dataset, val_dataset = random_split(full_dataset, [train_len, val_len])
val_dataset.dataset.augment = False # Disable augmentation for validation set

train_dataloader = DataLoader(dataset=train_dataset, batch_size=BATCH_SIZE, shuffle=True)
val_dataloader = DataLoader(dataset=val_dataset, batch_size=BATCH_SIZE, shuffle=False)

############################# </DATASET> #############################
############################### <MODEL_OPTIMIZER_LOSS> #############################
model = UNetVgg19(in_channels=3, num_classes=num_classes).to(device)
for name, param in model.named_parameters():
    if "downsample" in name:
        param.requires_grad = False

total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"Total trainable parameters: {total_params}")
print(model)

if torch.cuda.device_count() > 1:
    print(f"Using {torch.cuda.device_count()} GPUs")
    model = DataParallel(model)

# OPTIMIZER & LOSS
optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=2, threshold=0.005)
criterion = nn.CrossEntropyLoss()
############################### </MODEL_OPTIMIZER_LOSS> #############################

train_loss_history = []
val_loss_history = []
train_f1_history = []
val_f1_history = []

for epoch in range(EPOCHS):
    model.train()
    train_running_loss = 0
    epoch_f1 = np.zeros(num_classes)

    for img, mask in tqdm(train_dataloader):
        img, mask = img.to(device), mask.to(device)

        y_pred = model(img)
        loss = criterion(y_pred, mask)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        train_running_loss += loss.item()
        batch_f1 = compute_f1_score(y_pred, mask, num_classes)
        epoch_f1 += batch_f1

    train_loss = train_running_loss / len(train_dataloader)
    avg_train_f1 = epoch_f1 / len(train_dataloader)
    macro_train_f1 = np.mean(avg_train_f1)

    # === Validation Loop ===
    model.eval()
    val_running_loss = 0
    val_epoch_f1 = np.zeros(num_classes)
    with torch.no_grad():
        for img, mask in val_dataloader:
            img, mask = img.to(device), mask.to(device)

            y_pred = model(img)
            val_running_loss += criterion(y_pred, mask).item()
            batch_f1 = compute_f1_score(y_pred, mask, num_classes)
            val_epoch_f1 += batch_f1

    val_loss = val_running_loss / len(val_dataloader)
    avg_val_f1 = val_epoch_f1 / len(val_dataloader)
    macro_val_f1 = np.mean(avg_val_f1)

    train_loss_history.append(train_loss)
    val_loss_history.append(val_loss)
    train_f1_history.append(avg_train_f1.tolist())
    val_f1_history.append(avg_val_f1.tolist())

    scheduler.step(train_loss)

    # Logging
    with open(jn(output_name, "training_loss_VGG19.txt"), "a") as f:
        f.write(f"Epoch {epoch+1}: Loss={train_loss:.4f}, MacroF1={macro_train_f1:.4f}\n")
    with open(jn(output_name, "validation_loss_VGG19.txt"), "a") as f:
        f.write(f"Epoch {epoch+1}: Loss={val_loss:.4f}, MacroF1={macro_val_f1:.4f}\n")
    with open(jn(output_name, "f1_scores_VGG19_train.txt"), "a") as f:
        f.write(f"{avg_train_f1.tolist()}\n")
    with open(jn(output_name, "f1_scores_VGG19_test.txt"), "a") as f:
        f.write(f"{avg_val_f1.tolist()}\n")

    print(f"Epoch {epoch+1} Train MacroF1: {macro_train_f1:.4f} | Val MacroF1: {macro_val_f1:.4f}")
    torch.save(model.state_dict(), jn(output_name, f"UNET_model_VGG19UNet_{epoch}_{EPOCHS}.pth"))


# Convert F1 scores to arrays
train_f1_history = np.array(train_f1_history)
val_f1_history = np.array(val_f1_history)


# === Helper function for F1 and Loss plotting ===
def visualize_performance(train_f1_history, val_f1_history, train_loss_history, val_loss_history, num_classes, output_name):
    import matplotlib.pyplot as plt
    # F1 Score Plot
    plt.figure(figsize=(10, 6))
    for class_idx in range(num_classes):
        plt.plot(train_f1_history[:, class_idx], label=f'Train Class {class_idx}', linestyle='--')
        plt.plot(val_f1_history[:, class_idx], label=f'Val Class {class_idx}')
    plt.title("Per-Class F1 Score over Epochs")
    plt.xlabel("Epoch")
    plt.ylabel("F1 Score")
    plt.ylim(0, 1)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{output_name}/f1_plot.png")
    plt.close()

    # Loss Plot
    plt.figure(figsize=(8, 5))
    plt.plot(train_loss_history, label='Training Loss', linestyle='--')
    plt.plot(val_loss_history, label='Validation Loss')
    plt.title("Training and Validation Loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{output_name}/loss_plot.png")
    plt.close()


visualize_performance(train_f1_history, val_f1_history, train_loss_history, val_loss_history, num_classes, output_name)

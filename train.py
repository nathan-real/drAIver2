import csv
import glob
import os
import random

import cv2
import matplotlib

matplotlib.use("Agg")  # Sauvegarde la courbe sans ouvrir de fenêtre
import matplotlib.pyplot as plt
import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler

from model import SteeringNet
from processing import process_frame

DRIVING_RUNS = "dataset/driving/run_*"
RECOVERY_RUNS = "dataset/recovery/run_*"
VAL_DRIVING_RUN = "run_20261025_152111"  # Session complète gardée pour le test
VAL_RECOVERY_EVERY = 10  # 1 clip de récupération sur 10 gardé pour le test

MODEL_PATH = "model.pth"
PLOT_PATH = "loss.png"

EPOCHS = 20
BATCH_SIZE = 128
LEARNING_RATE = 1e-3
SMOOTHING_WINDOW = 5  # Nombre d'images de la moyenne glissante (impair)
RECOVERY_SHARE = 0.25  # Part des clips de récupération dans chaque lot
SEED = 42


def smooth(values):
    # Moyenne glissante, en répétant les valeurs du bord pour garder la même longueur
    half = SMOOTHING_WINDOW // 2
    padded = np.pad(values, half, mode="edge")
    kernel = np.ones(SMOOTHING_WINDOW) / SMOOTHING_WINDOW
    return np.convolve(padded, kernel, mode="valid")


def load_run(run_dir):
    with open(os.path.join(run_dir, "driving_log.csv"), newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    images = []
    for row in rows:
        image_path = os.path.join(run_dir, row["image_path"].replace("\\", "/"))
        # Même traitement que dans main.py, puis passage au format (C, H, L) de PyTorch
        image = process_frame(cv2.imread(image_path))
        images.append(torch.from_numpy(image).permute(2, 0, 1))

    steering = smooth(np.array([float(row["steering"]) for row in rows]))
    return images, steering


def load_runs(driving_dirs, recovery_dirs):
    all_images, all_steering, all_is_recovery = [], [], []

    for run_dirs, is_recovery in ((driving_dirs, False), (recovery_dirs, True)):
        for run_dir in run_dirs:
            images, steering = load_run(run_dir)
            all_images += images
            all_steering.append(steering)
            all_is_recovery += [is_recovery] * len(images)

    return (
        torch.stack(all_images),
        torch.tensor(np.concatenate(all_steering), dtype=torch.float32),
        torch.tensor(all_is_recovery),
    )


def split_runs():
    # On sépare par session entière : deux images qui se suivent sont presque identiques
    driving = sorted(glob.glob(DRIVING_RUNS))
    recovery = sorted(glob.glob(RECOVERY_RUNS))

    val_driving = [run for run in driving if os.path.basename(run) == VAL_DRIVING_RUN]
    train_driving = [run for run in driving if run not in val_driving]
    val_recovery = recovery[::VAL_RECOVERY_EVERY]
    train_recovery = [run for run in recovery if run not in val_recovery]

    return train_driving, train_recovery, val_driving, val_recovery


def sample_weights(is_recovery):
    # Poids choisis pour que les clips pèsent RECOVERY_SHARE, malgré leur petit nombre
    weights = torch.full((len(is_recovery),), (1 - RECOVERY_SHARE) / (~is_recovery).sum())
    weights[is_recovery] = RECOVERY_SHARE / is_recovery.sum()
    return weights


class DrivingDataset(Dataset):
    def __init__(self, images, steering, flip=False):
        self.images = images
        self.steering = steering
        self.flip = flip

    def __len__(self):
        return len(self.images)

    def __getitem__(self, index):
        image, steering = self.images[index], self.steering[index]

        # Image en miroir : la direction change de signe
        if self.flip and random.random() < 0.5:
            image, steering = torch.flip(image, dims=[2]), -steering

        return image, steering


def run_train_epoch(model, loader, optimizer, device):
    model.train()
    total_loss = 0.0

    for images, steering in loader:
        images, steering = images.to(device), steering.to(device)

        optimizer.zero_grad()
        loss = torch.nn.functional.mse_loss(model(images), steering)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * len(images)

    return total_loss / len(loader.dataset)


@torch.no_grad()
def evaluate(model, images, steering, weights, device):
    # Erreur pondérée, avec le même équilibre route/récupération qu'à l'entraînement
    model.eval()
    squared_errors = []

    for start in range(0, len(images), 512):
        batch = images[start : start + 512].to(device)
        target = steering[start : start + 512].to(device)
        squared_errors.append((model(batch) - target).pow(2).cpu())

    return ((torch.cat(squared_errors) * weights).sum() / weights.sum()).item()


def save_plot(train_losses, val_losses, ymax=None):
    epochs = range(1, len(train_losses) + 1)
    plt.plot(epochs, train_losses, label="Entraînement")
    plt.plot(epochs, val_losses, label="Test")
    plt.xlabel("Epoch")
    plt.ylabel("Erreur (MSE)")
    plt.title("Courbe d'apprentissage")
    plt.ylim(0, ymax)
    plt.legend()
    plt.savefig(PLOT_PATH, dpi=150)
    plt.close()


def main():
    random.seed(SEED)
    torch.manual_seed(SEED)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")

    train_driving, train_recovery, val_driving, val_recovery = split_runs()
    if not val_driving:
        raise ValueError(f"{VAL_DRIVING_RUN} not found in {DRIVING_RUNS}")

    print("Loading images...")
    train_images, train_steering, train_is_recovery = load_runs(train_driving, train_recovery)
    val_images, val_steering, val_is_recovery = load_runs(val_driving, val_recovery)
    print(
        f"Train: {len(train_images)} images ({train_is_recovery.sum()} recovery). "
        f"Test: {len(val_images)} images ({val_is_recovery.sum()} recovery)."
    )

    train_dataset = DrivingDataset(train_images, train_steering, flip=True)
    sampler = WeightedRandomSampler(
        sample_weights(train_is_recovery), num_samples=len(train_dataset)
    )
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, sampler=sampler)
    val_weights = sample_weights(val_is_recovery)

    model = SteeringNet().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

    best_val_loss = float("inf")
    train_losses, val_losses = [], []

    for epoch in range(1, EPOCHS + 1):
        train_loss = run_train_epoch(model, train_loader, optimizer, device)
        val_loss = evaluate(model, val_images, val_steering, val_weights, device)
        train_losses.append(train_loss)
        val_losses.append(val_loss)

        message = f"Epoch {epoch:2d}/{EPOCHS} | train {train_loss:.4f} | test {val_loss:.4f}"

        # On garde uniquement le modèle qui a le meilleur score sur le test
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), MODEL_PATH)
            message += " | saved"

        print(message)

    save_plot(train_losses, val_losses)
    print(f"Best test loss: {best_val_loss:.4f}. Model: {MODEL_PATH}, curve: {PLOT_PATH}.")


if __name__ == "__main__":
    main()

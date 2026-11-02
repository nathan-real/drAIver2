import ctypes
import mss
import cv2
import numpy as np
import time
import torch
import vgamepad as vg

from model import SteeringNet
from processing import process_frame

MODEL_PATH = "model.pth"
THROTTLE = 0.4  # Accélérateur fixe : à baisser si la voiture rate les virages

# Chargement du modèle entraîné
device = "cuda" if torch.cuda.is_available() else "cpu"
model = SteeringNet().to(device)
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.eval()

gamepad = vg.VX360Gamepad()

sct = mss.mss()
monitor = sct.monitors[1]  # Même capture que recorder.py (écran entier)

TARGET_FPS = 15
FRAME_TIME = 1.0 / TARGET_FPS
TARGET_SIZE = (128, 72)

# Codes Windows des touches du clavier
KEY_ENTER = 0x0D
KEY_LEFT = 0x25
KEY_UP = 0x26
KEY_RIGHT = 0x27
KEY_DOWN = 0x28


def is_pressed(key):
    # Lit le clavier même quand la fenêtre active est celle du jeu
    return bool(ctypes.windll.user32.GetAsyncKeyState(key) & 0x8000)


def send_commands(steering, throttle, brake):
    # Simule le volant
    gamepad.left_joystick_float(x_value_float=steering, y_value_float=0.0)

    # Simule l'accélérateur
    gamepad.right_trigger_float(value_float=throttle)

    # Simule le frein
    gamepad.left_trigger_float(value_float=brake)

    # Envoie les commandes à Windows
    gamepad.update()


def manual_commands():
    # Les flèches pilotent la manette virtuelle, pour refaire le mappage dans le jeu
    steering = float(is_pressed(KEY_RIGHT)) - float(is_pressed(KEY_LEFT))
    throttle = float(is_pressed(KEY_UP))
    brake = float(is_pressed(KEY_DOWN))
    return steering, throttle, brake


def ai_commands():
    # Capture de l'écran
    screenshot = sct.grab(monitor)
    img_bgra = np.array(screenshot)

    # Processing de l'image capturée
    original_height, original_width = img_bgra.shape[:2]
    target_height = int(original_width * 9 / 16)
    crop_amount = original_height - target_height
    img_cropped_bgra = img_bgra[crop_amount:original_height, :]

    # Suppression du canal alpha
    img_bgr = cv2.cvtColor(img_cropped_bgra, cv2.COLOR_BGRA2BGR)

    # Redimensionnement de l'image
    img_final = cv2.resize(img_bgr, TARGET_SIZE, interpolation=cv2.INTER_LINEAR)

    # Application du processing (crop, YUV, normalisation)
    img_processed = process_frame(img_final)

    # Passage au format attendu par le modèle : (lot, C, H, L)
    image_tensor = torch.from_numpy(img_processed).permute(2, 0, 1).unsqueeze(0)

    # Le modèle prédit la direction, l'accélérateur reste fixe
    with torch.no_grad():
        steering = model(image_tensor.to(device)).item()

    return steering, THROTTLE, 0.0


ai_enabled = False
enter_was_pressed = False

print("Arrows: gas, brake, steering. Enter: AI on/off. Ctrl+C: quit.")

try:
    while True:
        start_time = time.perf_counter()

        # On réagit uniquement au moment de l'appui, pas tant que la touche est maintenue
        enter_pressed = is_pressed(KEY_ENTER)
        if enter_pressed and not enter_was_pressed:
            ai_enabled = not ai_enabled
            print("AI on" if ai_enabled else "AI off (arrows)")
        enter_was_pressed = enter_pressed

        commands = ai_commands() if ai_enabled else manual_commands()
        send_commands(*commands)

        # Maintain 15 FPS
        process_time = time.perf_counter() - start_time
        sleep_time = FRAME_TIME - process_time

        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            print(f"Lag detected: processing took {process_time:.3f}s")

except KeyboardInterrupt:
    print("\nStopping simulation. Releasing virtual gamepad.")
    gamepad.reset()
    gamepad.update()

import mss
import cv2
import numpy as np
import time
import vgamepad as vg
import math

from processing import process_frame

# Importer modèle ia

gamepad = vg.VX360Gamepad()

sct = mss.mss()
monitor = {"top": 100, "left": 100, "width": 1280, "height": 720}

time.sleep(3)  # 3 secondes pour aller sur le jeu

TARGET_FPS = 15
FRAME_TIME = 1.0 / TARGET_FPS
TARGET_SIZE = (128, 72)

frame_count = 0

try:
    while True:
        start_time = time.perf_counter()

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

        # implementation AI
        # image_tensor = transform_to_tensor(img_processed)
        # prediction = model(image_tensor)

        # Fausse prédictions pour tester le mouvement
        prediction = {
            "steering": math.sin(frame_count * 0.5),
            "throttle": 0.8,
            "brake": 0.0,
        }
        # Simule le volant
        gamepad.left_joystick_float(
            x_value_float=prediction["steering"], y_value_float=0.0
        )

        # Simule l'accélérateur
        gamepad.right_trigger_float(value_float=prediction["throttle"])

        # Simule le frein
        gamepad.left_trigger_float(value_float=prediction["brake"])

        # Envoie les commandes à Windows
        gamepad.update()

        frame_count += 1

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

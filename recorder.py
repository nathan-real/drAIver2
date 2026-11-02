import mss
import pygame
import time
import cv2
import csv
import numpy as np
import os
from datetime import datetime

pygame.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()

sct = mss.mss()
monitor = sct.monitors[1]

TARGET_FPS = 15
FRAME_TIME = 1.0 / TARGET_FPS
TARGET_SIZE = (128, 72)

session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
base_dir = os.path.join("dataset", f"run_{session_id}")
img_dir = os.path.join(base_dir, "img")

os.makedirs(img_dir, exist_ok=True)

csv_path = os.path.join(base_dir, "driving_log.csv")
csv_file = open(csv_path, "w", newline="")
writer = csv.writer(csv_file)
writer.writerow(["image_path", "steering", "throttle", "brake"])

frame_count = 0

print("Get ready to drive...")
for i in range(5, 0, -1):
    print(f"Starting in {i}...")
    time.sleep(1)

print(
    f"Recording in {TARGET_SIZE[0]}x{TARGET_SIZE[1]} in folder {base_dir}. Press Ctrl+C to stop."
)

try:
    while True:
        start_time = time.perf_counter()

        pygame.event.pump()
        steering = round(joystick.get_axis(0), 3)
        throttle = round((joystick.get_axis(5) + 1.0) / 2.0, 3)
        brake = round((joystick.get_axis(4) + 1.0) / 2.0, 3)

        screenshot = sct.grab(monitor)
        img_bgra = np.array(screenshot)

        original_height, original_width = img_bgra.shape[:2]
        target_height = int(original_width * 9 / 16)
        crop_amount = original_height - target_height
        img_cropped_bgra = img_bgra[crop_amount:original_height, :]

        img_bgr = cv2.cvtColor(img_cropped_bgra, cv2.COLOR_BGRA2BGR)

        img_final = cv2.resize(img_bgr, TARGET_SIZE, interpolation=cv2.INTER_LINEAR)

        img_filename = f"{frame_count:05d}.jpg"
        relative_img_path = os.path.join("img", img_filename)
        absolute_img_path = os.path.join(img_dir, img_filename)

        cv2.imwrite(absolute_img_path, img_final)
        writer.writerow([relative_img_path, steering, throttle, brake])

        frame_count += 1

        process_time = time.perf_counter() - start_time
        sleep_time = FRAME_TIME - process_time

        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            print(f"FPS drop: processing too long ({process_time:.3f}s)")

except KeyboardInterrupt:
    print(f"End of recording: {frame_count} frames saved in {base_dir}.")
    csv_file.close()
    pygame.quit()

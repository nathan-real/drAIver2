import cv2
import numpy as np


def process_frame(image):
    # Rognage : 26 pixels en haut et 19 en bas, garde toute la largeur
    img_cropped = image[26:-19, :]

    # Conversion colorimétrique de BGR (format OpenCV) vers YUV
    img_yuv = cv2.cvtColor(img_cropped, cv2.COLOR_BGR2YUV)

    # Normalisation : conversion en décimales (float32) et division par 255
    img_normalized = img_yuv.astype(np.float32) / 255.0

    return img_normalized

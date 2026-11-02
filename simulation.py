import vgamepad as vg
import time
import math

# pip install vgamepad

# Imporation du modèle

gamepad = vg.VX360Gamepad()

time.sleep(3)  # 3 secondes pour aller sur le jeu

TARGET_FPS = 15
FRAME_TIME = 1.0 / TARGET_FPS


# Fonction qui simule des touches pour tester
def get_fake_ai_prediction(frame_count):
    throttle = 0.8
    brake = 0.0
    steering = math.sin(frame_count * 0.5)
    return {"steering": steering, "throttle": throttle, "brake": brake}


frame_count = 0

try:
    while True:
        start_time = time.perf_counter()

        # On récupère les inputs
        prediction = get_fake_ai_prediction(frame_count)

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

        # Ici on fait en sorte que la boucle dur bien le temps qu'il faut (1/15)
        process_time = time.perf_counter() - start_time
        sleep_time = FRAME_TIME - process_time

        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            print(f"Lag detected: {process_time:.3f}s")

except KeyboardInterrupt:
    print("\nStopping simulation. Releasing virtual gamepad.")
    gamepad.reset()
    gamepad.update()

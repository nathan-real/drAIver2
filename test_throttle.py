import math
import time
import winsound

import vgamepad as vg

# Teste plusieurs façons d'accélérer, pour trouver celle que le jeu accepte.
# Le nombre de bips annonce le numéro du test.
TESTS = [
    ("Constant 0.5", lambda t: 0.5),
    ("Constant 0.8", lambda t: 0.8),
    ("Constant 1.0", lambda t: 1.0),
    ("Variable 0.9 to 1.0", lambda t: 0.95 + 0.05 * math.sin(t * 10)),
]
TEST_DURATION = 6
PAUSE_DURATION = 3
FRAME_TIME = 1.0 / 15

gamepad = vg.VX360Gamepad()


def release():
    gamepad.reset()
    gamepad.update()


print("Starting in 5 seconds: go to the game.")
time.sleep(5)

try:
    for number, (name, throttle) in enumerate(TESTS, start=1):
        print(f"Test {number}: {name}")
        for _ in range(number):
            winsound.Beep(1000, 150)
            time.sleep(0.1)

        start_time = time.perf_counter()
        while time.perf_counter() - start_time < TEST_DURATION:
            gamepad.right_trigger_float(
                value_float=throttle(time.perf_counter() - start_time)
            )
            gamepad.update()
            time.sleep(FRAME_TIME)

        release()
        time.sleep(PAUSE_DURATION)

except KeyboardInterrupt:
    print("\nTest stopped.")

finally:
    release()

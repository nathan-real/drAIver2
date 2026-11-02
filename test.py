import pygame
import time
import sys

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("Aucune manette détectée. Veuillez la connecter et relancer le script.")
    sys.exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()

print(f"Manette connectée : {joystick.get_name()}")
print("Test des commandes normalisées. Appuyez sur Ctrl+C pour quitter.\n")

try:
    while True:
        pygame.event.pump()

        steering = joystick.get_axis(0)
        brake = (joystick.get_axis(4) + 1.0) / 2.0
        throttle = (joystick.get_axis(5) + 1.0) / 2.0

        print(
            f"\rDirection: {steering:5.2f} | Frein: {brake:5.2f} | Accélérateur: {throttle:5.2f}    ",
            end="",
        )

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nTest terminé.")
    pygame.quit()

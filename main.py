import subprocess
import cv2
import time
import os

# color in BGR format
YELLOW = (81, 222, 249)
WHITE = (255, 255, 255)

# Define pixels to check with their expected colors
pixels_to_check = [
    (957, 671, WHITE),     # play_vid
    (2198, 662, WHITE),    # violation
    (1316, 859, YELLOW),   # OK
    (2333, 1035, YELLOW),  # review
    (833, 418, WHITE),     # reason
]

special_pixel = (957, 671)  # Play button coordinate

special_wait_seconds = 30
normal_wait_seconds = 1
tolerance = 20

DEBUG_FOLDER = os.path.join(os.getcwd(), "debug_screenshots")
os.makedirs(DEBUG_FOLDER, exist_ok=True)


def color_match(c1, c2, tol):
    return all(abs(a - b) <= tol for a, b in zip(c1, c2))

def capture_screen(filename="screen.png"):
    subprocess.run(["adb", "exec-out", "screencap", "-p"], stdout=open(filename, "wb"))

counter = 0

while True:
    capture_screen()
    img = cv2.imread("screen.png")

    if img is None:
        print("Failed to load screenshot.")
        time.sleep(normal_wait_seconds)
        continue

    tapped = False
    for x, y, expected_color in pixels_to_check:
        if y >= img.shape[0] or x >= img.shape[1]:
            print(f"Warning: Coordinate ({x},{y}) out of image bounds.")
            continue

        pixel_color = tuple(int(c) for c in img[y, x])
        print(f"Checking pixel ({x},{y}): actual={pixel_color}, expected={expected_color}")

        if color_match(pixel_color, expected_color, tolerance):
            print(f"Color matched at ({x},{y}). Tapping...")
            subprocess.run(["adb", "shell", "input", "tap", str(x), str(y)])
            tapped = True


            if (x, y) == special_pixel:
                print(f"Special pixel tapped. Waiting {special_wait_seconds} seconds.")
                time.sleep(special_wait_seconds)
            else:
                time.sleep(normal_wait_seconds)

            break  # stop checking after first tap

    if not tapped:
        print("No matching pixels found. Waiting...")
        time.sleep(normal_wait_seconds)
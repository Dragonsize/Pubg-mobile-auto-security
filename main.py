import subprocess
import cv2
import time
import os
import re

# color in BGR format
YELLOW = (81, 222, 249)
WHITE = (255, 255, 255)

# cords percentages based on 2712x1220
pixels_to_check_percentage = [
    (0.353, 0.550, WHITE),   # play_vid
    (0.810, 0.542, WHITE),   # violation
    (0.485, 0.704, YELLOW),  # OK
    (0.860, 0.848, YELLOW),  # review
    (0.307, 0.342, WHITE),   # reason
]

special_pixel_percentage = (0.353, 0.550)  # play_vid

special_wait_seconds = 30
normal_wait_seconds = 1
tolerance = 20

DEBUG_FOLDER = os.path.join(os.getcwd(), "debug_screenshots")
os.makedirs(DEBUG_FOLDER, exist_ok=True)


def color_match(c1, c2, tol):
    return all(abs(a - b) <= tol for a, b in zip(c1, c2))

def capture_screen(filename="screen.png"):
    subprocess.run(["adb", "exec-out", "screencap", "-p"], stdout=open(filename, "wb"))

def get_phone_resolution():
    try:
        result = subprocess.run(['adb', 'shell', 'wm', 'size'], capture_output=True, text=True)
        output = result.stdout.strip()
        match = re.search(r'Physical size:\s*(\d+)x(\d+)', output)
        if match:
            width = int(match.group(1))
            height = int(match.group(2))
            print(f"Phone resolution: {width}x{height}")
            return width, height
        else:
            print("Could not get resolution.")
            return None, None
    except Exception as e:
        print(f"Error: {e}")
        return None, None

# Get phone resolution
phone_width, phone_height = get_phone_resolution()
if not phone_width or not phone_height:
    raise SystemExit("Failed to get phone resolution. Exiting.")

# Calculate absolute pixel positions
pixels_to_check = [
    (int(px * phone_width), int(py * phone_height), color)
    for px, py, color in pixels_to_check_percentage
]
special_pixel = (
    int(special_pixel_percentage[0] * phone_width),
    int(special_pixel_percentage[1] * phone_height)
)

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
import subprocess
import cv2
import time
import re
import numpy as np

# Colors in BGR
YELLOW = (81, 222, 249)
WHITE = (255, 255, 255)

pixels_to_check_percentage = [
    (957 / 2712, 671 / 1220, WHITE),    # play_vid
    (2198 / 2712, 662 / 1220, WHITE),   # violation
    (1316 / 2712, 859 / 1220, YELLOW),  # OK
    (2333 / 2712, 1035 / 1220, YELLOW), # review
    (833 / 2712, 418 / 1220, WHITE),    # reason
]

special_pixel_percentage = (957 / 2712, 671 / 1220)  # play_vid

special_wait_seconds = 30
normal_wait_seconds = 1 
tolerance = 20

def color_match(c1, c2, tol):
    return all(abs(a - b) <= tol for a, b in zip(c1, c2))

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

raw_width, raw_height = get_phone_resolution()

phone_width = max(raw_width, raw_height)
phone_height = min(raw_width, raw_height)

if not phone_width or not phone_height:
    raise SystemExit("Failed to get phone resolution. Exiting.")

pixels_to_check = [
    (round(px * phone_width), round(py * phone_height), color)
    for px, py, color in pixels_to_check_percentage
]
special_pixel = (
    round(special_pixel_percentage[0] * phone_width),
    round(special_pixel_percentage[1] * phone_height)
)

def capture_screen_to_cv2():
    result = subprocess.run(["adb", "exec-out", "screencap", "-p"], stdout=subprocess.PIPE)
    img_array = np.frombuffer(result.stdout, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    return img

while True:
    img = capture_screen_to_cv2()
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
            break

    if not tapped:
        print("No matching pixels found. Waiting...")
        time.sleep(normal_wait_seconds)

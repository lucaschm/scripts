#!/usr/bin/env python3
"""
WhatsApp Screenshot Splitter
----------------------------

Purpose:
    Automatically splits long WhatsApp screenshots (e.g., 1080x5643 px)
    into smaller snippets. Large screenshots are scanned
    from top to bottom and cut wherever a WhatsApp "bubble shadow" is found.

How it works:
    - Processes all images in folder INPUT_FOLDER ("x").
    - Scans each image from top to bottom.
    - Detects the light shadow line between chat bubbles by color.
    - Shadow must match:
        * exact SHADOW_COLOR (within COLOR_TOLERANCE)
        * exact SHADOW_HEIGHT (e.g., 2-5 px)
        * at least MIN_SHADOW_WIDTH pixels wide horizontally.
    - The image is split a few pixels *after* each detected shadow.
    - Each original screenshot gets its own output folder.
    - Snippets are named sequentially (001.png, 002.png...) in
      chronological (top-to-bottom) order.
    - Any completely white tail snippet at the end is removed.

Usage:
    1. Put all WhatsApp screenshots into folder "x/".
    2. Adjust SHADOW_COLOR, SHADOW_HEIGHT, MIN_SHADOW_WIDTH, etc.
    3. Run this script.
    4. Output appears in subfolders next to each screenshot.

"""


import os
from PIL import Image
import numpy as np

# --- CONFIG (adjustable) ---
INPUT_FOLDER = "x"
SHADOW_COLOR = (240, 240, 240)      # RGB tuple for the shadow color (user-provided)
SHADOW_HEIGHT = 2                   # exact pixel height of the shadow
MIN_SHADOW_WIDTH = 100              # minimum horizontal width (in px) for a valid shadow
OFFSET_AFTER_SHADOW = 3             # pixels below the shadow to split
COLOR_TOLERANCE = 5                 # pixel-value tolerance
SKIP_AFTER_DETECT = SHADOW_HEIGHT + OFFSET_AFTER_SHADOW + 2  # how many pixels to jump after a detection
NEAR_DUPLICATE_MIN_DISTANCE = 20    # don't create splits closer than this
# -----------------------------

def matches_color_block(segment, shadow_rgb, tolerance=0, min_width=100):
    """
    segment: numpy array shape (SHADOW_HEIGHT, width, 3)
    shadow_rgb: tuple (r,g,b)
    Returns True if there exists a contiguous horizontal run of columns
    where every pixel in the vertical slice (for the SHADOW_HEIGHT rows)
    matches the shadow color within tolerance, and the run length >= min_width.
    """
    # Compute absolute difference from the target color for each pixel
    # shape -> (SHADOW_HEIGHT, width, 3)
    diff = np.abs(segment.astype(np.int16) - np.array(shadow_rgb, dtype=np.int16))

    # for each pixel check if all three channels within tolerance
    pixel_ok = np.all(diff <= tolerance, axis=2)  # shape (SHADOW_HEIGHT, width)

    # for each column, check if all rows (the SHADOW_HEIGHT) are True
    col_ok = np.all(pixel_ok, axis=0)  # shape (width,)

    # Now find runs of True values in col_ok with length >= min_width
    if not np.any(col_ok):
        return False

    # Find lengths of consecutive True segments
    # convert to int and find boundaries
    arr = col_ok.astype(np.int8)
    # pad with zeros at both ends for easy diff
    padded = np.concatenate([[0], arr, [0]])
    diffs = np.diff(padded)
    starts = np.where(diffs == 1)[0]  # indices where a run starts
    ends = np.where(diffs == -1)[0]   # indices where a run ends
    lengths = ends - starts
    # check if any run long enough
    return np.any(lengths >= min_width)

def process_image(image_path):
    img = Image.open(image_path).convert("RGB")
    arr = np.array(img)
    height, width, _ = arr.shape

    split_positions = []
    y = 0
    while y <= height - SHADOW_HEIGHT:
        segment = arr[y:y + SHADOW_HEIGHT, :, :]  # shape (SHADOW_HEIGHT, width, 3)
        if matches_color_block(segment, SHADOW_COLOR, COLOR_TOLERANCE, MIN_SHADOW_WIDTH):
            # compute split position after shadow + OFFSET_AFTER_SHADOW
            split_y = y + SHADOW_HEIGHT + OFFSET_AFTER_SHADOW
            # clamp
            split_y = min(split_y, height)
            split_positions.append(split_y)
            # skip ahead to avoid re-detecting the same shadow
            y += SKIP_AFTER_DETECT
            continue
        y += 1

    # Remove near-duplicates (if any) and ensure ascending order
    cleaned = []
    for pos in sorted(split_positions):
        if not cleaned or pos - cleaned[-1] > NEAR_DUPLICATE_MIN_DISTANCE:
            cleaned.append(pos)
    split_positions = cleaned

    # Create output folder named after the original filename (without extension)
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_dir = os.path.join(os.path.dirname(image_path), base_name)
    os.makedirs(output_dir, exist_ok=True)

    # Crop and save snippets in chronological order (top -> bottom)
    start_y = 0
    snippet_paths = []
    for split_y in split_positions + [height]:
        if split_y <= start_y:
            start_y = split_y
            continue
        snippet = img.crop((0, start_y, width, split_y))
        out_name = f"{len(snippet_paths)+1:03d}.png"
        out_path = os.path.join(output_dir, out_name)
        snippet.save(out_path)
        snippet_paths.append(out_path)
        start_y = split_y

    # --- remove completely (or almost) white snippets at the end ---
    if snippet_paths:
        last_path = snippet_paths[-1]
        last_img = Image.open(last_path).convert("RGB")
        arr = np.array(last_img, dtype=np.uint8)
        mean_brightness = np.mean(arr)

        # if mean brightness is near 255 (white) and variation low, delete it
        if mean_brightness > 250 and np.std(arr) < 2:
            os.remove(last_path)
            snippet_paths.pop()
    # -------------------------------------------------------------

    # If no snippets saved, save the full image as 001.png
    if not snippet_paths:
        out_path = os.path.join(output_dir, "001.png")
        img.save(out_path)
        snippet_paths.append(out_path)

    print(f"[+] {os.path.basename(image_path)} -> {len(snippet_paths)} snippet(s) -> {output_dir}")

def main():
    if not os.path.isdir(INPUT_FOLDER):
        print(f"ERROR: input folder '{INPUT_FOLDER}' does not exist.")
        return

    files = sorted(os.listdir(INPUT_FOLDER))
    images = [f for f in files if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    if not images:
        print(f"No images found in '{INPUT_FOLDER}'.")
        return

    for fname in images:
        image_path = os.path.join(INPUT_FOLDER, fname)
        try:
            process_image(image_path)
        except Exception as e:
            print(f"ERROR processing {fname}: {e}")

if __name__ == "__main__":
    main()

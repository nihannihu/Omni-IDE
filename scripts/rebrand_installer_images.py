import os
from PIL import Image

# Path to the source logo
source_logo = r"c:\Users\nihan\Desktop\FINAL-PROJECTS\engine\omni-ide\logo.jpeg"
output_dir = r"c:\Users\nihan\Desktop\FINAL-PROJECTS\engine\omni-ide\resources\win32"

# Inno Setup dimensions (Width, Height)
BIG_IMAGES = {
    "inno-big-100.bmp": (164, 314),
    "inno-big-125.bmp": (205, 393),
    "inno-big-150.bmp": (246, 471),
    "inno-big-175.bmp": (287, 549),
    "inno-big-200.bmp": (328, 628),
    "inno-big-225.bmp": (369, 707),
    "inno-big-250.bmp": (410, 785),
}

SMALL_IMAGES = {
    "inno-small-100.bmp": (55, 55),
    "inno-small-125.bmp": (69, 69),
    "inno-small-150.bmp": (82, 82),
    "inno-small-175.bmp": (96, 96),
    "inno-small-200.bmp": (110, 110),
    "inno-small-225.bmp": (124, 124),
    "inno-small-250.bmp": (137, 137),
}

def create_padded_image(img, target_size, background_color=(255, 255, 255)):
    """Resizes and pads the image to fit the target size while preserving aspect ratio."""
    target_w, target_h = target_size
    img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)

    # Create new background image
    new_img = Image.new("RGB", target_size, background_color)

    # Paste logo in the center (horizontally) and middle (vertically)
    # For BIG images, we usually want it slightly higher or centered
    offset_x = (target_w - img.width) // 2
    offset_y = (target_h - img.height) // 2
    new_img.paste(img, (offset_x, offset_y))

    return new_img

def main():
    if not os.path.exists(source_logo):
        print(f"Error: Could not find {source_logo}")
        return

    img = Image.open(source_logo).convert("RGB")

    print("Generating Wizard Images...")
    for filename, size in BIG_IMAGES.items():
        path = os.path.join(output_dir, filename)
        new_img = create_padded_image(img, size)
        new_img.save(path)
        print(f"  Created: {filename} ({size[0]}x{size[1]})")

    for filename, size in SMALL_IMAGES.items():
        path = os.path.join(output_dir, filename)
        new_img = create_padded_image(img, size)
        new_img.save(path)
        print(f"  Created: {filename} ({size[0]}x{size[1]})")

    print("\nSuccess! All branding bitmaps have been updated.")

if __name__ == "__main__":
    main()

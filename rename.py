import os
from pathlib import Path

# CONFIG
TARGET_CLASS = 0  # class to rename
PREFIX = "g_"

image_dirs = [
    r"C:\Users\Vijey Abinessh\OneDrive\Desktop\lake_lab_2\images\train",
    r"C:\Users\Vijey Abinessh\OneDrive\Desktop\lake_lab_2\images\val"
]

label_dirs = [
    r"C:\Users\Vijey Abinessh\OneDrive\Desktop\lake_lab_2\labels\train",
    r"C:\Users\Vijey Abinessh\OneDrive\Desktop\lake_lab_2\labels\val"
]

for img_dir, lbl_dir in zip(image_dirs, label_dirs):

    for label_file in os.listdir(lbl_dir):

        if not label_file.endswith(".txt"):
            continue

        label_path = os.path.join(lbl_dir, label_file)

        # Check if target class exists in label
        contains_class = False

        with open(label_path, "r") as f:
            for line in f:
                if line.strip():
                    cls = int(line.split()[0])
                    if cls == TARGET_CLASS:
                        contains_class = True
                        break

        if not contains_class:
            continue

        stem = Path(label_file).stem

        # Rename label
        new_label_name = PREFIX + label_file
        new_label_path = os.path.join(lbl_dir, new_label_name)

        if not os.path.exists(new_label_path):
            os.rename(label_path, new_label_path)

        # Rename corresponding image
        for ext in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
            img_path = os.path.join(img_dir, stem + ext)

            if os.path.exists(img_path):
                new_img_name = PREFIX + stem + ext
                new_img_path = os.path.join(img_dir, new_img_name)

                if not os.path.exists(new_img_path):
                    os.rename(img_path, new_img_path)

                print(f"Renamed: {stem}")
                break
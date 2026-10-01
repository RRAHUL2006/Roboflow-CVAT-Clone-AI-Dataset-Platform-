from pathlib import Path
import shutil

labels_dir = Path(r"C:\Users\Vijey Abinessh\OneDrive\Desktop\ongoing projects\robo_flow\projects\lake_monitering_system\annotations")
images_dir = Path(r"C:\Users\Vijey Abinessh\OneDrive\Desktop\video_lake\WhatsApp Video 2026-06-04 at 18.22.59 (2)_frames")
output_dir = Path(r"C:\Users\Vijey Abinessh\OneDrive\Desktop\ongoing projects\robo_flow\tr4")

output_dir.mkdir(parents=True, exist_ok=True)

copied = 0

# Build lookup using frame number
image_lookup = {}

for img in images_dir.glob("*.jpg"):
    frame_num = img.stem.split("_")[-1]  # 000000
    image_lookup[frame_num] = img

for txt_file in labels_dir.glob("*.txt"):

    frame_num = txt_file.stem.replace(".jpg", "").split("_")[-1]

    if frame_num in image_lookup:
        shutil.copy2(
            image_lookup[frame_num],
            output_dir / image_lookup[frame_num].name
        )
        copied += 1

print(f"Copied {copied} images")
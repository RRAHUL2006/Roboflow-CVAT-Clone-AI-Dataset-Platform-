import json
from pathlib import Path

json_folder = r"C:\Users\Vijey Abinessh\OneDrive\Desktop\ongoing projects\robo_flow\projects\lake_monitering_system\annotations"

for json_file in Path(json_folder).glob("*.json"):

    with open(json_file, "r") as f:
        data = json.load(f)

    txt_lines = []

    for ann in data.get("annotations", []):

        class_id = ann["class_id"]

        # Polygon
        if ann.get("type") == "polygon":

            line = [str(class_id)]

            for x, y in ann["points"]:
                line.extend([str(float(x)), str(float(y))])

            txt_lines.append(" ".join(line))

        # Rectangle
        elif ann.get("type") == "rect":

            x = float(ann["x"])
            y = float(ann["y"])
            w = float(ann["w"])
            h = float(ann["h"])

            txt_lines.append(
                f"{class_id} {x} {y} {w} {h}"
            )

    txt_file = json_file.with_suffix(".txt")

    with open(txt_file, "w") as f:
        f.write("\n".join(txt_lines))

    print(f"Converted: {json_file.name} -> {txt_file.name}")

print("Done!")
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import json
import shutil
import random
import cv2
import yaml
from flask import send_file
import base64
import numpy as np
from pathlib import Path
from tkinter import Tk
from tkinter.filedialog import askdirectory
from tkinter.filedialog import askopenfilename

app = Flask(__name__)
app.secret_key = "labeler_secret_key"

PROJECTS_DIR = "projects"
os.makedirs(PROJECTS_DIR, exist_ok=True)


def get_image_files(folder):
    exts = [".jpg", ".jpeg", ".png", ".bmp", ".webp"]
    files = []

    for f in os.listdir(folder):
        if Path(f).suffix.lower() in exts:
            files.append(f)

    return sorted(files)

@app.route("/browse_folder")
def browse_folder():

    root = Tk()

    root.withdraw()

    root.attributes(
        "-topmost",
        True
    )

    root.update()

    folder = askdirectory(
        parent=root
    )

    root.destroy()

    return jsonify({
        "folder": folder
    })

@app.route("/browse_video")
def browse_video():

    root = Tk()

    root.withdraw()

    root.attributes(
        "-topmost",
        True
    )

    root.update()

    file = askopenfilename(
        parent=root,
        filetypes=[
            (
                "Video Files",
                "*.mp4 *.avi *.mov *.mkv"
            )
        ]
    )

    root.destroy()

    return jsonify({
        "file": file
    })

@app.route("/video_file")
def video_file():

    path = request.args.get(
        "path"
    )

    return send_file(path)

@app.route(
    "/extract_video",
    methods=["POST"]
)
def extract_video():

    data = request.json

    video_path = data["video"]

    output_folder = data["output"]

    capture_fps = float(
        data["fps"]
    )

    video_name = Path(
        video_path
    ).stem

    save_folder = os.path.join(
        output_folder,
        video_name + "_frames"
    )

    os.makedirs(
        save_folder,
        exist_ok=True
    )

    cap = cv2.VideoCapture(
        video_path
    )

    video_fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    interval = max(
        1,
        int(video_fps / capture_fps)
    )

    frame_id = 0

    saved = 0

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        if frame_id % interval == 0:

            cv2.imwrite(

                os.path.join(
                    save_folder,
                    f"{video_name}_{saved:06d}.jpg"
                ),

                frame

            )

            saved += 1

        frame_id += 1

    cap.release()

    return jsonify({

        "saved": saved,

        "folder": save_folder

    })

@app.route(
    "/save_single_frame",
    methods=["POST"]
)
def save_single_frame():

    data = request.json

    image_data = data["image"]

    output_folder = data["output"]

    video_name = data["video_name"]

    save_folder = os.path.join(
        output_folder,
        video_name + "_frames"
    )

    os.makedirs(
        save_folder,
        exist_ok=True
    )

    existing = len(
        os.listdir(save_folder)
    )

    image_data = image_data.split(",")[1]

    image_bytes = base64.b64decode(
        image_data
    )

    frame_path = os.path.join(
        save_folder,
        f"{video_name}_{existing:06d}.jpg"
    )

    with open(frame_path, "wb") as f:
        f.write(image_bytes)

    return jsonify({
        "saved": existing + 1
    })

@app.route("/")
def index():

    projects = []

    for project_name in os.listdir(PROJECTS_DIR):

        project_path = os.path.join(
            PROJECTS_DIR,
            project_name
        )

        project_file = os.path.join(
            project_path,
            "project.json"
        )

        if os.path.exists(project_file):

            with open(project_file) as f:
                project = json.load(f)
            old_total = len(project["images"])

            annotation_dir = os.path.join(
                project_path,
                "annotations"
            )

            completed = len([
                x for x in os.listdir(annotation_dir)
                if x.endswith(".json")
            ])

            project["completed"] = completed
            project["total"] = len(project["images"])

            projects.append(project)

    return render_template(
        "index.html",
        projects=projects
    )

@app.route("/add_folder", methods=["POST"])
def add_folder():

    project_name = session["project"]

    data = request.json

    folder = data["folder"]

    project_path = os.path.join(
        PROJECTS_DIR,
        project_name
    )

    project_file = os.path.join(
        project_path,
        "project.json"
    )

    with open(project_file) as f:
        project = json.load(f)
    old_total = len(project["images"])
    if "image_folders" not in project:

        project["image_folders"] = [
            project["image_folder"]
        ]

    project["image_folders"].append(folder)

    new_images = get_image_files(folder)

    for img in new_images:

        image_info = {
            "folder": folder,
            "file": img
        }

        project["images"].append(image_info)
    if project["current_index"] >= old_total:
        project["current_index"] = old_total
    with open(project_file, "w") as f:
        json.dump(project, f, indent=4)

    return jsonify({
        "status":"ok"
    })

@app.route(
    "/add_folder_to_project",
    methods=["POST"]
)
def add_folder_to_project():

    data = request.json

    project_name = data["project"]
    folder = data["folder"]

    project_path = os.path.join(
        PROJECTS_DIR,
        project_name
    )

    project_file = os.path.join(
        project_path,
        "project.json"
    )

    with open(project_file) as f:
        project = json.load(f)

    if (
        len(project["images"]) > 0
        and
        isinstance(project["images"][0], str)
    ):

        converted = []

        for img in project["images"]:

            converted.append({
                "folder": project["image_folder"],
                "file": img
            })

        project["images"] = converted

    old_total = len(project["images"])

    existing = set()

    for img in project["images"]:

        existing.add(
            (
                img["folder"],
                img["file"]
            )
        )

    
    for img in get_image_files(folder):

        if (folder, img) not in existing:

            project["images"].append({
                "folder": folder,
                "file": img
            })
    if project["current_index"] >= old_total:
        project["current_index"] = old_total
    with open(project_file, "w") as f:
        json.dump(project, f, indent=4)

    return jsonify({
        "status":"ok"
    })

@app.route("/delete_project/<name>")
def delete_project(name):

    project_path = os.path.join(
        PROJECTS_DIR,
        name
    )

    shutil.rmtree(
        project_path,
        ignore_errors=True
    )

    return redirect("/")

@app.route("/open_project/<name>")
def open_project(name):

    session["project"] = name

    return redirect("/annotate")

@app.route("/video_extractor")
def video_extractor():

    return render_template(
        "video_extractor.html"
    )


@app.route("/create_project", methods=["POST"])
def create_project():

    project_name = request.form["project_name"]

    classes = [
        x.strip()
        for x in request.form["classes"].split(",")
        if x.strip()
    ]

    image_folder = request.form["image_folder"]
    output_folder = request.form["output_folder"]

    train_pct = int(request.form["train_pct"])
    val_pct = int(request.form["val_pct"])
    export_format = request.form[
    "export_format"
]
    project_path = os.path.join(PROJECTS_DIR, project_name)
    annotations_path = os.path.join(project_path, "annotations")

    os.makedirs(project_path, exist_ok=True)
    os.makedirs(annotations_path, exist_ok=True)

    images = []

    for img in get_image_files(image_folder):

        images.append({
            "folder": image_folder,
            "file": img
        })

    project_data = {
        "name": project_name,
        "classes": classes,
        "image_folder": image_folder,
        "output_folder": output_folder,
        "export_format":
    export_format,
        "train_pct": train_pct,
        "val_pct": val_pct,
        "images": images,
        "current_index": 0
    }

    with open(
        os.path.join(project_path, "project.json"),
        "w"
    ) as f:
        json.dump(project_data, f, indent=4)

    session["project"] = project_name

    return redirect("/annotate")


@app.route("/annotate")
def annotate():

    project_name = session.get("project")

    if not project_name:
        return redirect("/")

    project_path = os.path.join(
        PROJECTS_DIR,
        project_name
    )

    with open(
        os.path.join(project_path, "project.json")
    ) as f:
        project = json.load(f)

    annotations_dir = os.path.join(
        project_path,
        "annotations"
    )

    completed = len([
        x for x in os.listdir(annotations_dir)
        if x.endswith(".json")
    ])

    idx = project["current_index"]
    print("=" * 50)
    print("PROJECT:", project_name)
    print("CURRENT INDEX:", idx)
    print("TOTAL IMAGES:", len(project["images"]))
    print("=" * 50)

    if idx >= len(project["images"]):
        return render_template(
            "annotate.html",
            completed=True
        )

    image_data = project["images"][idx]
    image_name = image_data["file"]

    return render_template(
        "annotate.html",
        completed=False,
        image_name=image_name,
        image_index=idx + 1,
        total_images=len(project["images"]),
        classes=project["classes"]
    )


@app.route("/image")
def serve_image():

    project_name = session["project"]

    project_path = os.path.join(
        PROJECTS_DIR,
        project_name
    )

    with open(
        os.path.join(project_path, "project.json")
    ) as f:
        project = json.load(f)

    idx = project["current_index"]

    image_data = project["images"][idx]

    image_path = os.path.join(
        image_data["folder"],
        image_data["file"]
    )

    from flask import send_file
    return send_file(image_path)


@app.route("/save_annotation", methods=["POST"])
def save_annotation():

    data = request.json

    project_name = session["project"]

    project_path = os.path.join(
        PROJECTS_DIR,
        project_name
    )

    annotations_dir = os.path.join(
        project_path,
        "annotations"
    )

    image_name = data["image"]

    with open(
        os.path.join(
            annotations_dir,
            image_name + ".json"
        ),
        "w"
    ) as f:
        json.dump(data, f, indent=4)

    return jsonify({"status": "ok"})


@app.route("/next_image", methods=["POST"])
def next_image():

    project_name = session["project"]

    project_path = os.path.join(
        PROJECTS_DIR,
        project_name
    )

    project_file = os.path.join(
        project_path,
        "project.json"
    )

    with open(project_file) as f:
        project = json.load(f)
    project["current_index"] += 1
    
    with open(project_file, "w") as f:
        json.dump(project, f, indent=4)

    return jsonify({"status": "ok"})

def export_yolo(
    project,
    project_path,
    export_format
):
    dataset_root = project["output_folder"]

    images_train = os.path.join(
        dataset_root,
        "images",
        "train"
    )

    images_val = os.path.join(
        dataset_root,
        "images",
        "val"
    )

    labels_train = os.path.join(
        dataset_root,
        "labels",
        "train"
    )

    labels_val = os.path.join(
        dataset_root,
        "labels",
        "val"
    )

    for p in [
        images_train,
        images_val,
        labels_train,
        labels_val
    ]:
        os.makedirs(p, exist_ok=True)

    annotated = []

    annotations_dir = os.path.join(
        project_path,
        "annotations"
    )

    for f in os.listdir(annotations_dir):
        if f.endswith(".json"):
            annotated.append(f)

    random.shuffle(annotated)

    split = int(
        len(annotated)
        * project["train_pct"]
        / 100
    )

    train_files = annotated[:split]
    val_files = annotated[split:]

    for group, img_dest, lbl_dest in [
        (train_files, images_train, labels_train),
        (val_files, images_val, labels_val)
    ]:

        for ann_file in group:

            with open(
                os.path.join(
                    annotations_dir,
                    ann_file
                )
            ) as f:
                ann = json.load(f)

            image_name = ann["image"]

            src_img = None

            for img in project["images"]:

                if img["file"] == image_name:

                    src_img = os.path.join(
                        img["folder"],
                        img["file"]
                    )

                    break

            if not src_img:
                continue

            shutil.copy2(
                src_img,
                os.path.join(
                    img_dest,
                    image_name
                )
            )

            txt_name = (
                Path(image_name).stem
                + ".txt"
            )

            with open(
                os.path.join(
                    lbl_dest,
                    txt_name
                ),
                "w"
            ) as label_file:

                for box in ann["annotations"]:

                    box_type = box.get(
                        "type",
                        "rect"
                    )
                    if (
                        export_format == "yolo_det"
                        and
                        box_type != "rect"
                    ):
                        continue
                    if box_type == "rect":

                        label_file.write(
                            f"{box['class_id']} "
                            f"{box['x']} "
                            f"{box['y']} "
                            f"{box['w']} "
                            f"{box['h']}\n"
                        )

                    elif box_type == "polygon":

                        line = f"{box['class_id']} "

                        for point in box["points"]:

                            line += (
                                f"{point[0]} "
                                f"{point[1]} "
                            )

                        label_file.write(
                            line.strip() + "\n"
                        )

                    
    yaml_data = {
    "path": dataset_root,
    "train": "images/train",
    "val": "images/val",
    "names": {
        i: c
        for i, c
        in enumerate(project["classes"])
    }
}
    with open(
        os.path.join(
            dataset_root,
            "data.yaml"
        ),
        "w"
    ) as f:
        yaml.dump(yaml_data, f)

    return project["output_folder"]
    # move your current finalize export code here
    
def export_coco(
    project,
    project_path,
    segmentation=False
):

    annotations_dir = os.path.join(
        project_path,
        "annotations"
    )

    dataset_root = project[
        "output_folder"
    ]

    coco = {

        "images": [],
        "annotations": [],
        "categories": []

    }

    for i, cls in enumerate(
        project["classes"]
    ):

        coco["categories"].append({

            "id": i,

            "name": cls

        })

    image_id = 1
    ann_id = 1

    for ann_file in os.listdir(
        annotations_dir
    ):

        if not ann_file.endswith(
            ".json"
        ):
            continue

        with open(
            os.path.join(
                annotations_dir,
                ann_file
            )
        ) as f:

            ann = json.load(f)

        image_name = ann["image"]

        img_path = None

        for img in project["images"]:

            if img["file"] == image_name:

                img_path = os.path.join(
                    img["folder"],
                    img["file"]
                )

                break

        if not img_path:
            continue

        img_cv = cv2.imread(
            img_path
        )

        h, w = img_cv.shape[:2]

        coco["images"].append({

            "id": image_id,

            "file_name":
                image_name,

            "width": w,

            "height": h

        })

        for box in ann["annotations"]:

            box_type = box.get(
                "type",
                "rect"
            )

            if box_type == "rect":

                bw = float(box["w"]) * w
                bh = float(box["h"]) * h

                bx = (
                    float(box["x"]) * w
                ) - bw/2

                by = (
                    float(box["y"]) * h
                ) - bh/2

                coco["annotations"].append({

                    "id": ann_id,

                    "image_id":
                        image_id,

                    "category_id":
                        box["class_id"],

                    "bbox": [
                        bx,
                        by,
                        bw,
                        bh
                    ],

                    "area":
                        bw * bh,

                    "iscrowd": 0

                })

                ann_id += 1

            elif (
                segmentation
                and
                box_type == "polygon"
            ):

                seg = []

                for p in box["points"]:

                    seg.extend([

                        float(p[0]) * w,

                        float(p[1]) * h

                    ])

                coco["annotations"].append({

                    "id": ann_id,

                    "image_id":
                        image_id,

                    "category_id":
                        box["class_id"],

                    "segmentation":
                        [seg],

                    "bbox":[0,0,0,0],

                    "area":0,

                    "iscrowd":0

                })

                ann_id += 1

        image_id += 1

    with open(

        os.path.join(
            dataset_root,
            "annotations.json"
        ),

        "w"

    ) as f:

        json.dump(
            coco,
            f,
            indent=4
        )

    return dataset_root

@app.route("/finalize")
def finalize():

    project_name = session["project"]

    project_path = os.path.join(
        PROJECTS_DIR,
        project_name
    )

    with open(
        os.path.join(
            project_path,
            "project.json"
        )
    ) as f:

        project = json.load(f)

    export_format = project.get(
        "export_format",
        "yolo_det"
    )

    if export_format == "yolo_det":

        dataset_root = export_yolo(
            project,
            project_path,
            "yolo_det"
        )

    elif export_format == "yolo_seg":

        dataset_root = export_yolo(
            project,
            project_path,
            "yolo_seg"
        )

    elif export_format == "coco_det":

        dataset_root = export_coco(
            project,
            project_path,
            False
        )

    elif export_format == "coco_seg":

        dataset_root = export_coco(
            project,
            project_path,
            True
        )

    return render_template(
        "export_success.html",
        dataset_path=dataset_root,
        export_format=export_format
    )

if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )
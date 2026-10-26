import os
import io
import base64
import threading

import cv2
import numpy as np
import torch

from flask import Flask, render_template, request
from PIL import Image
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

# Load the AI depth-estimation model once.
MODEL = None
TRANSFORM = None
MODEL_LOCK = threading.Lock()


def load_model():
    global MODEL, TRANSFORM

    if MODEL is None:
        with MODEL_LOCK:
            if MODEL is None:
                model_type = "MiDaS_small"
                MODEL = torch.hub.load(
                    "intel-isl/MiDaS",
                    model_type
                )
                MODEL.eval()

                transforms = torch.hub.load(
                    "intel-isl/MiDaS",
                    "transforms"
                )
                TRANSFORM = transforms.small_transform

    return MODEL, TRANSFORM


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def create_depth_map(image):
    model, transform = load_model()

    rgb = np.array(image.convert("RGB"))
    input_batch = transform(rgb)

    with torch.no_grad():
        prediction = model(input_batch)

        prediction = torch.nn.functional.interpolate(
            prediction.unsqueeze(1),
            size=rgb.shape[:2],
            mode="bicubic",
            align_corners=False
        ).squeeze()

    depth = prediction.cpu().numpy()
    depth = cv2.normalize(
        depth,
        None,
        0,
        255,
        cv2.NORM_MINMAX
    )

    return depth.astype(np.uint8)


def create_anaglyph(image, depth):
    rgb = np.array(image.convert("RGB"))

    # Keep image dimensions manageable.
    h, w = rgb.shape[:2]
    max_side = 1000

    if max(h, w) > max_side:
        scale = max_side / max(h, w)
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))

        rgb = cv2.resize(rgb, (new_w, new_h))
        depth = cv2.resize(depth, (new_w, new_h))

    h, w = rgb.shape[:2]

    # Estimate small depth-dependent horizontal shifts.
    depth_float = depth.astype(np.float32) / 255.0
    shift = (depth_float - 0.5) * 12.0

    map_x = np.tile(
        np.arange(w, dtype=np.float32),
        (h, 1)
    )

    map_y = np.tile(
        np.arange(h, dtype=np.float32).reshape(-1, 1),
        (1, w)
    )

    left_map = map_x - shift
    right_map = map_x + shift

    left = cv2.remap(
        rgb,
        left_map,
        map_y,
        cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT
    )

    right = cv2.remap(
        rgb,
        right_map,
        map_y,
        cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT
    )

    # Red channel for left eye; cyan channels for right eye.
    output = np.zeros_like(rgb)
    output[:, :, 0] = left[:, :, 0]
    output[:, :, 1] = right[:, :, 1]
    output[:, :, 2] = right[:, :, 2]

    return Image.fromarray(output)


def image_to_data_url(image):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    encoded = base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")

    return "data:image/png;base64," + encoded


@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    error = None

    if request.method == "POST":
        file = request.files.get("photo")

        if not file or not file.filename:
            error = "Please select a photo first."

        elif not allowed_file(file.filename):
            error = "Please upload a JPG, PNG, JPEG, or WEBP image."

        else:
            try:
                image = Image.open(file.stream).convert("RGB")

                if image.width * image.height > 20_000_000:
                    raise ValueError(
                        "Image is too large. Please use a smaller photo."
                    )

                depth = create_depth_map(image)
                converted = create_anaglyph(image, depth)

                result = image_to_data_url(converted)

            except Exception as exc:
                app.logger.exception("Photo conversion failed")
                error = (
                    "Conversion failed. Check the Render logs "
                    "for the exact error. "
                    + str(exc)[:250]
                )

    return render_template(
        "index.html",
        result=result,
        error=error
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

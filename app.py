import os
import io
import base64
import logging

import cv2
import numpy as np
import torch

from flask import Flask, render_template, request
from PIL import Image
from transformers import pipeline

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

logging.basicConfig(level=logging.INFO)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

DEPTH_PIPELINE = None


def load_model():
    global DEPTH_PIPELINE

    if DEPTH_PIPELINE is None:
        logging.info("Loading depth estimation model...")

        DEPTH_PIPELINE = pipeline(
            task="depth-estimation",
            model="Intel/dpt-hybrid-midas",
            device=-1
        )

        logging.info("Depth estimation model loaded.")

    return DEPTH_PIPELINE


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def image_to_data_url(image):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return "data:image/png;base64," + encoded


def create_3d_style_image(image, depth):
    rgb = np.array(image.convert("RGB"))

    height, width = rgb.shape[:2]
    max_dimension = 1000

    if max(height, width) > max_dimension:
        scale = max_dimension / max(height, width)
        new_width = max(1, int(width * scale))
        new_height = max(1, int(height * scale))

        rgb = cv2.resize(
            rgb, (new_width, new_height),
            interpolation=cv2.INTER_AREA
        )

        depth = cv2.resize(
            depth, (new_width, new_height),
            interpolation=cv2.INTER_CUBIC
        )

    height, width = rgb.shape[:2]

    depth = cv2.normalize(
        depth.astype(np.float32),
        None,
        0,
        255,
        cv2.NORM_MINMAX
    )

    depth = cv2.GaussianBlur(depth, (5, 5), 0)
    depth_float = depth / 255.0

    # Small depth-dependent displacement.
    displacement = (depth_float - 0.5) * 10.0

    map_x = np.tile(
        np.arange(width, dtype=np.float32),
        (height, 1)
    )

    map_y = np.tile(
        np.arange(height, dtype=np.float32).reshape(-1, 1),
        (1, width)
    )

    left = cv2.remap(
        rgb,
        map_x - displacement,
        map_y,
        cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT
    )

    right = cv2.remap(
        rgb,
        map_x + displacement,
        map_y,
        cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT
    )

    # Red/cyan anaglyph image for 3D glasses.
    output = np.zeros_like(rgb)
    output[:, :, 0] = left[:, :, 0]
    output[:, :, 1] = right[:, :, 1]
    output[:, :, 2] = right[:, :, 2]

    return Image.fromarray(output)


@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    error = None

    if request.method == "POST":
        uploaded_file = request.files.get("photo")

        if uploaded_file is None or not uploaded_file.filename:
            error = "Please select a photo first."

        elif not allowed_file(uploaded_file.filename):
            error = "Please upload a JPG, JPEG, PNG, or WEBP image."

        else:
            try:
                image = Image.open(uploaded_file.stream).convert("RGB")

                if image.width * image.height > 20000000:
                    raise ValueError(
                        "Image is too large. Please use a smaller photo."
                    )

                depth_model = load_model()

                prediction = depth_model(image)
                depth_image = prediction["depth"]

                depth_array = np.array(depth_image.convert("L"))

                converted_image = create_3d_style_image(
                    image,
                    depth_array
                )

                result = image_to_data_url(converted_image)

            except Exception:
                logging.exception("Photo conversion failed")
                error = (
                    "Photo conversion failed. Check Render logs "
                    "for the underlying model or memory error."
                )

    return render_template(
        "index.html",
        result=result,
        error=error
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)

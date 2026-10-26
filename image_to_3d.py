"""
Single image -> depth map -> 3D point cloud + mesh.

Install:
    pip install torch transformers pillow numpy open3d

Usage:
    python image_to_3d.py input.jpg
Outputs:
    depth.png, output_pointcloud.ply, output_mesh.ply
"""
import sys
import numpy as np
from PIL import Image
from transformers import pipeline
import open3d as o3d


def estimate_depth(image: Image.Image) -> np.ndarray:
    pipe = pipeline(
        task="depth-estimation",
        model="depth-anything/Depth-Anything-V2-Small-hf",
    )
    depth = np.array(pipe(image)["depth"], dtype=np.float32)
    depth = (depth - depth.min()) / (depth.max() - depth.min() + 1e-8)
    return depth  # 0..1, larger = closer


def build_3d(image: Image.Image, depth: np.ndarray, depth_scale: float = 0.5):
    w, h = image.size
    color = o3d.geometry.Image(np.array(image.convert("RGB")))
    # Convert "closer = larger" into a z distance, then scale it
    z = (1.0 - depth) * depth_scale + 0.1
    depth_o3d = o3d.geometry.Image(z.astype(np.float32))

    rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(
        color, depth_o3d, depth_scale=1.0, depth_trunc=10.0,
        convert_rgb_to_intensity=False,
    )

    # Approximate pinhole camera (focal length ~ image width)
    f = w
    intrinsic = o3d.camera.PinholeCameraIntrinsic(w, h, f, f, w / 2, h / 2)

    pcd = o3d.geometry.PointCloud.create_from_rgbd_image(rgbd, intrinsic)
    pcd.transform([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])
    pcd.estimate_normals()

    # Poisson surface reconstruction -> mesh
    mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
        pcd, depth=9
    )
    d = np.asarray(densities)
    mesh.remove_vertices_by_mask(d < np.quantile(d, 0.05))
    return pcd, mesh


def main(path: str):
    image = Image.open(path).convert("RGB")
    # Keep it reasonably sized for speed
    image.thumbnail((768, 768))

    depth = estimate_depth(image)
    Image.fromarray((depth * 255).astype(np.uint8)).save("depth.png")

    pcd, mesh = build_3d(image, depth)
    o3d.io.write_point_cloud("output_pointcloud.ply", pcd)
    o3d.io.write_triangle_mesh("output_mesh.ply", mesh)

    # Interactive viewer (comment out on headless machines)
    o3d.visualization.draw_geometries([pcd])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python image_to_3d.py input.jpg")
        sys.exit(1)
    main(sys.argv[1])

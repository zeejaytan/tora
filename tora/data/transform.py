import logging
from typing import Tuple
import os

import numpy as np
import trimesh
from scipy.spatial.transform import Rotation

logger = logging.getLogger("Data")
trimesh.util.log.setLevel(logging.ERROR)

if os.environ.get("USE_PCU", "0") == "1":
    try:
        import point_cloud_utils as pcu
        use_pcu = True
        logger.info("Using point_cloud_utils for point sampling.")
    except ImportError:
        logger.warning("point_cloud_utils not found, using trimesh.sample instead.")
        use_pcu = False
else:
    logger.info("Using trimesh.sample for point sampling.")
    use_pcu = False


def sample_points_poisson(mesh: trimesh.Trimesh, count: int, seed: int | None = None) -> Tuple[np.ndarray, np.ndarray]:
    """Sample points using Poisson disk sampling. seed=None draws as before; an int fixes the
    points (paired presentations, dataset.py presentation_seed). point_cloud_utils is unseeded,
    so a seed with USE_PCU=1 is refused rather than silently ignored."""
    if use_pcu:
        if seed is not None:
            raise ValueError("presentation_seed with USE_PCU=1: point_cloud_utils cannot be seeded here")
        v = mesh.vertices
        f = mesh.faces
        idx, bc = pcu.sample_mesh_poisson_disk(v, f, num_samples=count)
        pts = pcu.interpolate_barycentric_coords(f, idx, bc, v)
    else:
        if seed is None:
            pts, idx = trimesh.sample.sample_surface_even(mesh, count=count)
        else:
            pts, idx = trimesh.sample.sample_surface_even(mesh, count=count, seed=seed)
    return pts, idx


def center_pcd(pcd: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Center point cloud at origin."""
    center = np.mean(pcd, axis=0)
    pcd = pcd - center
    return pcd, center


def rotate_pcd(pcd: np.ndarray, normals: np.ndarray = None, random_state=None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Randomly rotate point cloud and normals. random_state=None draws as before; a
    numpy RandomState fixes the turn (paired presentations, dataset.py presentation_seed)."""
    rot = Rotation.random() if random_state is None else Rotation.random(random_state=random_state)
    pcd = rot.apply(pcd)

    if normals is not None:
        normals = rot.apply(normals)

    rot_inv = rot.inv()
    return pcd, normals, rot_inv.as_matrix()


def pad_data(input_data: np.ndarray, max_parts: int) -> np.ndarray:
    """Pad zeros to data of shape (p, ...) to (max_parts, ...)"""
    d = np.array(input_data)
    pad_shape = (max_parts,) + tuple(d.shape[1:])
    pad_data = np.zeros(pad_shape, dtype=np.float32)
    pad_data[: d.shape[0]] = d
    return pad_data

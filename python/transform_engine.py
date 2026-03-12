"""
transform_engine.py — Python Image Transformation Engine

Applies 3×3 matrix transformations to images using OpenCV and NumPy.
Supports affine and perspective warps with configurable interpolation.
"""

import numpy as np
import cv2
from typing import Tuple, Optional
from python.matrix_engine import identity, determinant, is_affine, invert


def apply_transform(
    image: np.ndarray,
    matrix: np.ndarray,
    interpolation: str = 'bilinear',
    border_mode: str = 'constant',
    border_value: Tuple = (0, 0, 0, 0),
    output_size: Optional[Tuple[int, int]] = None
) -> np.ndarray:
    """
    Apply a 3×3 transformation matrix to an image.

    Args:
        image: Input image (H×W×C NumPy array).
        matrix: 3×3 transformation matrix.
        interpolation: 'nearest', 'bilinear', or 'cubic'.
        border_mode: 'constant', 'reflect', 'wrap', or 'replicate'.
        border_value: Fill color for out-of-bounds pixels.
        output_size: (width, height) of output. Defaults to input size.

    Returns:
        Transformed image as NumPy array.
    """
    h, w = image.shape[:2]
    out_w, out_h = output_size or (w, h)

    interp_flag = _get_interpolation_flag(interpolation)
    border_flag = _get_border_flag(border_mode)

    if is_affine(matrix):
        affine_2x3 = matrix[:2, :].astype(np.float64)
        result = cv2.warpAffine(
            image, affine_2x3, (out_w, out_h),
            flags=interp_flag,
            borderMode=border_flag,
            borderValue=border_value
        )
    else:
        result = cv2.warpPerspective(
            image, matrix.astype(np.float64), (out_w, out_h),
            flags=interp_flag,
            borderMode=border_flag,
            borderValue=border_value
        )

    return result


def apply_transform_manual(
    image: np.ndarray,
    matrix: np.ndarray,
    interpolation: str = 'bilinear'
) -> np.ndarray:
    """
    Apply transformation using manual per-pixel inverse mapping.
    This is the pure NumPy implementation (slower but educational).
    Demonstrates the same algorithm as transform.js.
    """
    h, w = image.shape[:2]
    channels = image.shape[2] if image.ndim == 3 else 1
    inv = invert(matrix)
    if inv is None:
        return np.zeros_like(image)

    # Create output coordinate grid
    ys, xs = np.mgrid[0:h, 0:w]
    ones = np.ones_like(xs, dtype=np.float64)
    coords = np.stack([xs.ravel(), ys.ravel(), ones.ravel()], axis=0)  # 3 × (H*W)

    # Inverse map all output coordinates to source coordinates
    src_coords = inv @ coords  # 3 × (H*W)

    # Perspective division
    w_vals = src_coords[2, :]
    valid = np.abs(w_vals) > 1e-10
    src_x = np.zeros_like(w_vals)
    src_y = np.zeros_like(w_vals)
    src_x[valid] = src_coords[0, valid] / w_vals[valid]
    src_y[valid] = src_coords[1, valid] / w_vals[valid]

    if interpolation == 'nearest':
        result = _sample_nearest(image, src_x, src_y, w, h)
    else:
        result = _sample_bilinear(image, src_x, src_y, w, h)

    return result.reshape(h, w, channels) if channels > 1 else result.reshape(h, w)


def compute_bounding_box(matrix: np.ndarray, w: int, h: int) -> Tuple[int, int, int, int]:
    """
    Compute the bounding box of the transformed image.
    Returns (min_x, min_y, width, height).
    """
    corners = np.array([
        [0, 0, 1],
        [w, 0, 1],
        [0, h, 1],
        [w, h, 1]
    ], dtype=np.float64).T  # 3×4

    transformed = matrix @ corners  # 3×4

    # Perspective division
    tx = transformed[0] / transformed[2]
    ty = transformed[1] / transformed[2]

    min_x = int(np.floor(tx.min()))
    min_y = int(np.floor(ty.min()))
    max_x = int(np.ceil(tx.max()))
    max_y = int(np.ceil(ty.max()))

    return (min_x, min_y, max_x - min_x, max_y - min_y)


# ===== Preset Transform Builders =====

def rotation_matrix(degrees: float, center: Optional[Tuple[float, float]] = None,
                     image_size: Optional[Tuple[int, int]] = None) -> np.ndarray:
    """Build a rotation matrix. Rotates around center if provided."""
    if center is None and image_size is not None:
        center = (image_size[0] / 2, image_size[1] / 2)
    if center is not None:
        return cv2.getRotationMatrix2D(center, degrees, 1.0).astype(np.float64)
    rad = np.radians(degrees)
    c, s = np.cos(rad), np.sin(rad)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=np.float64)


def scale_matrix(sx: float, sy: float, center: Optional[Tuple[float, float]] = None) -> np.ndarray:
    """Build a scaling matrix. Scales around center if provided."""
    m = np.array([[sx, 0, 0], [0, sy, 0], [0, 0, 1]], dtype=np.float64)
    if center:
        cx, cy = center
        m[0, 2] = cx - sx * cx
        m[1, 2] = cy - sy * cy
    return m


def translation_matrix(tx: float, ty: float) -> np.ndarray:
    """Build a translation matrix."""
    return np.array([[1, 0, tx], [0, 1, ty], [0, 0, 1]], dtype=np.float64)


def shear_matrix(kx: float = 0, ky: float = 0) -> np.ndarray:
    """Build a shear matrix."""
    return np.array([[1, kx, 0], [ky, 1, 0], [0, 0, 1]], dtype=np.float64)


def reflection_matrix(axis: str, size: int) -> np.ndarray:
    """Build a reflection matrix. axis='x' for horizontal, 'y' for vertical."""
    if axis == 'x':
        return np.array([[-1, 0, size], [0, 1, 0], [0, 0, 1]], dtype=np.float64)
    else:
        return np.array([[1, 0, 0], [0, -1, size], [0, 0, 1]], dtype=np.float64)


def perspective_matrix(g: float = 0, h: float = 0) -> np.ndarray:
    """Build a perspective matrix with coefficients g, h."""
    return np.array([[1, 0, 0], [0, 1, 0], [g, h, 1]], dtype=np.float64)


# ===== Internal Sampling =====

def _sample_nearest(image: np.ndarray, src_x: np.ndarray, src_y: np.ndarray,
                     w: int, h: int) -> np.ndarray:
    """Nearest-neighbor sampling for all output pixels."""
    ix = np.round(src_x).astype(int)
    iy = np.round(src_y).astype(int)
    valid = (ix >= 0) & (ix < w) & (iy >= 0) & (iy < h)

    channels = image.shape[2] if image.ndim == 3 else 1
    result = np.zeros((len(src_x), channels), dtype=image.dtype)
    result[valid] = image[iy[valid], ix[valid]]
    return result


def _sample_bilinear(image: np.ndarray, src_x: np.ndarray, src_y: np.ndarray,
                      w: int, h: int) -> np.ndarray:
    """Bilinear interpolation for all output pixels."""
    x0 = np.floor(src_x).astype(int)
    y0 = np.floor(src_y).astype(int)
    x1 = x0 + 1
    y1 = y0 + 1

    valid = (x0 >= 0) & (x1 < w) & (y0 >= 0) & (y1 < h)

    fx = (src_x - x0).astype(np.float64)
    fy = (src_y - y0).astype(np.float64)

    channels = image.shape[2] if image.ndim == 3 else 1
    result = np.zeros((len(src_x), channels), dtype=np.float64)

    if np.any(valid):
        x0v, y0v, x1v, y1v = x0[valid], y0[valid], x1[valid], y1[valid]
        fxv, fyv = fx[valid], fy[valid]

        p00 = image[y0v, x0v].astype(np.float64)
        p10 = image[y0v, x1v].astype(np.float64)
        p01 = image[y1v, x0v].astype(np.float64)
        p11 = image[y1v, x1v].astype(np.float64)

        w00 = ((1 - fxv) * (1 - fyv))[:, np.newaxis]
        w10 = (fxv * (1 - fyv))[:, np.newaxis]
        w01 = ((1 - fxv) * fyv)[:, np.newaxis]
        w11 = (fxv * fyv)[:, np.newaxis]

        result[valid] = p00 * w00 + p10 * w10 + p01 * w01 + p11 * w11

    return np.clip(result, 0, 255).astype(image.dtype)


def _get_interpolation_flag(interp: str) -> int:
    """Convert string interpolation name to OpenCV flag."""
    flags = {
        'nearest': cv2.INTER_NEAREST,
        'bilinear': cv2.INTER_LINEAR,
        'cubic': cv2.INTER_CUBIC,
    }
    return flags.get(interp, cv2.INTER_LINEAR)


def _get_border_flag(border: str) -> int:
    """Convert string border mode to OpenCV flag."""
    flags = {
        'constant': cv2.BORDER_CONSTANT,
        'reflect': cv2.BORDER_REFLECT,
        'wrap': cv2.BORDER_WRAP,
        'replicate': cv2.BORDER_REPLICATE,
    }
    return flags.get(border, cv2.BORDER_CONSTANT)

"""
matrix_engine.py — Python 3×3 Matrix Math Engine

Pure NumPy implementation of all matrix operations used
by the transformation tool. Mirrors the JavaScript matrix.js module.
"""

import numpy as np
from typing import Optional, Tuple, List


def identity() -> np.ndarray:
    """Return the 3×3 identity matrix."""
    return np.eye(3, dtype=np.float64)


def multiply(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Multiply two 3×3 matrices: C = A × B."""
    return a @ b


def determinant(m: np.ndarray) -> float:
    """Calculate the determinant of a 3×3 matrix."""
    return float(np.linalg.det(m))


def invert(m: np.ndarray) -> Optional[np.ndarray]:
    """
    Compute the inverse of a 3×3 matrix.
    Returns None if the matrix is singular.
    """
    det = determinant(m)
    if abs(det) < 1e-10:
        return None
    return np.linalg.inv(m)


def transpose(m: np.ndarray) -> np.ndarray:
    """Return the transpose of a 3×3 matrix."""
    return m.T.copy()


def apply_to_point(m: np.ndarray, x: float, y: float) -> Tuple[float, float]:
    """
    Transform a single point (x, y) through matrix M.
    Returns (x', y') with perspective division.
    """
    p = np.array([x, y, 1.0], dtype=np.float64)
    result = m @ p
    w = result[2]
    if abs(w) < 1e-10:
        return (0.0, 0.0)
    return (result[0] / w, result[1] / w)


def is_affine(m: np.ndarray) -> bool:
    """Check if the matrix represents an affine transformation."""
    return (abs(m[2, 0]) < 1e-10 and
            abs(m[2, 1]) < 1e-10 and
            abs(m[2, 2] - 1) < 1e-10)


def equals(a: np.ndarray, b: np.ndarray, epsilon: float = 1e-10) -> bool:
    """Check if two matrices are approximately equal."""
    return np.allclose(a, b, atol=epsilon)


def from_list(values: List[float]) -> np.ndarray:
    """
    Create a 3×3 matrix from a flat list of 9 values (row-major).
    Example: [a,b,c, d,e,f, g,h,i]
    """
    if len(values) != 9:
        raise ValueError("Expected 9 values for a 3x3 matrix")
    return np.array(values, dtype=np.float64).reshape(3, 3)


def to_list(m: np.ndarray) -> List[float]:
    """Convert a 3×3 matrix to a flat list of 9 values (row-major)."""
    return m.flatten().tolist()


def eigenvalues(m: np.ndarray) -> np.ndarray:
    """Compute eigenvalues of the matrix."""
    return np.linalg.eigvals(m)


def svd(m: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute Singular Value Decomposition: M = U × S × Vt."""
    return np.linalg.svd(m)


def compose(*matrices: np.ndarray) -> np.ndarray:
    """
    Compose multiple transformations.
    compose(A, B, C) returns C @ B @ A (A applied first, then B, then C).
    """
    result = identity()
    for m in matrices:
        result = m @ result
    return result


def decompose_affine(m: np.ndarray) -> dict:
    """
    Decompose an affine matrix into translation, rotation, scale, and shear.
    Returns a dict with keys: translation, rotation_deg, scale, shear.
    """
    tx, ty = m[0, 2], m[1, 2]

    # Extract the 2×2 linear part
    a, b = m[0, 0], m[0, 1]
    c, d = m[1, 0], m[1, 1]

    # Scale
    sx = np.sqrt(a*a + c*c)
    sy = np.sqrt(b*b + d*d)

    # Check for reflection
    det_2x2 = a*d - b*c
    if det_2x2 < 0:
        sy = -sy

    # Rotation
    rotation_rad = np.arctan2(c, a)
    rotation_deg = float(np.degrees(rotation_rad))

    # Shear
    shear = 0.0
    if sx > 1e-10:
        shear = (a*b + c*d) / (sx * sx)

    return {
        'translation': (float(tx), float(ty)),
        'rotation_deg': rotation_deg,
        'scale': (float(sx), float(sy)),
        'shear': float(shear)
    }

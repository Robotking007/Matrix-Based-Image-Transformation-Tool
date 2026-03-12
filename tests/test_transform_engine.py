"""
test_transform_engine.py — Unit tests for the Python image transformation engine.

Run with: python -m pytest tests/ -v
"""

import numpy as np
import cv2
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from python.matrix_engine import identity
from python.transform_engine import (
    apply_transform,
    apply_transform_manual,
    compute_bounding_box,
    rotation_matrix,
    scale_matrix,
    translation_matrix,
    shear_matrix,
    reflection_matrix,
    perspective_matrix,
)


def make_test_image(w=100, h=80, channels=3):
    """Create a simple test image with a known pattern."""
    img = np.zeros((h, w, channels), dtype=np.uint8)
    # Red quadrant top-left
    img[:h//2, :w//2, 2] = 255
    # Green quadrant top-right
    img[:h//2, w//2:, 1] = 255
    # Blue quadrant bottom-left
    img[h//2:, :w//2, 0] = 255
    # White quadrant bottom-right
    img[h//2:, w//2:, :] = 255
    return img


class TestApplyTransform:
    def test_identity_preserves_image(self):
        img = make_test_image()
        result = apply_transform(img, identity())
        assert np.array_equal(result, img)

    def test_translation_shifts_pixels(self):
        img = make_test_image()
        m = translation_matrix(10, 0)
        result = apply_transform(img, m.astype(np.float64))
        # Left column should be black (shifted right)
        assert np.all(result[:, :10] == 0)

    def test_scale_up(self):
        img = make_test_image(50, 50)
        center = (25, 25)
        m = scale_matrix(2.0, 2.0, center=center)
        result = apply_transform(img, m, output_size=(100, 100))
        assert result.shape[:2] == (100, 100)

    def test_rotation_90(self):
        img = make_test_image(100, 100)
        center = (50.0, 50.0)
        rot_2x3 = rotation_matrix(90, center=center)
        m = np.vstack([rot_2x3, [0, 0, 1]])
        result = apply_transform(img, m)
        assert result.shape == img.shape

    def test_reflection_x(self):
        img = make_test_image(100, 80)
        m = reflection_matrix('x', 100)
        result = apply_transform(img, m)
        # Reflected image: column 0 should now have what was in column 99
        assert np.allclose(result[:, 0], img[:, 99], atol=1)

    def test_perspective_runs(self):
        img = make_test_image()
        m = perspective_matrix(0.001, 0)
        result = apply_transform(img, m)
        assert result.shape == img.shape


class TestManualTransform:
    def test_identity_manual(self):
        img = make_test_image(50, 50)
        result = apply_transform_manual(img, identity())
        assert np.allclose(result, img, atol=1)

    def test_translation_manual(self):
        img = make_test_image(50, 50)
        m = translation_matrix(5, 5)
        result = apply_transform_manual(img, m, interpolation='nearest')
        # Pixels shifted: top-left corner should be black
        assert np.all(result[:5, :5] == 0)


class TestComputeBoundingBox:
    def test_identity_bbox(self):
        x, y, bw, bh = compute_bounding_box(identity(), 100, 80)
        assert x == 0 and y == 0 and bw == 100 and bh == 80

    def test_translation_bbox(self):
        m = translation_matrix(50, 30)
        x, y, bw, bh = compute_bounding_box(m, 100, 80)
        assert x == 50 and y == 30 and bw == 100 and bh == 80

    def test_scale_bbox(self):
        m = scale_matrix(2, 2)
        x, y, bw, bh = compute_bounding_box(m, 100, 80)
        assert bw == 200 and bh == 160


class TestPresetMatrices:
    def test_rotation_matrix_shape(self):
        m = rotation_matrix(45)
        # This returns 2x3 when center given, 3x3 when not
        assert m.shape in [(2, 3), (3, 3)]

    def test_scale_matrix(self):
        m = scale_matrix(2, 3)
        assert m[0, 0] == pytest.approx(2.0)
        assert m[1, 1] == pytest.approx(3.0)

    def test_translation_matrix(self):
        m = translation_matrix(10, 20)
        assert m[0, 2] == pytest.approx(10.0)
        assert m[1, 2] == pytest.approx(20.0)

    def test_shear_matrix(self):
        m = shear_matrix(0.5, 0.3)
        assert m[0, 1] == pytest.approx(0.5)
        assert m[1, 0] == pytest.approx(0.3)

    def test_reflection_x(self):
        m = reflection_matrix('x', 100)
        assert m[0, 0] == pytest.approx(-1.0)
        assert m[0, 2] == pytest.approx(100.0)

    def test_reflection_y(self):
        m = reflection_matrix('y', 80)
        assert m[1, 1] == pytest.approx(-1.0)
        assert m[1, 2] == pytest.approx(80.0)

    def test_perspective_matrix(self):
        m = perspective_matrix(0.001, 0.002)
        assert m[2, 0] == pytest.approx(0.001)
        assert m[2, 1] == pytest.approx(0.002)

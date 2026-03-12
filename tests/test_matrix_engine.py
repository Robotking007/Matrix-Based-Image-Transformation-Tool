"""
test_matrix_engine.py — Unit tests for the Python matrix math engine.

Run with: python -m pytest tests/ -v
"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from python.matrix_engine import (
    identity, multiply, determinant, invert, transpose,
    apply_to_point, is_affine, equals, from_list, to_list,
    compose, decompose_affine, eigenvalues
)


class TestIdentity:
    def test_identity_shape(self):
        m = identity()
        assert m.shape == (3, 3)

    def test_identity_values(self):
        m = identity()
        expected = np.eye(3)
        assert np.allclose(m, expected)

    def test_identity_determinant(self):
        assert determinant(identity()) == pytest.approx(1.0)


class TestMultiply:
    def test_identity_multiply(self):
        a = np.array([[2, 3, 1], [0, 1, 4], [0, 0, 1]], dtype=np.float64)
        result = multiply(identity(), a)
        assert np.allclose(result, a)

    def test_multiply_order(self):
        a = np.array([[1, 0, 5], [0, 1, 10], [0, 0, 1]], dtype=np.float64)  # translate(5, 10)
        b = np.array([[2, 0, 0], [0, 2, 0], [0, 0, 1]], dtype=np.float64)  # scale(2, 2)
        ab = multiply(a, b)
        ba = multiply(b, a)
        assert not np.allclose(ab, ba), "Matrix multiplication should not be commutative in general"

    def test_known_product(self):
        a = np.array([[1, 2, 0], [3, 4, 0], [0, 0, 1]], dtype=np.float64)
        b = np.array([[5, 6, 0], [7, 8, 0], [0, 0, 1]], dtype=np.float64)
        result = multiply(a, b)
        expected = a @ b
        assert np.allclose(result, expected)


class TestDeterminant:
    def test_identity_det(self):
        assert determinant(identity()) == pytest.approx(1.0)

    def test_scaling_det(self):
        m = np.array([[2, 0, 0], [0, 3, 0], [0, 0, 1]], dtype=np.float64)
        assert determinant(m) == pytest.approx(6.0)

    def test_singular_det(self):
        m = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=np.float64)
        assert abs(determinant(m)) < 1e-6

    def test_reflection_det(self):
        m = np.array([[-1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=np.float64)
        assert determinant(m) == pytest.approx(-1.0)


class TestInvert:
    def test_identity_inverse(self):
        inv = invert(identity())
        assert np.allclose(inv, identity())

    def test_translation_inverse(self):
        m = np.array([[1, 0, 50], [0, 1, 30], [0, 0, 1]], dtype=np.float64)
        inv = invert(m)
        assert inv is not None
        assert np.allclose(inv, np.array([[1, 0, -50], [0, 1, -30], [0, 0, 1]]))

    def test_inverse_product(self):
        m = np.array([[2, 1, 3], [0, 3, 1], [0, 0, 1]], dtype=np.float64)
        inv = invert(m)
        assert inv is not None
        product = multiply(m, inv)
        assert np.allclose(product, identity(), atol=1e-9)

    def test_singular_returns_none(self):
        m = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=np.float64)
        assert invert(m) is None


class TestTranspose:
    def test_transpose(self):
        m = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=np.float64)
        t = transpose(m)
        expected = np.array([[1, 4, 7], [2, 5, 8], [3, 6, 9]], dtype=np.float64)
        assert np.allclose(t, expected)

    def test_identity_transpose(self):
        assert np.allclose(transpose(identity()), identity())


class TestApplyToPoint:
    def test_identity_point(self):
        x, y = apply_to_point(identity(), 10, 20)
        assert x == pytest.approx(10.0)
        assert y == pytest.approx(20.0)

    def test_translation(self):
        m = np.array([[1, 0, 100], [0, 1, 200], [0, 0, 1]], dtype=np.float64)
        x, y = apply_to_point(m, 10, 20)
        assert x == pytest.approx(110.0)
        assert y == pytest.approx(220.0)

    def test_scaling(self):
        m = np.array([[2, 0, 0], [0, 3, 0], [0, 0, 1]], dtype=np.float64)
        x, y = apply_to_point(m, 5, 10)
        assert x == pytest.approx(10.0)
        assert y == pytest.approx(30.0)

    def test_perspective_division(self):
        m = np.array([[1, 0, 0], [0, 1, 0], [0.01, 0, 1]], dtype=np.float64)
        x, y = apply_to_point(m, 100, 50)
        expected_w = 0.01 * 100 + 0 + 1  # = 2.0
        assert x == pytest.approx(100.0 / 2.0)
        assert y == pytest.approx(50.0 / 2.0)


class TestIsAffine:
    def test_identity_is_affine(self):
        assert is_affine(identity()) is True

    def test_translation_is_affine(self):
        m = np.array([[1, 0, 50], [0, 1, 30], [0, 0, 1]], dtype=np.float64)
        assert is_affine(m) is True

    def test_perspective_not_affine(self):
        m = np.array([[1, 0, 0], [0, 1, 0], [0.001, 0, 1]], dtype=np.float64)
        assert is_affine(m) is False


class TestCompose:
    def test_compose_identity(self):
        result = compose(identity(), identity())
        assert np.allclose(result, identity())

    def test_compose_two_translations(self):
        t1 = np.array([[1, 0, 10], [0, 1, 20], [0, 0, 1]], dtype=np.float64)
        t2 = np.array([[1, 0, 30], [0, 1, 40], [0, 0, 1]], dtype=np.float64)
        result = compose(t1, t2)
        expected = np.array([[1, 0, 40], [0, 1, 60], [0, 0, 1]], dtype=np.float64)
        assert np.allclose(result, expected)


class TestDecomposeAffine:
    def test_decompose_translation(self):
        m = np.array([[1, 0, 50], [0, 1, 30], [0, 0, 1]], dtype=np.float64)
        d = decompose_affine(m)
        assert d['translation'] == pytest.approx((50.0, 30.0))
        assert d['rotation_deg'] == pytest.approx(0.0, abs=1e-6)
        assert d['scale'] == pytest.approx((1.0, 1.0), abs=1e-6)

    def test_decompose_rotation(self):
        angle = 45.0
        rad = np.radians(angle)
        c, s = np.cos(rad), np.sin(rad)
        m = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=np.float64)
        d = decompose_affine(m)
        assert d['rotation_deg'] == pytest.approx(45.0, abs=0.01)

    def test_decompose_scale(self):
        m = np.array([[2, 0, 0], [0, 3, 0], [0, 0, 1]], dtype=np.float64)
        d = decompose_affine(m)
        assert d['scale'][0] == pytest.approx(2.0)
        assert d['scale'][1] == pytest.approx(3.0)


class TestFromToList:
    def test_roundtrip(self):
        original = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        m = from_list(original)
        result = to_list(m)
        assert result == pytest.approx(original)

    def test_invalid_length(self):
        with pytest.raises(ValueError):
            from_list([1, 2, 3])

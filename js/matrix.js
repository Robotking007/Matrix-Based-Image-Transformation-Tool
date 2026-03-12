/**
 * matrix.js — 3×3 Matrix Math Engine
 *
 * All matrices are represented as flat 9-element arrays in row-major order:
 *   [ a, b, c,
 *     d, e, f,
 *     g, h, i ]
 *
 * which corresponds to:
 *   | a  b  c |
 *   | d  e  f |
 *   | g  h  i |
 */

const Matrix = (() => {
  'use strict';

  /** Returns the 3×3 identity matrix. */
  function identity() {
    return [
      1, 0, 0,
      0, 1, 0,
      0, 0, 1
    ];
  }

  /** Multiplies two 3×3 matrices: C = A × B. */
  function multiply(a, b) {
    return [
      a[0]*b[0] + a[1]*b[3] + a[2]*b[6],
      a[0]*b[1] + a[1]*b[4] + a[2]*b[7],
      a[0]*b[2] + a[1]*b[5] + a[2]*b[8],

      a[3]*b[0] + a[4]*b[3] + a[5]*b[6],
      a[3]*b[1] + a[4]*b[4] + a[5]*b[7],
      a[3]*b[2] + a[4]*b[5] + a[5]*b[8],

      a[6]*b[0] + a[7]*b[3] + a[8]*b[6],
      a[6]*b[1] + a[7]*b[4] + a[8]*b[7],
      a[6]*b[2] + a[7]*b[5] + a[8]*b[8]
    ];
  }

  /** Calculates the determinant of a 3×3 matrix. */
  function determinant(m) {
    return (
      m[0] * (m[4]*m[8] - m[5]*m[7]) -
      m[1] * (m[3]*m[8] - m[5]*m[6]) +
      m[2] * (m[3]*m[7] - m[4]*m[6])
    );
  }

  /** Returns the inverse of a 3×3 matrix, or null if singular. */
  function invert(m) {
    const det = determinant(m);
    if (Math.abs(det) < 1e-10) return null;
    const invDet = 1 / det;
    return [
      (m[4]*m[8] - m[5]*m[7]) * invDet,
      (m[2]*m[7] - m[1]*m[8]) * invDet,
      (m[1]*m[5] - m[2]*m[4]) * invDet,

      (m[5]*m[6] - m[3]*m[8]) * invDet,
      (m[0]*m[8] - m[2]*m[6]) * invDet,
      (m[2]*m[3] - m[0]*m[5]) * invDet,

      (m[3]*m[7] - m[4]*m[6]) * invDet,
      (m[1]*m[6] - m[0]*m[7]) * invDet,
      (m[0]*m[4] - m[1]*m[3]) * invDet
    ];
  }

  /** Returns the transpose of a 3×3 matrix. */
  function transpose(m) {
    return [
      m[0], m[3], m[6],
      m[1], m[4], m[7],
      m[2], m[5], m[8]
    ];
  }

  /**
   * Transforms a single point (x, y) through matrix M.
   * Returns [x', y'] with perspective division.
   */
  function applyToPoint(m, x, y) {
    const w = m[6]*x + m[7]*y + m[8];
    if (Math.abs(w) < 1e-10) return [0, 0];
    return [
      (m[0]*x + m[1]*y + m[2]) / w,
      (m[3]*x + m[4]*y + m[5]) / w
    ];
  }

  /** Checks if the matrix is affine (bottom row is [0, 0, 1]). */
  function isAffine(m) {
    return Math.abs(m[6]) < 1e-10 &&
           Math.abs(m[7]) < 1e-10 &&
           Math.abs(m[8] - 1) < 1e-10;
  }

  /** Creates a copy of the matrix. */
  function clone(m) {
    return m.slice();
  }

  /** Checks if two matrices are approximately equal. */
  function equals(a, b, epsilon) {
    const eps = epsilon || 1e-10;
    for (let i = 0; i < 9; i++) {
      if (Math.abs(a[i] - b[i]) > eps) return false;
    }
    return true;
  }

  return {
    identity,
    multiply,
    determinant,
    invert,
    transpose,
    applyToPoint,
    isAffine,
    clone,
    equals
  };
})();

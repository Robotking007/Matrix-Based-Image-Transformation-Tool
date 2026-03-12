/**
 * presets.js — Preset Transformation Matrices
 *
 * Factory functions that generate 3×3 transformation matrices
 * from user-friendly parameters.
 */

const Presets = (() => {
  'use strict';

  /** Rotation by angle (degrees) around origin. */
  function rotation(degrees) {
    const rad = degrees * Math.PI / 180;
    const c = Math.cos(rad);
    const s = Math.sin(rad);
    return [
      c, -s, 0,
      s,  c, 0,
      0,  0, 1
    ];
  }

  /** Rotation around center of image (w × h). */
  function rotationCenter(degrees, w, h) {
    const toOrigin = translation(-w / 2, -h / 2);
    const rot = rotation(degrees);
    const back = translation(w / 2, h / 2);
    return Matrix.multiply(back, Matrix.multiply(rot, toOrigin));
  }

  /** Uniform or non-uniform scaling. */
  function scale(sx, sy) {
    return [
      sx, 0,  0,
      0,  sy, 0,
      0,  0,  1
    ];
  }

  /** Scaling around center of image. */
  function scaleCenter(sx, sy, w, h) {
    const toOrigin = translation(-w / 2, -h / 2);
    const sc = scale(sx, sy);
    const back = translation(w / 2, h / 2);
    return Matrix.multiply(back, Matrix.multiply(sc, toOrigin));
  }

  /** Translation by (tx, ty). */
  function translation(tx, ty) {
    return [
      1, 0, tx,
      0, 1, ty,
      0, 0, 1
    ];
  }

  /** Shear along X axis. */
  function shearX(k) {
    return [
      1, k, 0,
      0, 1, 0,
      0, 0, 1
    ];
  }

  /** Shear along Y axis. */
  function shearY(k) {
    return [
      1, 0, 0,
      k, 1, 0,
      0, 0, 1
    ];
  }

  /** Combined shear. */
  function shear(kx, ky) {
    return Matrix.multiply(shearX(kx), shearY(ky));
  }

  /** Reflect across Y-axis (horizontal flip). Requires image width. */
  function reflectX(w) {
    return [
      -1, 0, w,
       0, 1, 0,
       0, 0, 1
    ];
  }

  /** Reflect across X-axis (vertical flip). Requires image height. */
  function reflectY(h) {
    return [
      1,  0, 0,
      0, -1, h,
      0,  0, 1
    ];
  }

  /** Perspective transform with coefficients g, h. */
  function perspective(g, h) {
    return [
      1, 0, 0,
      0, 1, 0,
      g, h, 1
    ];
  }

  /** Describe what a matrix does, returning a human-readable string. */
  function describe(m) {
    const id = Matrix.identity();
    if (Matrix.equals(m, id, 0.001)) return 'Identity';

    const parts = [];

    // Check for perspective
    if (Math.abs(m[6]) > 1e-6 || Math.abs(m[7]) > 1e-6) {
      parts.push('Perspective');
    }

    // Check determinant sign for reflection
    const det = Matrix.determinant(m);
    if (det < -1e-6) {
      parts.push('Reflection');
    }

    // Check for translation
    if (Math.abs(m[2]) > 0.5 || Math.abs(m[5]) > 0.5) {
      parts.push('Translation');
    }

    // Check for rotation (off-diagonal a,b,d,e elements)
    if (Math.abs(m[1]) > 1e-6 || Math.abs(m[3]) > 1e-6) {
      if (Math.abs(m[1] + m[3]) < 1e-4 && Math.abs(m[0] - m[4]) < 1e-4) {
        parts.push('Rotation');
      } else {
        parts.push('Shear/Rotation');
      }
    }

    // Check for scaling
    if (Math.abs(Math.abs(m[0]) - 1) > 1e-6 || Math.abs(Math.abs(m[4]) - 1) > 1e-6) {
      parts.push('Scale');
    }

    return parts.length > 0 ? parts.join(' + ') : 'Custom';
  }

  return {
    rotation,
    rotationCenter,
    scale,
    scaleCenter,
    translation,
    shearX,
    shearY,
    shear,
    reflectX,
    reflectY,
    perspective,
    describe
  };
})();

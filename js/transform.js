/**
 * transform.js — Image Transformation Engine
 *
 * Applies 3×3 matrix transformations to image pixel data.
 * Uses inverse mapping to avoid holes in the output.
 */

const Transform = (() => {
  'use strict';

  /**
   * Apply an affine transform using native Canvas setTransform (GPU-accelerated).
   * @param {CanvasRenderingContext2D} ctx - Target canvas context.
   * @param {HTMLImageElement|HTMLCanvasElement} source - Source image.
   * @param {number[]} m - 3×3 transformation matrix (row-major).
   * @param {number} outW - Output canvas width.
   * @param {number} outH - Output canvas height.
   */
  function applyAffine(ctx, source, m, outW, outH) {
    ctx.clearRect(0, 0, outW, outH);
    ctx.save();
    // Canvas setTransform uses column notation:
    // setTransform(a, b, c, d, e, f) where:
    //   a = m[0], b = m[3], c = m[1], d = m[4], e = m[2], f = m[5]
    ctx.setTransform(m[0], m[3], m[1], m[4], m[2], m[5]);
    ctx.drawImage(source, 0, 0);
    ctx.restore();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
  }

  /**
   * Apply a perspective (non-affine) transform using per-pixel inverse mapping.
   * @param {CanvasRenderingContext2D} ctx - Target canvas context.
   * @param {ImageData} srcData - Source image data.
   * @param {number[]} m - 3×3 transformation matrix (row-major).
   * @param {number} outW - Output width.
   * @param {number} outH - Output height.
   * @param {boolean} bilinear - Use bilinear interpolation.
   */
  function applyPerspective(ctx, srcData, m, outW, outH, bilinear) {
    const inv = Matrix.invert(m);
    if (!inv) {
      ctx.clearRect(0, 0, outW, outH);
      return;
    }

    const srcW = srcData.width;
    const srcH = srcData.height;
    const src = srcData.data;
    const output = ctx.createImageData(outW, outH);
    const dst = output.data;

    for (let y = 0; y < outH; y++) {
      for (let x = 0; x < outW; x++) {
        // Inverse map: find source coordinate for this output pixel
        const w = inv[6]*x + inv[7]*y + inv[8];
        if (Math.abs(w) < 1e-10) continue;

        const sx = (inv[0]*x + inv[1]*y + inv[2]) / w;
        const sy = (inv[3]*x + inv[4]*y + inv[5]) / w;

        const dstIdx = (y * outW + x) * 4;

        if (bilinear) {
          sampleBilinear(src, srcW, srcH, sx, sy, dst, dstIdx);
        } else {
          sampleNearest(src, srcW, srcH, sx, sy, dst, dstIdx);
        }
      }
    }

    ctx.putImageData(output, 0, 0);
  }

  /** Nearest-neighbor sampling. */
  function sampleNearest(src, w, h, sx, sy, dst, dstIdx) {
    const ix = Math.round(sx);
    const iy = Math.round(sy);
    if (ix < 0 || ix >= w || iy < 0 || iy >= h) {
      dst[dstIdx] = dst[dstIdx+1] = dst[dstIdx+2] = dst[dstIdx+3] = 0;
      return;
    }
    const srcIdx = (iy * w + ix) * 4;
    dst[dstIdx]   = src[srcIdx];
    dst[dstIdx+1] = src[srcIdx+1];
    dst[dstIdx+2] = src[srcIdx+2];
    dst[dstIdx+3] = src[srcIdx+3];
  }

  /** Bilinear interpolation sampling. */
  function sampleBilinear(src, w, h, sx, sy, dst, dstIdx) {
    const x0 = Math.floor(sx);
    const y0 = Math.floor(sy);
    const x1 = x0 + 1;
    const y1 = y0 + 1;

    if (x0 < 0 || x1 >= w || y0 < 0 || y1 >= h) {
      // Fall back to nearest for edge pixels
      sampleNearest(src, w, h, sx, sy, dst, dstIdx);
      return;
    }

    const fx = sx - x0;
    const fy = sy - y0;
    const fx1 = 1 - fx;
    const fy1 = 1 - fy;

    const i00 = (y0 * w + x0) * 4;
    const i10 = (y0 * w + x1) * 4;
    const i01 = (y1 * w + x0) * 4;
    const i11 = (y1 * w + x1) * 4;

    const w00 = fx1 * fy1;
    const w10 = fx  * fy1;
    const w01 = fx1 * fy;
    const w11 = fx  * fy;

    for (let c = 0; c < 4; c++) {
      dst[dstIdx + c] = Math.round(
        src[i00+c]*w00 + src[i10+c]*w10 +
        src[i01+c]*w01 + src[i11+c]*w11
      );
    }
  }

  /**
   * Main transform function — chooses affine or perspective path.
   * @param {CanvasRenderingContext2D} ctx - Target context.
   * @param {HTMLImageElement|HTMLCanvasElement} sourceElement - Source image element.
   * @param {ImageData} sourceData - Source image data (for perspective).
   * @param {number[]} matrix - 3×3 matrix.
   * @param {number} outW - Output width.
   * @param {number} outH - Output height.
   * @param {boolean} bilinear - Bilinear interpolation.
   */
  function apply(ctx, sourceElement, sourceData, matrix, outW, outH, bilinear) {
    if (Matrix.isAffine(matrix)) {
      applyAffine(ctx, sourceElement, matrix, outW, outH);
    } else {
      applyPerspective(ctx, sourceData, matrix, outW, outH, bilinear);
    }
  }

  /**
   * Compute output bounding box for a given image size and matrix.
   * Returns { x, y, width, height }.
   */
  function computeBounds(m, w, h) {
    const corners = [
      [0, 0], [w, 0], [0, h], [w, h]
    ];
    let minX = Infinity, minY = Infinity;
    let maxX = -Infinity, maxY = -Infinity;

    for (const [cx, cy] of corners) {
      const [tx, ty] = Matrix.applyToPoint(m, cx, cy);
      if (tx < minX) minX = tx;
      if (ty < minY) minY = ty;
      if (tx > maxX) maxX = tx;
      if (ty > maxY) maxY = ty;
    }

    return {
      x: Math.floor(minX),
      y: Math.floor(minY),
      width: Math.ceil(maxX - minX),
      height: Math.ceil(maxY - minY)
    };
  }

  return {
    apply,
    applyAffine,
    applyPerspective,
    computeBounds
  };
})();

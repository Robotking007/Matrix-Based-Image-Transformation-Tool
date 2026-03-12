/**
 * app.js — Application Entry Point
 *
 * Initializes canvases, loads default content, wires up
 * the UI to the transform engine, and manages rendering.
 */

(function () {
  'use strict';

  const originalCanvas = document.getElementById('originalCanvas');
  const transformedCanvas = document.getElementById('transformedCanvas');
  const originalCtx = originalCanvas.getContext('2d');
  const transformedCtx = transformedCanvas.getContext('2d');

  let sourceImage = null;
  let sourceImageData = null;

  /** Resize both canvases to match image dimensions. */
  function resizeCanvases(w, h) {
    originalCanvas.width = w;
    originalCanvas.height = h;
    transformedCanvas.width = w;
    transformedCanvas.height = h;
  }

  /** Draw the original image on the left canvas. */
  function drawOriginal(img) {
    resizeCanvases(img.width, img.height);
    originalCtx.clearRect(0, 0, img.width, img.height);
    originalCtx.drawImage(img, 0, 0);
    sourceImageData = originalCtx.getImageData(0, 0, img.width, img.height);
    UI.setSourceImageData(sourceImageData);
  }

  /** Apply the current combined matrix and render to the transformed canvas. */
  function renderTransform(combinedMatrix) {
    if (!sourceImage) return;

    const w = sourceImage.width;
    const h = sourceImage.height;

    transformedCtx.clearRect(0, 0, w, h);

    Transform.apply(
      transformedCtx,
      sourceImage,
      sourceImageData,
      combinedMatrix,
      w,
      h,
      UI.isBilinear()
    );
  }

  /** Download the transformed canvas as PNG. */
  function downloadImage() {
    if (!sourceImage) return;
    const link = document.createElement('a');
    link.download = 'transformed-image.png';
    link.href = transformedCanvas.toDataURL('image/png');
    link.click();
  }

  /** Generate a default sample image (gradient with shapes). */
  function generateSampleImage() {
    const w = 400;
    const h = 300;
    const canvas = document.createElement('canvas');
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext('2d');

    // Background gradient
    const grad = ctx.createLinearGradient(0, 0, w, h);
    grad.addColorStop(0, '#667eea');
    grad.addColorStop(0.5, '#764ba2');
    grad.addColorStop(1, '#f093fb');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);

    // Grid lines
    ctx.strokeStyle = 'rgba(255,255,255,0.15)';
    ctx.lineWidth = 1;
    for (let x = 0; x <= w; x += 40) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
    }
    for (let y = 0; y <= h; y += 40) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
    }

    // Circle
    ctx.fillStyle = 'rgba(255,255,255,0.3)';
    ctx.beginPath();
    ctx.arc(w * 0.3, h * 0.4, 50, 0, Math.PI * 2);
    ctx.fill();

    // Rectangle
    ctx.fillStyle = 'rgba(255,255,255,0.25)';
    ctx.fillRect(w * 0.55, h * 0.25, 100, 60);

    // Triangle
    ctx.fillStyle = 'rgba(255,255,255,0.2)';
    ctx.beginPath();
    ctx.moveTo(w * 0.5, h * 0.7);
    ctx.lineTo(w * 0.35, h * 0.9);
    ctx.lineTo(w * 0.65, h * 0.9);
    ctx.closePath();
    ctx.fill();

    // Text
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 24px Segoe UI, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Matrix Transform', w / 2, h * 0.15);
    ctx.font = '14px Segoe UI, sans-serif';
    ctx.fillStyle = 'rgba(255,255,255,0.7)';
    ctx.fillText('Upload your image or use this sample', w / 2, h * 0.15 + 25);

    // Coordinate axes
    ctx.strokeStyle = 'rgba(255,255,255,0.5)';
    ctx.lineWidth = 2;
    // X axis
    ctx.beginPath(); ctx.moveTo(20, h - 20); ctx.lineTo(120, h - 20); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(115, h - 25); ctx.lineTo(120, h - 20); ctx.lineTo(115, h - 15); ctx.stroke();
    // Y axis
    ctx.beginPath(); ctx.moveTo(20, h - 20); ctx.lineTo(20, h - 120); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(15, h - 115); ctx.lineTo(20, h - 120); ctx.lineTo(25, h - 115); ctx.stroke();

    ctx.font = '12px Consolas, monospace';
    ctx.fillStyle = 'rgba(255,255,255,0.6)';
    ctx.textAlign = 'left';
    ctx.fillText('x', 125, h - 16);
    ctx.fillText('y', 10, h - 125);

    return canvas;
  }

  /** Load sample image into the app. */
  function loadSampleImage() {
    const sampleCanvas = generateSampleImage();
    const img = new Image();
    img.onload = () => {
      sourceImage = img;
      drawOriginal(img);
      renderTransform(UI.getCombinedMatrix());
      document.getElementById('imgDimensions').textContent = `${img.width} × ${img.height} px`;
    };
    img.src = sampleCanvas.toDataURL();
  }

  // ===== Initialize =====
  UI.init(renderTransform);

  UI.onImageLoaded = (img) => {
    sourceImage = img;
    drawOriginal(img);
    renderTransform(UI.getCombinedMatrix());
  };

  UI.onDownload = downloadImage;

  // Load default sample
  loadSampleImage();
})();

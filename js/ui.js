/**
 * ui.js — User Interface Controller
 *
 * Manages all DOM interactions: matrix grid, presets, sliders,
 * image upload, history (undo/redo), and canvas coordination.
 */

const UI = (() => {
  'use strict';

  // DOM references
  const elements = {};

  // State
  let currentMatrix = Matrix.identity();
  let accumulatedMatrix = Matrix.identity();
  let history = [Matrix.clone(Matrix.identity())];
  let historyIndex = 0;
  let sourceImage = null;
  let sourceImageData = null;

  // Callbacks
  let onTransformUpdate = null;

  /** Cache all DOM element references. */
  function cacheElements() {
    elements.uploadArea = document.getElementById('uploadArea');
    elements.uploadPlaceholder = document.getElementById('uploadPlaceholder');
    elements.uploadPreview = document.getElementById('uploadPreview');
    elements.fileInput = document.getElementById('fileInput');
    elements.matrixGrid = document.getElementById('matrixGrid');
    elements.matrixCells = document.querySelectorAll('.matrix-cell');
    elements.detValue = document.getElementById('detValue');
    elements.bilinearToggle = document.getElementById('bilinearToggle');

    // Sliders
    elements.rotAngle = document.getElementById('rotAngle');
    elements.rotAngleVal = document.getElementById('rotAngleVal');
    elements.scaleX = document.getElementById('scaleX');
    elements.scaleXVal = document.getElementById('scaleXVal');
    elements.scaleY = document.getElementById('scaleY');
    elements.scaleYVal = document.getElementById('scaleYVal');
    elements.transX = document.getElementById('transX');
    elements.transXVal = document.getElementById('transXVal');
    elements.transY = document.getElementById('transY');
    elements.transYVal = document.getElementById('transYVal');
    elements.shearX = document.getElementById('shearX');
    elements.shearXVal = document.getElementById('shearXVal');
    elements.shearY = document.getElementById('shearY');
    elements.shearYVal = document.getElementById('shearYVal');
    elements.perspG = document.getElementById('perspG');
    elements.perspGVal = document.getElementById('perspGVal');
    elements.perspH = document.getElementById('perspH');
    elements.perspHVal = document.getElementById('perspHVal');

    // Buttons
    elements.btnApplyCompose = document.getElementById('btnApplyCompose');
    elements.btnReset = document.getElementById('btnReset');
    elements.btnUndo = document.getElementById('btnUndo');
    elements.btnRedo = document.getElementById('btnRedo');
    elements.btnDownload = document.getElementById('btnDownload');

    // Info
    elements.imgDimensions = document.getElementById('imgDimensions');
    elements.transformType = document.getElementById('transformType');
  }

  /** Set the current matrix and update the UI grid. */
  function setMatrix(m) {
    currentMatrix = Matrix.clone(m);
    updateGridFromMatrix();
    updateDeterminant();
    updateTransformLabel();
    triggerTransform();
  }

  /** Read matrix values from the UI grid. */
  function readMatrixFromGrid() {
    const m = [];
    elements.matrixCells.forEach(cell => {
      const val = parseFloat(cell.value);
      m.push(isNaN(val) ? 0 : val);
    });
    return m;
  }

  /** Write matrix values to the UI grid. */
  function updateGridFromMatrix() {
    elements.matrixCells.forEach((cell, i) => {
      const val = currentMatrix[i];
      cell.value = Number.isInteger(val) ? val : parseFloat(val.toFixed(6));

      // Highlight non-identity values
      const identityVals = [1,0,0, 0,1,0, 0,0,1];
      cell.classList.toggle('changed', Math.abs(val - identityVals[i]) > 1e-6);
    });
  }

  /** Update the determinant display. */
  function updateDeterminant() {
    const det = Matrix.determinant(currentMatrix);
    elements.detValue.textContent = det.toFixed(4);
    elements.detValue.style.color = Math.abs(det) < 1e-6 ? '#f87171' : '';
  }

  /** Update the transform type label. */
  function updateTransformLabel() {
    const combined = Matrix.multiply(currentMatrix, accumulatedMatrix);
    elements.transformType.textContent = 'Transform: ' + Presets.describe(combined);
  }

  /** Push current matrix to history. */
  function pushHistory() {
    // Discard any redo states
    history = history.slice(0, historyIndex + 1);
    history.push(Matrix.clone(currentMatrix));
    historyIndex = history.length - 1;
    updateHistoryButtons();
  }

  /** Undo to previous state. */
  function undo() {
    if (historyIndex <= 0) return;
    historyIndex--;
    setMatrix(history[historyIndex]);
    updateHistoryButtons();
  }

  /** Redo to next state. */
  function redo() {
    if (historyIndex >= history.length - 1) return;
    historyIndex++;
    setMatrix(history[historyIndex]);
    updateHistoryButtons();
  }

  /** Update undo/redo button states. */
  function updateHistoryButtons() {
    elements.btnUndo.disabled = historyIndex <= 0;
    elements.btnRedo.disabled = historyIndex >= history.length - 1;
  }

  /** Trigger the transform callback. */
  function triggerTransform() {
    if (onTransformUpdate) {
      const combined = Matrix.multiply(currentMatrix, accumulatedMatrix);
      onTransformUpdate(combined);
    }
  }

  // ===== Slider Helpers =====
  function setupSliders() {
    const sliders = [
      { el: elements.rotAngle,  display: elements.rotAngleVal, suffix: '°',  decimals: 0 },
      { el: elements.scaleX,    display: elements.scaleXVal,   suffix: '',   decimals: 1 },
      { el: elements.scaleY,    display: elements.scaleYVal,   suffix: '',   decimals: 1 },
      { el: elements.transX,    display: elements.transXVal,   suffix: '',   decimals: 0 },
      { el: elements.transY,    display: elements.transYVal,   suffix: '',   decimals: 0 },
      { el: elements.shearX,    display: elements.shearXVal,   suffix: '',   decimals: 2 },
      { el: elements.shearY,    display: elements.shearYVal,   suffix: '',   decimals: 2 },
      { el: elements.perspG,    display: elements.perspGVal,   suffix: '',   decimals: 4 },
      { el: elements.perspH,    display: elements.perspHVal,   suffix: '',   decimals: 4 },
    ];

    sliders.forEach(s => {
      s.el.addEventListener('input', () => {
        const val = parseFloat(s.el.value);
        s.display.textContent = val.toFixed(s.decimals) + s.suffix;
      });
    });
  }

  // ===== Image Upload =====
  function setupUpload() {
    elements.uploadArea.addEventListener('click', () => elements.fileInput.click());

    elements.fileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        loadImageFile(e.target.files[0]);
      }
    });

    elements.uploadArea.addEventListener('dragover', (e) => {
      e.preventDefault();
      elements.uploadArea.classList.add('drag-over');
    });

    elements.uploadArea.addEventListener('dragleave', () => {
      elements.uploadArea.classList.remove('drag-over');
    });

    elements.uploadArea.addEventListener('drop', (e) => {
      e.preventDefault();
      elements.uploadArea.classList.remove('drag-over');
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        loadImageFile(e.dataTransfer.files[0]);
      }
    });
  }

  function loadImageFile(file) {
    if (!file.type.startsWith('image/')) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        sourceImage = img;
        elements.uploadPreview.src = e.target.result;
        elements.uploadPreview.classList.remove('hidden');
        elements.uploadPlaceholder.classList.add('hidden');
        elements.imgDimensions.textContent = `${img.width} × ${img.height} px`;

        // Notify app
        if (UI.onImageLoaded) UI.onImageLoaded(img);
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  }

  // ===== Preset Buttons =====
  function setupPresets() {
    document.querySelectorAll('.preset-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const preset = btn.dataset.preset;
        const w = sourceImage ? sourceImage.width : 400;
        const h = sourceImage ? sourceImage.height : 400;
        let m;

        switch (preset) {
          case 'rotate':
            m = Presets.rotationCenter(parseFloat(elements.rotAngle.value), w, h);
            break;
          case 'rotate90':
            m = Presets.rotationCenter(90, w, h);
            break;
          case 'rotate180':
            m = Presets.rotationCenter(180, w, h);
            break;
          case 'rotate270':
            m = Presets.rotationCenter(270, w, h);
            break;
          case 'scale':
            m = Presets.scaleCenter(
              parseFloat(elements.scaleX.value),
              parseFloat(elements.scaleY.value),
              w, h
            );
            break;
          case 'translate':
            m = Presets.translation(
              parseFloat(elements.transX.value),
              parseFloat(elements.transY.value)
            );
            break;
          case 'shear':
            m = Presets.shear(
              parseFloat(elements.shearX.value),
              parseFloat(elements.shearY.value)
            );
            break;
          case 'reflectX':
            m = Presets.reflectX(w);
            break;
          case 'reflectY':
            m = Presets.reflectY(h);
            break;
          case 'perspective':
            m = Presets.perspective(
              parseFloat(elements.perspG.value),
              parseFloat(elements.perspH.value)
            );
            break;
          default:
            return;
        }

        setMatrix(m);
        pushHistory();
      });
    });
  }

  // ===== Matrix Grid Input =====
  let debounceTimer = null;

  function setupMatrixInput() {
    elements.matrixCells.forEach(cell => {
      cell.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          currentMatrix = readMatrixFromGrid();
          updateDeterminant();
          updateTransformLabel();
          triggerTransform();
          pushHistory();
        }, 80);
      });
    });
  }

  // ===== Action Buttons =====
  function setupActions() {
    elements.btnApplyCompose.addEventListener('click', () => {
      accumulatedMatrix = Matrix.multiply(currentMatrix, accumulatedMatrix);
      setMatrix(Matrix.identity());
      pushHistory();
    });

    elements.btnReset.addEventListener('click', () => {
      accumulatedMatrix = Matrix.identity();
      setMatrix(Matrix.identity());
      pushHistory();
    });

    elements.btnUndo.addEventListener('click', undo);
    elements.btnRedo.addEventListener('click', redo);

    elements.btnDownload.addEventListener('click', () => {
      if (UI.onDownload) UI.onDownload();
    });

    elements.bilinearToggle.addEventListener('change', () => {
      triggerTransform();
    });
  }

  // ===== Keyboard Shortcuts =====
  function setupKeyboard() {
    document.addEventListener('keydown', (e) => {
      // Ignore when typing in matrix cells
      if (e.target.classList.contains('matrix-cell')) return;

      if (e.ctrlKey && e.key === 'z') { e.preventDefault(); undo(); }
      if (e.ctrlKey && e.key === 'y') { e.preventDefault(); redo(); }
      if (e.ctrlKey && e.key === 's') { e.preventDefault(); if (UI.onDownload) UI.onDownload(); }
      if (e.ctrlKey && e.key === 'r') { e.preventDefault(); elements.btnReset.click(); }
      if (e.ctrlKey && e.key === 'o') { e.preventDefault(); elements.fileInput.click(); }
    });
  }

  // ===== Public Init =====
  function init(transformCallback) {
    cacheElements();
    onTransformUpdate = transformCallback;

    setupSliders();
    setupUpload();
    setupPresets();
    setupMatrixInput();
    setupActions();
    setupKeyboard();
    updateHistoryButtons();
  }

  return {
    init,
    setMatrix,
    getMatrix: () => Matrix.clone(currentMatrix),
    getAccumulated: () => Matrix.clone(accumulatedMatrix),
    getCombinedMatrix: () => Matrix.multiply(currentMatrix, accumulatedMatrix),
    isBilinear: () => elements.bilinearToggle && elements.bilinearToggle.checked,
    getSourceImage: () => sourceImage,
    setSourceImageData: (data) => { sourceImageData = data; },
    onImageLoaded: null,
    onDownload: null
  };
})();

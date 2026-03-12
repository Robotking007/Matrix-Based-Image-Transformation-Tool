# Contributors

## Project Team

This project is built and maintained by the following contributors:

| # | Name | Role |
|---|---|---|
| 1 | **Siddhant Udavant** | Project Lead & Core Architecture |
| 2 | **Trupti Shinde** | Matrix Math Engine & Algorithms |
| 3 | **Kanika Shinde** | UI/UX Design & Frontend Development |
| 4 | **Aayush Shewale** | Canvas Rendering & Image Processing |
| 5 | **Shruti Sonawane** | Testing, Documentation & Quality Assurance |

---

## Contribution Details

### 1. Siddhant Udavant — Project Lead & Core Architecture

- Defined the overall system architecture and project structure.
- Designed the module separation for both JavaScript (`matrix.js`, `transform.js`, `presets.js`, `ui.js`, `app.js`) and Python (`matrix_engine.py`, `transform_engine.py`).
- Implemented the application entry point and initialization logic (`app.js`).
- Designed the Flask REST API architecture (`server.py`) with endpoints for single transform, batch transform, and matrix analysis.
- Coordinated integration between frontend (JavaScript) and backend (Python) modules.
- Managed version control workflow and code reviews.
- Oversaw project planning, task assignment, and milestone tracking.

### 2. Trupti Shinde — Matrix Math Engine & Algorithms

- Implemented the 3×3 matrix math engine in JavaScript (`matrix.js`) and Python (`python/matrix_engine.py`).
- Developed core linear algebra functions: `multiply()`, `invert()`, `determinant()`, `transpose()`, `identity()` in both languages.
- Implemented the `applyToPoint()` / `apply_to_point()` function with perspective division.
- Built the transformation composition (matrix chaining) logic using NumPy's `@` operator.
- Developed preset transformation factory functions (`presets.js` and `transform_engine.py`): rotation, scaling, translation, shearing, reflection, and perspective matrices.
- Implemented advanced matrix analysis in Python: eigenvalue computation, SVD decomposition, and affine matrix decomposition (`decompose_affine()`).
- Validated all matrix operations against known mathematical results using pytest.

### 3. Kanika Shinde — UI/UX Design & Frontend Development

- Designed the complete user interface layout and visual styling (`style.css`).
- Built the interactive 3×3 matrix grid editor with real-time input validation.
- Implemented drag-and-drop image upload functionality.
- Created preset transformation buttons and parameter sliders.
- Developed the undo/redo history UI and action bar controls.
- Implemented keyboard shortcuts (Ctrl+Z, Ctrl+Y, Ctrl+S, Ctrl+R, Ctrl+O).
- Ensured responsive design across desktop and tablet viewports.
- Integrated frontend with Flask backend API endpoints for server-side rendering support.

### 4. Aayush Shewale — Canvas Rendering & Image Processing

- Implemented the HTML5 Canvas rendering pipeline for original and transformed views.
- Developed the pixel-level image transformation engine in JavaScript (`transform.js`) and Python (`python/transform_engine.py`).
- Built the inverse mapping algorithm to eliminate holes in transformed output — implemented in both JavaScript (per-pixel loop) and Python (NumPy vectorized).
- Implemented nearest-neighbor and bilinear interpolation modes in both JavaScript and Python.
- Handled boundary checking for out-of-bounds pixel lookups.
- Integrated native Canvas `setTransform()` for GPU-accelerated affine transforms (frontend).
- Integrated OpenCV's `warpAffine()` and `warpPerspective()` for optimized server-side transforms (Python).
- Implemented the image export (download) functionality in PNG/JPEG formats.
- Developed the CLI tool (`cli.py`) for command-line image transformations with composable flags.

### 5. Shruti Sonawane — Testing, Documentation & Quality Assurance

- Authored the project `README.md` with detailed mathematical documentation.
- Created the `CONTRIBUTING.md` (this file) with contributor details.
- Wrote comprehensive Python unit tests using pytest (`tests/test_matrix_engine.py`, `tests/test_transform_engine.py`) — 30+ test cases covering matrix operations, transformations, and edge cases.
- Performed cross-browser testing (Chrome, Firefox, Edge, Safari).
- Validated all transformation presets against expected mathematical outputs in both JavaScript and Python.
- Tested edge cases: large images, zero-determinant matrices, extreme parameter values, singular matrix handling.
- Verified Python-JavaScript parity — ensured both engines produce identical results for the same inputs.
- Documented keyboard shortcuts, UI controls, CLI usage, and API endpoints.
- Set up `requirements.txt` with pinned Python dependencies.
- Reviewed code for consistency, style adherence (PEP 8 for Python), and correctness.

---

## Contribution Summary

| Contributor | Modules Owned | Key Deliverables |
|---|---|---|
| Siddhant Udavant | `app.js`, `server.py`, Architecture | System design, Flask API, integration, project management |
| Trupti Shinde | `matrix.js`, `presets.js`, `python/matrix_engine.py` | Matrix operations (JS + Python), preset transforms, eigenvalues, SVD, decomposition |
| Kanika Shinde | `ui.js`, `style.css` | UI design, event handling, keyboard shortcuts, responsive layout, API integration |
| Aayush Shewale | `transform.js`, `python/transform_engine.py`, `cli.py` | Rendering pipeline (JS + Python), OpenCV warp, interpolation, CLI tool, image export |
| Shruti Sonawane | `README.md`, `CONTRIBUTING.md`, `tests/` | Documentation, pytest test suite (30+ tests), cross-browser QA, Python-JS parity validation |

---

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | HTML5 + CSS3 + JavaScript | Interactive web UI with Canvas rendering |
| Backend | Python + Flask | REST API for server-side transforms |
| Math Engine | JavaScript (custom) + NumPy | 3×3 matrix operations |
| Image Processing | Canvas 2D API + OpenCV | Affine & perspective warps |
| CLI | Python + argparse | Command-line batch transforms |
| Testing | pytest | Unit tests for Python modules |

---

## Acknowledgments

We would like to thank the open-source community and the following resources that guided this project:

- **OpenCV** documentation for reference implementations of affine and perspective transforms.
- **GeeksforGeeks** articles on 2D transformation matrices.
- **MDN Web Docs** for Canvas 2D API reference.
- **Linear Algebra and Its Applications** by Gilbert Strang for mathematical foundations.

---

<p align="center">
  <em>Built with collaboration, powered by linear algebra.</em>
</p>

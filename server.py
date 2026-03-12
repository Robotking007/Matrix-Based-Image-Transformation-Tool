"""
server.py — Flask Backend Server

Serves the web frontend and provides REST API endpoints for
server-side image transformations using NumPy and OpenCV.
"""

import os
import io
import json
import base64
import numpy as np
import cv2
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='.', static_url_path='')


# ===== Static File Serving =====

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory('css', filename)


@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('js', filename)


# ===== API Endpoints =====

@app.route('/api/transform', methods=['POST'])
def api_transform():
    """
    Apply a 3x3 matrix transformation to an uploaded image.

    Request JSON:
    {
        "image": "<base64 encoded image>",
        "matrix": [[a,b,c],[d,e,f],[g,h,i]],
        "interpolation": "bilinear" | "nearest",
        "output_format": "png" | "jpeg"
    }

    Response JSON:
    {
        "image": "<base64 encoded result>",
        "dimensions": [width, height],
        "determinant": float,
        "transform_type": "affine" | "perspective"
    }
    """
    data = request.get_json()
    if not data or 'image' not in data or 'matrix' not in data:
        return jsonify({'error': 'Missing image or matrix'}), 400

    try:
        # Decode image
        img_data = base64.b64decode(data['image'])
        img_array = np.frombuffer(img_data, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_UNCHANGED)

        if img is None:
            return jsonify({'error': 'Invalid image data'}), 400

        # Parse matrix
        matrix = np.array(data['matrix'], dtype=np.float64)
        if matrix.shape != (3, 3):
            return jsonify({'error': 'Matrix must be 3x3'}), 400

        # Interpolation flag
        interp_str = data.get('interpolation', 'bilinear')
        if interp_str == 'nearest':
            interp = cv2.INTER_NEAREST
        else:
            interp = cv2.INTER_LINEAR

        h, w = img.shape[:2]
        det = np.linalg.det(matrix)

        # Determine affine vs perspective
        is_affine = abs(matrix[2, 0]) < 1e-10 and abs(matrix[2, 1]) < 1e-10 and abs(matrix[2, 2] - 1) < 1e-10

        if is_affine:
            # Use affine warp (2x3 matrix)
            affine_matrix = matrix[:2, :]
            result = cv2.warpAffine(img, affine_matrix, (w, h), flags=interp,
                                     borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
            transform_type = 'affine'
        else:
            # Use perspective warp (3x3 matrix)
            result = cv2.warpPerspective(img, matrix, (w, h), flags=interp,
                                          borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
            transform_type = 'perspective'

        # Encode result
        output_format = data.get('output_format', 'png')
        if output_format == 'jpeg':
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, 92]
            ext = '.jpg'
        else:
            encode_params = [cv2.IMWRITE_PNG_COMPRESSION, 3]
            ext = '.png'

        _, buffer = cv2.imencode(ext, result, encode_params)
        result_b64 = base64.b64encode(buffer).decode('utf-8')

        return jsonify({
            'image': result_b64,
            'dimensions': [int(result.shape[1]), int(result.shape[0])],
            'determinant': float(det),
            'transform_type': transform_type
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/batch-transform', methods=['POST'])
def api_batch_transform():
    """
    Apply a sequence of transformations and return intermediate results.

    Request JSON:
    {
        "image": "<base64>",
        "transforms": [
            {"type": "rotate", "angle": 45},
            {"type": "scale", "sx": 2, "sy": 2},
            {"type": "translate", "tx": 50, "ty": 30},
            {"type": "shear", "kx": 0.3, "ky": 0},
            {"type": "reflect", "axis": "x"},
            {"type": "perspective", "g": 0.001, "h": 0},
            {"type": "custom", "matrix": [[...],[...],[...]]}
        ]
    }
    """
    data = request.get_json()
    if not data or 'image' not in data or 'transforms' not in data:
        return jsonify({'error': 'Missing image or transforms'}), 400

    try:
        img_data = base64.b64decode(data['image'])
        img_array = np.frombuffer(img_data, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_UNCHANGED)

        if img is None:
            return jsonify({'error': 'Invalid image data'}), 400

        h, w = img.shape[:2]
        results = []
        composed = np.eye(3, dtype=np.float64)

        for t in data['transforms']:
            matrix = _build_transform_matrix(t, w, h)
            composed = matrix @ composed
            results.append({
                'type': t.get('type', 'custom'),
                'matrix': composed.tolist(),
                'determinant': float(np.linalg.det(composed))
            })

        # Apply composed transform
        is_affine = abs(composed[2, 0]) < 1e-10 and abs(composed[2, 1]) < 1e-10 and abs(composed[2, 2] - 1) < 1e-10

        if is_affine:
            result = cv2.warpAffine(img, composed[:2, :], (w, h),
                                     flags=cv2.INTER_LINEAR,
                                     borderMode=cv2.BORDER_CONSTANT)
        else:
            result = cv2.warpPerspective(img, composed, (w, h),
                                          flags=cv2.INTER_LINEAR,
                                          borderMode=cv2.BORDER_CONSTANT)

        _, buffer = cv2.imencode('.png', result)
        result_b64 = base64.b64encode(buffer).decode('utf-8')

        return jsonify({
            'image': result_b64,
            'steps': results,
            'composed_matrix': composed.tolist()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/matrix-info', methods=['POST'])
def api_matrix_info():
    """
    Analyze a 3x3 matrix and return mathematical properties.

    Request JSON: { "matrix": [[a,b,c],[d,e,f],[g,h,i]] }
    Response JSON: { determinant, is_invertible, is_affine, eigenvalues, inverse, description }
    """
    data = request.get_json()
    if not data or 'matrix' not in data:
        return jsonify({'error': 'Missing matrix'}), 400

    try:
        matrix = np.array(data['matrix'], dtype=np.float64)
        if matrix.shape != (3, 3):
            return jsonify({'error': 'Matrix must be 3x3'}), 400

        det = float(np.linalg.det(matrix))
        is_invertible = abs(det) > 1e-10
        eigenvalues = np.linalg.eigvals(matrix).tolist()

        inverse = None
        if is_invertible:
            inverse = np.linalg.inv(matrix).tolist()

        is_affine = abs(matrix[2, 0]) < 1e-10 and abs(matrix[2, 1]) < 1e-10 and abs(matrix[2, 2] - 1) < 1e-10

        return jsonify({
            'determinant': det,
            'is_invertible': is_invertible,
            'is_affine': is_affine,
            'eigenvalues': [{'real': float(np.real(e)), 'imag': float(np.imag(e))} for e in eigenvalues],
            'inverse': inverse,
            'description': _describe_matrix(matrix)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===== Helper Functions =====

def _build_transform_matrix(t, w, h):
    """Build a 3x3 matrix from a transform descriptor dict."""
    ttype = t.get('type', 'custom')

    if ttype == 'rotate':
        angle = np.radians(t.get('angle', 0))
        cx, cy = w / 2, h / 2
        c, s = np.cos(angle), np.sin(angle)
        return np.array([
            [c, -s, cx - c*cx + s*cy],
            [s,  c, cy - s*cx - c*cy],
            [0,  0,  1]
        ], dtype=np.float64)

    elif ttype == 'scale':
        sx, sy = t.get('sx', 1), t.get('sy', 1)
        cx, cy = w / 2, h / 2
        return np.array([
            [sx, 0, cx - sx*cx],
            [0, sy, cy - sy*cy],
            [0,  0,  1]
        ], dtype=np.float64)

    elif ttype == 'translate':
        tx, ty = t.get('tx', 0), t.get('ty', 0)
        return np.array([
            [1, 0, tx],
            [0, 1, ty],
            [0, 0,  1]
        ], dtype=np.float64)

    elif ttype == 'shear':
        kx, ky = t.get('kx', 0), t.get('ky', 0)
        return np.array([
            [1,  kx, 0],
            [ky,  1, 0],
            [0,   0, 1]
        ], dtype=np.float64)

    elif ttype == 'reflect':
        axis = t.get('axis', 'x')
        if axis == 'x':
            return np.array([[-1,0,w],[0,1,0],[0,0,1]], dtype=np.float64)
        else:
            return np.array([[1,0,0],[0,-1,h],[0,0,1]], dtype=np.float64)

    elif ttype == 'perspective':
        g, hv = t.get('g', 0), t.get('h', 0)
        return np.array([
            [1, 0, 0],
            [0, 1, 0],
            [g, hv, 1]
        ], dtype=np.float64)

    elif ttype == 'custom':
        return np.array(t.get('matrix', np.eye(3).tolist()), dtype=np.float64)

    return np.eye(3, dtype=np.float64)


def _describe_matrix(m):
    """Return a human-readable description of the matrix transform."""
    parts = []
    if abs(m[2, 0]) > 1e-6 or abs(m[2, 1]) > 1e-6:
        parts.append('Perspective')
    det = np.linalg.det(m)
    if det < -1e-6:
        parts.append('Reflection')
    if abs(m[0, 2]) > 0.5 or abs(m[1, 2]) > 0.5:
        parts.append('Translation')
    if abs(m[0, 1]) > 1e-6 or abs(m[1, 0]) > 1e-6:
        if abs(m[0, 1] + m[1, 0]) < 1e-4 and abs(m[0, 0] - m[1, 1]) < 1e-4:
            parts.append('Rotation')
        else:
            parts.append('Shear/Rotation')
    if abs(abs(m[0, 0]) - 1) > 1e-6 or abs(abs(m[1, 1]) - 1) > 1e-6:
        parts.append('Scale')
    if not parts:
        if np.allclose(m, np.eye(3)):
            return 'Identity'
        return 'Custom'
    return ' + '.join(parts)


if __name__ == '__main__':
    print('=' * 50)
    print('  Matrix Image Transformation Tool — Server')
    print('  Open http://127.0.0.1:5000 in your browser')
    print('=' * 50)
    app.run(host='127.0.0.1', port=5000, debug=True)

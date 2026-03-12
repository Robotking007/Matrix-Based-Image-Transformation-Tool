"""
cli.py — Command-Line Interface for Matrix Image Transformer

Usage:
    python cli.py input.png output.png --rotate 45
    python cli.py input.png output.png --scale 2 1.5
    python cli.py input.png output.png --translate 100 50
    python cli.py input.png output.png --shear 0.3 0
    python cli.py input.png output.png --reflect x
    python cli.py input.png output.png --perspective 0.001 0
    python cli.py input.png output.png --matrix "1,0,0,0,1,0,0,0,1"
    python cli.py input.png output.png --rotate 45 --scale 2 2 --translate 10 20
"""

import argparse
import sys
import numpy as np
import cv2

from python.matrix_engine import identity, multiply, determinant, is_affine, decompose_affine
from python.transform_engine import (
    apply_transform,
    rotation_matrix,
    scale_matrix,
    translation_matrix,
    shear_matrix,
    reflection_matrix,
    perspective_matrix,
    compute_bounding_box
)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Matrix-Based Image Transformation Tool — CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s photo.png rotated.png --rotate 90
  %(prog)s photo.png scaled.png --scale 0.5 0.5
  %(prog)s photo.png out.png --rotate 30 --scale 1.5 1.5 --translate 20 10
  %(prog)s photo.png out.png --matrix "0.87,-0.5,50,0.5,0.87,30,0,0,1"
  %(prog)s photo.png out.png --reflect x
  %(prog)s photo.png --info --matrix "1,0,0,0,1,0,0.001,0,1"
        """
    )

    parser.add_argument('input', help='Input image file path')
    parser.add_argument('output', nargs='?', default=None, help='Output image file path')

    # Transform options
    parser.add_argument('--rotate', type=float, metavar='DEG', help='Rotation angle in degrees (around center)')
    parser.add_argument('--scale', type=float, nargs=2, metavar=('SX', 'SY'), help='Scale factors (X, Y)')
    parser.add_argument('--translate', type=float, nargs=2, metavar=('TX', 'TY'), help='Translation in pixels (X, Y)')
    parser.add_argument('--shear', type=float, nargs=2, metavar=('KX', 'KY'), help='Shear factors (X, Y)')
    parser.add_argument('--reflect', choices=['x', 'y'], help='Reflection axis (x=horizontal, y=vertical)')
    parser.add_argument('--perspective', type=float, nargs=2, metavar=('G', 'H'), help='Perspective coefficients (g, h)')
    parser.add_argument('--matrix', type=str, help='Custom 3x3 matrix as 9 comma-separated values (row-major)')

    # Options
    parser.add_argument('--interpolation', choices=['nearest', 'bilinear', 'cubic'], default='bilinear',
                        help='Interpolation method (default: bilinear)')
    parser.add_argument('--info', action='store_true', help='Print matrix info without transforming')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed transformation info')

    return parser.parse_args()


def build_composed_matrix(args, w, h):
    """Build the final composed matrix from all CLI arguments."""
    transforms = []

    if args.matrix:
        values = [float(v.strip()) for v in args.matrix.split(',')]
        if len(values) != 9:
            print("Error: --matrix must have exactly 9 comma-separated values", file=sys.stderr)
            sys.exit(1)
        custom = np.array(values, dtype=np.float64).reshape(3, 3)
        transforms.append(('Custom', custom))

    if args.translate:
        tx, ty = args.translate
        m = translation_matrix(tx, ty)
        transforms.append((f'Translate({tx}, {ty})', m))

    if args.rotate:
        center = (w / 2, h / 2)
        rot_2x3 = rotation_matrix(args.rotate, center=center)
        m = np.vstack([rot_2x3, [0, 0, 1]])
        transforms.append((f'Rotate({args.rotate}°)', m))

    if args.scale:
        sx, sy = args.scale
        center = (w / 2, h / 2)
        m = scale_matrix(sx, sy, center=center)
        transforms.append((f'Scale({sx}, {sy})', m))

    if args.shear:
        kx, ky = args.shear
        m = shear_matrix(kx, ky)
        transforms.append((f'Shear({kx}, {ky})', m))

    if args.reflect:
        size = w if args.reflect == 'x' else h
        m = reflection_matrix(args.reflect, size)
        transforms.append((f'Reflect({args.reflect})', m))

    if args.perspective:
        g, hp = args.perspective
        m = perspective_matrix(g, hp)
        transforms.append((f'Perspective({g}, {hp})', m))

    if not transforms:
        return identity(), []

    # Compose: apply in order (first transform applied first)
    composed = identity()
    for name, m in transforms:
        composed = m @ composed

    return composed, transforms


def print_matrix_info(matrix, transforms=None):
    """Print detailed info about the transformation matrix."""
    det = determinant(matrix)
    affine = is_affine(matrix)

    print("\n╔══════════════════════════════════════════╗")
    print("║     Matrix Transformation Analysis       ║")
    print("╚══════════════════════════════════════════╝\n")

    if transforms:
        print("Applied transforms:")
        for i, (name, _) in enumerate(transforms, 1):
            print(f"  {i}. {name}")
        print()

    print("Composed matrix:")
    for row in range(3):
        vals = [f"{matrix[row, col]:10.6f}" for col in range(3)]
        bracket = "│" if row == 1 else ("┌" if row == 0 else "└")
        bracket_r = "│" if row == 1 else ("┐" if row == 0 else "┘")
        print(f"  {bracket} {vals[0]}  {vals[1]}  {vals[2]} {bracket_r}")

    print(f"\n  Determinant:  {det:+.6f}")
    print(f"  Type:         {'Affine' if affine else 'Perspective'}")
    print(f"  Invertible:   {'Yes' if abs(det) > 1e-10 else 'No'}")

    if affine:
        decomp = decompose_affine(matrix)
        print(f"\n  Decomposition:")
        print(f"    Translation: ({decomp['translation'][0]:.2f}, {decomp['translation'][1]:.2f})")
        print(f"    Rotation:    {decomp['rotation_deg']:.2f}°")
        print(f"    Scale:       ({decomp['scale'][0]:.4f}, {decomp['scale'][1]:.4f})")
        print(f"    Shear:       {decomp['shear']:.4f}")

    if abs(det) > 1e-10:
        inv = np.linalg.inv(matrix)
        print(f"\n  Inverse matrix:")
        for row in range(3):
            vals = [f"{inv[row, col]:10.6f}" for col in range(3)]
            bracket = "│" if row == 1 else ("┌" if row == 0 else "└")
            bracket_r = "│" if row == 1 else ("┐" if row == 0 else "┘")
            print(f"  {bracket} {vals[0]}  {vals[1]}  {vals[2]} {bracket_r}")

    print()


def main():
    args = parse_args()

    # Load input image
    image = cv2.imread(args.input, cv2.IMREAD_UNCHANGED)
    if image is None:
        print(f"Error: Could not load image '{args.input}'", file=sys.stderr)
        sys.exit(1)

    h, w = image.shape[:2]
    channels = image.shape[2] if image.ndim == 3 else 1

    if args.verbose:
        print(f"Input: {args.input} ({w}×{h}, {channels} channels)")

    # Build transformation
    matrix, transforms = build_composed_matrix(args, w, h)

    # Info mode
    if args.info:
        print_matrix_info(matrix, transforms)
        return

    # Check output path
    if args.output is None:
        print("Error: Output path required (or use --info for analysis only)", file=sys.stderr)
        sys.exit(1)

    # Apply transform
    if args.verbose:
        print_matrix_info(matrix, transforms)
        bbox = compute_bounding_box(matrix, w, h)
        print(f"  Output bounding box: {bbox[2]}×{bbox[3]} at ({bbox[0]}, {bbox[1]})\n")

    result = apply_transform(image, matrix, interpolation=args.interpolation)

    # Save
    cv2.imwrite(args.output, result)
    if args.verbose or True:
        print(f"Output saved: {args.output} ({result.shape[1]}×{result.shape[0]})")


if __name__ == '__main__':
    main()

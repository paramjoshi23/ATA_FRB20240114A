#!/usr/bin/env python3
"""
Combine multiple PNG files into a collage for publication.

Usage:
    python create_png_collage.py output.png image1.png image2.png image3.png ...
    
    Or modify the script to specify your image list directly.
"""

import sys
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math


def create_collage(image_paths, output_path, layout=None, spacing=10, 
                   add_labels=False, label_font_size=20, img_size=None):
    """
    Create a collage from multiple images.
    
    Args:
        image_paths: List of paths to PNG files
        output_path: Output path for the collage
        layout: Tuple (rows, cols) or None for auto layout
        spacing: Pixel spacing between images
        add_labels: Whether to add image filenames as labels
        label_font_size: Size of label text
        img_size: Size of each image in pixels. If None, keep original sizes.
    """
    
    # Load all images
    images = []
    for path in image_paths:
        img = Image.open(path)
        images.append((img, Path(path).stem))
    
    if not images:
        print("No images found!")
        return
    
    # Determine layout if not specified
    if layout is None:
        n_images = len(images)
        cols = math.ceil(math.sqrt(n_images))
        rows = math.ceil(n_images / cols)
    else:
        rows, cols = layout
    
    # Resize images to uniform size if img_size provided; otherwise keep originals
    resized_images = []
    if img_size is None:
        for img, label in images:
            resized_images.append((img.copy(), label))
    else:
        img_width = img_size
        img_height = img_size
        for img, label in images:
            im = img.copy()
            im.thumbnail((img_width, img_height), Image.Resampling.LANCZOS)
            resized_images.append((im, label))
    
    # Calculate canvas size using actual resized image sizes so packing is tight
    label_height = label_font_size + 10 if add_labels else 0

    # Get actual sizes of resized images
    sizes = []  # list of (w, h_with_label)
    for img, label in resized_images:
        w, h = img.size
        h_with_label = h + (label_height if add_labels else 0)
        sizes.append((w, h_with_label))

    # Compute max width per column and max height per row
    col_widths = [0] * cols
    row_heights = [0] * rows
    for idx, (w, h) in enumerate(sizes):
        r = idx // cols
        c = idx % cols
        if w > col_widths[c]:
            col_widths[c] = w
        if h > row_heights[r]:
            row_heights[r] = h

    canvas_width = sum(col_widths) + (cols - 1) * spacing
    canvas_height = sum(row_heights) + (rows - 1) * spacing

    # Create canvas
    canvas = Image.new('RGB', (canvas_width, canvas_height), color='white')

    # Paste images onto canvas using column widths and row heights
    x_offsets = []
    x = 0
    for c_w in col_widths:
        x_offsets.append(x)
        x += c_w + spacing

    y_offsets = []
    y = 0
    for r_h in row_heights:
        y_offsets.append(y)
        y += r_h + spacing

    for idx, (img, label) in enumerate(resized_images):
        row = idx // cols
        col = idx % cols

        x = x_offsets[col]
        y = y_offsets[row]

        # Paste image (left-aligned in its column)
        canvas.paste(img, (x, y))

        # Add label if requested
        if add_labels:
            draw = ImageDraw.Draw(canvas)
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 
                                         label_font_size)
            except:
                font = ImageFont.load_default()

            label_y = y + img.size[1] + 5
            draw.text((x, label_y), label, fill='black', font=font)
    
    # Save collage
    canvas.save(output_path)
    print(f"Collage saved to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Create a collage from multiple PNG files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python create_png_collage.py output.png image1.png image2.png image3.png
  python create_png_collage.py output.png --layout 1 5 image1.png image2.png image3.png
  python create_png_collage.py output.png --spacing 20 image1.png image2.png
        """
    )
    
    parser.add_argument('output', help='Output collage filename')
    parser.add_argument('images', nargs='*', help='PNG image files to combine')
    parser.add_argument('--dir', dest='dirpath', default=None,
                       help='Directory containing PNG files to include (non-recursive)')
    parser.add_argument('--layout', type=int, nargs=2, metavar=('ROWS', 'COLS'), 
                       help='Layout as rows cols (e.g., 1 5 for 1 row, 5 columns)')
    parser.add_argument('--spacing', type=int, default=10, 
                       help='Spacing between images in pixels (default: 10)')
    parser.add_argument('--img-size', type=int, default=600,
                       help='Size of each image in pixels (default: 600)')
    parser.add_argument('--labels', action='store_true', 
                       help='Add image filenames as labels')
    parser.add_argument('--label-size', type=int, default=16,
                       help='Label font size (default: 16)')
    
    args = parser.parse_args()
    
    layout = tuple(args.layout) if args.layout else None

    # Build list of image files from --dir and positional images
    images = []
    if args.dirpath:
        p = Path(args.dirpath)
        if not p.is_dir():
            parser.error(f"--dir path does not exist or is not a directory: {args.dirpath}")
        # Collect PNGs (case-insensitive), sorted
        pngs = sorted([str(x) for x in p.iterdir() if x.is_file() and x.suffix.lower() == '.png'])
        images.extend(pngs)

    # Positional image files (explicit list) come after directory files
    if args.images:
        images.extend(args.images)

    if not images:
        parser.error('No images provided. Pass filenames or use --dir to point to a directory of PNGs.')

    create_collage(
        images,
        args.output,
        layout=layout,
        spacing=args.spacing,
        add_labels=args.labels,
        label_font_size=args.label_size,
        img_size=args.img_size
    )

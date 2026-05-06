# imgtoolkit

A powerful Python toolkit for image processing, specializing in finding duplicate and blurry images. This tool helps you organize your image collections by identifying and managing duplicate images and detecting low-quality or blurry photos.

## Features

- **Find Duplicate Images**: Uses perceptual hashing (dhash) to identify visually identical images
- **Detect Blurry Images**: Identifies and separates blurry or low-quality images
- **Remove Fake PNG Backgrounds**: Converts fake transparent PNG images to true transparent PNGs
- **Multi-format Support**: Works with various image formats (JPG, JPEG, PNG, BMP, TIFF)
- **Configurable**: Supports JSON configuration files for customized settings
- **Parallel Processing**: Uses multiprocessing for improved performance
- **Progress Tracking**: Shows progress bars for long-running operations

## Installation

```bash
pip install imgtoolkit
```

### Upgrade to the Latest Version

```bash
pip install --upgrade imgtoolkit
```

## Usage

### Command Line Interface

```bash
# Show help
imgtoolkit --help

# Default run (no subcommand): find blurry images, then duplicates
imgtoolkit

# Find duplicate images only
imgtoolkit find-duplicates [--folder OUTPUT_FOLDER] [--prefix PREFIX] [--formats jpg png]

# Find blurry images only
imgtoolkit find-blur [--folder OUTPUT_FOLDER] [--threshold BLUR_THRESHOLD] [--formats jpg png]

# Remove duplicate prefix from images
imgtoolkit remove-duplicate-prefix FOLDER [--prefix PREFIX]

# Remove fake transparent background from PNG
imgtoolkit remove-fakepng-bg SOURCE_PNG DESTINATION_PNG

# Show version
imgtoolkit version
```

### Using Configuration File

Create a JSON configuration file (e.g., `config.json`):

```json
{
    "duplicate": {
        "folder": "duplicates/",
        "prefix": "DUP_",
        "formats": ["jpg", "png"]
    },
    "blur": {
        "folder": "blurry/",
        "threshold": 5.0,
        "formats": ["jpg", "png"]
    }
}
```

Then run with the config file:

```bash
imgtoolkit --config config.json find-duplicates
imgtoolkit --config config.json find-blur
```

## Command Options

### find-duplicates
- `--folder`: Output folder for duplicate images (default: "duplicate/")
- `--prefix`: Prefix for marking duplicate files (default: "DUPLICATED_")
- `--formats`: List of image formats to process (default: jpg, jpeg, png)

### find-blur
- `--folder`: Output folder for blurry images (default: "blur/")
- `--threshold`: Blur detection threshold (default: 5.0, lower = more blurry). The detector combines a frequency-domain sharpness score with edge strength (Tenengrad) to reduce false positives on detailed images.
- `--formats`: List of image formats to process (default: jpg, jpeg, png)
- During the scan, any JPEG files that are unreadable/truncated (e.g. triggering "Premature end of JPEG file") are moved to a `broken/` subfolder.

### Blur Detection Technology and Techniques
- **Core stack**: Implemented in Python using `OpenCV (cv2)` for image processing and `NumPy` for matrix/FFT operations.
- **Frequency-domain sharpness (FFT)**: The image is converted to grayscale, center-cropped, resized to `512x512`, transformed by 2D FFT, then scored by `high-frequency energy / low-frequency energy` (scaled by `x1000`). Lower score means less fine detail, so more likely blur.
- **Edge-strength validation (Tenengrad)**: Sobel gradients are used to compute gradient energy (Tenengrad). This avoids false positives where FFT score is low but the image still has strong edges and visible detail.
- **Final decision rule**: An image is classified as blurry only when both signals are weak: low FFT score and low Tenengrad.
- **Robust file handling**: During `find-blur`, zero-byte files are deleted immediately, and corrupted/truncated JPEGs are moved to the `broken/` folder so the scan can continue.

### remove-duplicate-prefix
- `folder`: The folder containing marked duplicate images
- `--prefix`: Prefix to remove from filenames (default: "DUPLICATED_")

### remove-fakepng-bg
- `src`: Source PNG file with fake transparent background
- `dst`: Destination path for the fixed PNG file

## Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- TIFF (.tiff)

## Requirements

- Python 3.6+
- OpenCV (cv2)
- Pillow
- dhash
- numpy
- alive-progress

## Error Handling

The toolkit provides clear error messages for common issues:
- Invalid image formats
- Missing or inaccessible files
- Processing errors
- Invalid configuration

## Development

To contribute to imgtoolkit:

1. Clone the repository
2. Install development dependencies:
```bash
pip install -e ".[dev]"
```
3. Run tests:
```bash
pytest
```

## Version History
**v0.1.8**
Improved Find Blurry Image logic

**v0.1.3**
Resolved a bug of handling incomplete / corrupted image files

**v0.1.2**
Revamp the command structure, adding features of remove fake PNG backgrounds

## License

MIT License - See LICENSE file for details.

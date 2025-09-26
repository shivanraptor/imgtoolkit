import dhash
import glob
import os
import cv2
import numpy as np
import warnings
import sys
from math import ceil
from PIL import Image, ImageDraw, ImageFile, UnidentifiedImageError
from timeit import default_timer as timer
from datetime import timedelta
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager
from alive_progress import alive_bar
from itertools import chain
from pathlib import Path
from importlib.metadata import version
from argparse import ArgumentParser
from typing import Set, Dict, Any, Optional
import json

# Avoid OSError :  image file is truncated hashing error
ImageFile.LOAD_TRUNCATED_IMAGES = True

warnings.simplefilter('ignore', Image.DecompressionBombWarning)

IMG_FILTER = '*.jpg'
FOLDER_DUP = 'duplicate/'
FOLDER_BLUR = 'blur/'
DUP_PREFIX = 'DUPLICATED_'

debug_flag = False

# Supported image formats
SUPPORTED_FORMATS = {
    'jpg': '*.jpg',
    'jpeg': '*.jpeg',
    'png': '*.png',
    'bmp': '*.bmp',
    'tiff': '*.tiff'
}

class ImageToolkitError(Exception):
    """Base exception class for ImageToolkit errors."""
    pass

# Main Functions
def find_duplicate(folder: str = FOLDER_DUP, prefix: str = DUP_PREFIX, formats: Optional[list[str]] = None) -> None:
    """Find and move duplicate images to a specified folder.
    
    Args:
        folder: Directory where duplicate images will be moved
        prefix: Prefix to add to duplicate image filenames
        formats: List of image formats to process (e.g. ['jpg', 'png'])
        
    Raises:
        ImageToolkitError: If no valid images found or processing fails
        OSError: If folder creation or file operations fail
    """
    print("Start finding duplicates")
    try:
        if os.path.exists(folder) and listdir_nohidden(folder):
            raise ImageToolkitError("Duplicate folder exists and not empty")
            
        start = timer()
        with Manager() as manager:
            print("Phase 1 - Hashing")
            d = manager.dict()
            images = get_image_files(formats)
            
            if not images:
                raise ImageToolkitError("No valid image files found")
                
            total = len(images)
            with alive_bar(total) as bar, ProcessPoolExecutor() as executor:
                for ex in executor.map(makehash, [(jpg, d) for jpg in images]):
                    bar()

            print("Phase 2 - Find Duplicates")
            duplicates = process_duplicate(d)
            create_dir(folder)
            print("Phase 3 - Move Duplicates")
            move_duplicates(duplicates, folder, prefix)
            
        end = timer()
        print_elapsed(end-start)
        
    except (OSError, UnidentifiedImageError) as e:
        raise ImageToolkitError(f"Error processing images: {str(e)}")


def find_blur(folder: str = FOLDER_BLUR, threshold: int = 20, formats: Optional[list[str]] = None) -> None:
    """Detect and move blurry images to a specified folder.
    
    Args:
        folder: Directory where blurry images will be moved
        threshold: Laplacian variance threshold for blur detection (lower = more blurry)
        formats: List of image formats to process (e.g. ['jpg', 'png'])
        
    Raises:
        ImageToolkitError: If no valid images found or processing fails
        OSError: If folder creation or file operations fail
    """
    print("Start finding blurs")
    try:
        if os.path.exists(folder) and listdir_nohidden(folder):
            raise ImageToolkitError("Blur folder exists and not empty")

        start = timer()
        imgs = get_image_files(formats)
        
        if not imgs:
            raise ImageToolkitError("No valid image files found")

        cnt = 0
        create_dir(folder)
        with alive_bar(len(imgs)) as bar:
            for i in imgs:
                try:
                    img = cv2.imread(i)
                    if img is None:
                        print(f"Warning: Could not load image {i}")
                        continue
                        
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    val = np.max(cv2.convertScaleAbs(cv2.Laplacian(gray, 3)))
                    if(val < threshold):
                        cnt += 1
                        os.rename(i, folder + i)
                except cv2.error as e:
                    print(f"Warning: Error processing image {i}: {str(e)}")
                bar()

        print(cnt, "blur photos processed, moved to " + folder)
        end = timer()
        print_elapsed(end-start)
        
    except Exception as e:
        raise ImageToolkitError(f"Error processing images: {str(e)}")

def remove_duplicate_prefix(folder: str = FOLDER_DUP, prefix: str = DUP_PREFIX):
    if hasattr(folder, "folder"):
        folder = vars(folder).get("folder")
    
    print("Working folder:", os.path.join(folder, IMG_FILTER))
    if os.path.exists(folder) and listdir_nohidden(folder):
        start = timer()
        imgs = glob.glob(os.path.join(folder, IMG_FILTER))
        cnt = 0
        with alive_bar(len(list(imgs))) as bar:
            for i in imgs:
                os.rename(i, i.replace(DUP_PREFIX, ''))
                cnt += 1
        end = timer()
        print(cnt, "images have been renamed.")
    else:
        print("Nothing to rename")

def analyze_blur(target_folder: str = '.'):
    start = timer()

    path = Path(target_folder, IMG_FILTER)
    print("Start analyzing blur at path: " + target_folder)
    imgs = glob.glob(path.as_posix())
    with alive_bar(len(list(imgs))) as bar:
        for i in imgs:
            img = cv2.imread(i)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            val = np.max(cv2.convertScaleAbs(cv2.Laplacian(gray, 3)))
            print(str(i), "Blur Value: " + str(val))
            bar()

    end = timer()
    print_elapsed(end-start)

def fakepng_removebg(config):
    imgpath = config.src
    savepath = config.dst
    if not os.path.exists(imgpath):
        raise ValueError("ERROR: The input file does not exist, or cannot be read.")

    # ========================
    # Step 1: Detect Tile Size
    # ========================
    # TODO: Read from command line / input file name
    original = cv2.imread(imgpath, cv2.IMREAD_UNCHANGED)
    h, w, *_ = original.shape

    # get the left top pixel color
    color = original[0][0]

    checker_size_x = 0
    checker_size_y = 0

    checker_color1 = tuple(color)
    checker_color2 = (255, 255, 255)

    offset_x = 0
    offset_y = 0

    for x in range(w):
        next_color = original[0][x]
        if next_color[0] != color[0]:
            # color changed
            checker_size_x = x
            offset_x = x
            checker_color2 = next_color # Assume the first row of the image has checker
            break

    for y in range(h):
        next_color = original[y][0]
        if next_color[0] != color[0]:
            # color changed
            checker_size_y = y
            offset_y = y
            break

    # if the checker is a square
    if checker_size_x == checker_size_y:
        # ========================
    	# Step 2: Generate Tilemap
    	# ========================
        image_w = ceil(w / checker_size_x) * checker_size_x
        image_h = ceil(h / checker_size_x) * checker_size_x

        checkerboard = Image.new("RGB", (image_w, image_h), (255, 0, 0))
        pixels = checkerboard.load()

        for i in range (0, image_w, checker_size_x):
            for j in range(0, image_h, checker_size_x):
                y, x = i // checker_size_x, j // checker_size_x
                if (y&1)^(x&1):
                    for di in range(checker_size_x):
                        for dj in range(checker_size_x):
                            pixels[i+di, j+dj] = tuple(checker_color2)
                else:
                    for di in range(checker_size_x):
                        for dj in range(checker_size_x):
                            pixels[i+di, j+dj] = tuple(checker_color1)

        checkerboard.save('checkerboard.png')
        start_x = checker_size_x - offset_x
        start_y = checker_size_x - offset_y
        checkerboard = checkerboard.crop((start_x, start_y, w + start_x, h + start_y))

    	# ========================
    	# Step 3: Subtract Tilemap
    	# ========================
        # convert Pillow image to OpenCV format
        tiled = cv2.cvtColor(np.array(checkerboard), cv2.COLOR_RGB2BGR)
        subtract = cv2.subtract(tiled, original)

    	# inverting the color
        subtract = ~subtract
        #cv2.imwrite('subtract.png', subtract)

    	# ========================
    	# Step 4: Add Alpha Channel
    	# ========================
        # TODO: Make the colors optional input parameters
        # The color range is commonly used in the checkboard of fake transparent PNGs
        mask = cv2.inRange(subtract, (253, 253, 253), (255, 255, 255))
        #cv2.imwrite('mask.png', mask)

    	# convert the source to RGBA Color Space to enable Alpha channel
        rgba = cv2.cvtColor(original, cv2.COLOR_RGB2RGBA)
        rgba[mask > 0] = (0, 0, 0, 0)

    	# Writing and saving the final results to a new image
        cv2.imwrite(savepath, rgba)
        print('Done! Fixed image is saved at', savepath)
        os.remove('checkerboard.png')
    else:
        raise ValueError("ERROR: Checker size is not square. Please check.")


# Support Functions
def process_duplicate(file_list: Dict[str, str]) -> Set[str]:
    """Process a dictionary of file hashes to find duplicates.
    
    Args:
        file_list: Dictionary mapping filenames to their dhash values
        
    Returns:
        Set of filenames that are duplicates
    """
    rev_dict = {}
    for key, value in file_list.items():
        rev_dict.setdefault(value, set()).add(key)
    result = set(chain.from_iterable(
        values for key, values in rev_dict.items() if len(values) > 1))
    return result


def listdir_nohidden(path):
    return glob.glob(os.path.join(path, '*'))


def create_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def move_duplicates(dups, folder, prefix):
    cnt = 0
    for i in dups:
        os.rename(i, folder + prefix + i.replace('./', ''))
        cnt += 1
    print(cnt, "duplicated images moved to " + folder)


def makehash(t: tuple[str, Any]) -> None:
    """Generate a dhash for an image file.
    
    Args:
        t: Tuple containing (filename, shared_dict)
        
    Raises:
        PIL.UnidentifiedImageError: If image format cannot be identified
        OSError: If image file cannot be opened
    """
    filename, d = t
    with Image.open(filename) as image:
        image.draft('L', (32, 32))
        row, col = dhash.dhash_row_col(image)
        d[filename] = dhash.format_hex(row, col)


def print_elapsed(sec):
    print("Elapsed Time: ", timedelta(seconds=sec))


def show_version(config):
    print("imgtoolkit " + version("imgtoolkit"))

def set_debug(value):
    if type(value) == bool:
        if value is True:
            sys.excepthook = exception_handler
        else:
            sys.excepthook = exception_handler_simple
    else:
        raise ValueError("set_debug() input parameter is not Boolean.")

DEFAULT_CONFIG = {
    'duplicate': {
        'folder': FOLDER_DUP,
        'prefix': DUP_PREFIX,
        'formats': ['jpg', 'jpeg', 'png']
    },
    'blur': {
        'folder': FOLDER_BLUR,
        'threshold': 20,
        'formats': ['jpg', 'jpeg', 'png']
    }
}

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file or return defaults.
    
    Args:
        config_path: Path to JSON config file
        
    Returns:
        Configuration dictionary
    """
    if config_path and Path(config_path).exists():
        with open(config_path) as f:
            user_config = json.load(f)
            # Merge with defaults
            config = DEFAULT_CONFIG.copy()
            config.update(user_config)
            return config
    return DEFAULT_CONFIG

def main():
    print("Image Toolkit", version("imgtoolkit"), "loaded")

    parser = ArgumentParser(description='Image processing toolkit for finding duplicates and blurry images')
    parser.add_argument('--config', help='Path to configuration file')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # version
    parser_version = subparsers.add_parser('version', help='Show version')
    parser_version.set_defaults(func=show_version)

    # find duplicates
    parser_find_dup = subparsers.add_parser('find-duplicates', help='Find and move duplicate images')
    parser_find_dup.add_argument('--folder', help='Output folder for duplicates')
    parser_find_dup.add_argument('--prefix', help='Prefix for duplicate files')
    parser_find_dup.add_argument('--formats', nargs='+', help='Image formats to process (e.g. jpg png)')
    
    # find blur
    parser_find_blur = subparsers.add_parser('find-blur', help='Find and move blurry images')
    parser_find_blur.add_argument('--folder', help='Output folder for blurry images')
    parser_find_blur.add_argument('--threshold', type=int, help='Blur detection threshold')
    parser_find_blur.add_argument('--formats', nargs='+', help='Image formats to process (e.g. jpg png)')

    # remove_duplicate_prefix
    parser_remove_dup_prefix = subparsers.add_parser('remove-duplicate-prefix', help='Remove duplicated image prefix')
    parser_remove_dup_prefix.add_argument('folder', help='The folder containing marked duplicate images')
    parser_remove_dup_prefix.add_argument('--prefix', help='Prefix to remove')

    # remove fake background
    parser_fakepng = subparsers.add_parser('remove-fakepng-bg', help='Remove fake transparent background from PNG')
    parser_fakepng.add_argument('src', help='Source PNG file')
    parser_fakepng.add_argument('dst', help='Destination file path')

    args = parser.parse_args()
    config = load_config(args.config if hasattr(args, 'config') else None)

    try:
        if args.command == 'find-duplicates':
            dup_config = config['duplicate']
            find_duplicate(
                folder=args.folder or dup_config['folder'],
                prefix=args.prefix or dup_config['prefix'],
                formats=args.formats or dup_config['formats']
            )
        elif args.command == 'find-blur':
            blur_config = config['blur']
            find_blur(
                folder=args.folder or blur_config['folder'],
                threshold=args.threshold or blur_config['threshold'],
                formats=args.formats or blur_config['formats']
            )
        elif args.command == 'remove-duplicate-prefix':
            remove_duplicate_prefix(args.folder, args.prefix or DUP_PREFIX)
        elif args.command == 'remove-fakepng-bg':
            fakepng_removebg(args)
        elif args.command == 'version':
            show_version(args)
        else:
            parser.print_help()
    except ImageToolkitError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        if debug_flag:
            raise
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)

def exception_handler(exception_type, exception, traceback):
    if issubclass(exception_type, KeyboardInterrupt):
        sys.__excepthook__(exception_type, exception, traceback)
        return

    print(exception_type.__name__,": ", exception)
    print(traceback)

def exception_handler_simple(exception_type, exception, traceback):
    if issubclass(exception_type, KeyboardInterrupt):
        sys.__excepthook__(exception_type, exception, traceback)
        return

    print(exception_type.__name__,": ", exception)

# default exception handler
sys.excepthook = exception_handler_simple

def get_image_files(formats: Optional[list[str]] = None) -> list[str]:
    """Get list of image files in supported formats.
    
    Args:
        formats: List of formats to include (e.g. ['jpg', 'png']). If None, includes all supported formats.
    
    Returns:
        List of image file paths
    """
    if formats is None:
        formats = SUPPORTED_FORMATS.keys()
    
    patterns = [SUPPORTED_FORMATS[fmt] for fmt in formats if fmt in SUPPORTED_FORMATS]
    if not patterns:
        raise ImageToolkitError("No valid image formats specified")
        
    images = []
    for pattern in patterns:
        images.extend(glob.glob(pattern))
    return images

if __name__ == '__main__':
    main()

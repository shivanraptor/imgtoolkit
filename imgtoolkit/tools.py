import dhash
import glob
import os
import cv2
import numpy as np
import warnings
import sys
from math import ceil
from PIL import Image, ImageDraw
from timeit import default_timer as timer
from datetime import timedelta
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager
from alive_progress import alive_bar
from itertools import chain
from pathlib import Path
from importlib.metadata import version
from argparse import ArgumentParser


warnings.simplefilter('ignore', Image.DecompressionBombWarning)

IMG_FILTER = '*.jpg'
FOLDER_DUP = 'duplicate/'
FOLDER_BLUR = 'blur/'
DUP_PREFIX = 'DUPLICATED_'

debug_flag = False

# Main Functions
def find_duplicate(folder: str = FOLDER_DUP, prefix: str = DUP_PREFIX):
    print("Start finding duplicates")
    if os.path.exists(folder) and listdir_nohidden(folder):
        print("ERROR: Duplicate folder exists and not empty. Halting")
    else:
        start = timer()
        with Manager() as manager:
            print("Phase 1 - Hashing")
            d = manager.dict()
            images = glob.glob(IMG_FILTER)
            total = len(list(images))
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


def find_blur(folder: str = FOLDER_BLUR, threshold: int = 20):
    print("Start finding blurs")
    if os.path.exists(folder) and listdir_nohidden(folder):
        print("ERROR: Blur folder exists and not empty. Halting")
    else:
        start = timer()

        imgs = glob.glob(IMG_FILTER)
        cnt = 0
        create_dir(folder)
        with alive_bar(len(list(imgs))) as bar:
            for i in imgs:
                img = cv2.imread(i)
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                val = np.max(cv2.convertScaleAbs(cv2.Laplacian(gray, 3)))
                if(val < threshold):
                    cnt += 1
                    os.rename(i, folder + i)
                bar()

        print(cnt, "blur photos processed, moved to " + folder)

        end = timer()
        print_elapsed(end-start)

def remove_duplicate_prefix(folder: str = FOLDER_DUP, prefix: str = DUP_PREFIX):
    if os.path.exists(folder) and listdir_nohidden(folder):
        start = timer()
        imgs = glob.glob(FOLDER_DUP + IMG_FILTER)
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
def process_duplicate(file_list):
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


def makehash(t):
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

def main():
    print("Image Toolkit", version("imgtoolkit"), "loaded")

    parser = ArgumentParser()
    subparsers = parser.add_subparsers()

    # version
    parser_version = subparsers.add_parser('version', help='Show version')
    parser_version.set_defaults(func=show_version)

    # remove_duplciate_prefix
    parser_remove_dup_prefix = subparsers.add_parser('remove_duplicate_prefix', help='Remove duplicated image prefix')
    parser_remove_dup_prefix.set_defaults(func=remove_duplicate_prefix)

    # remove fake background
    parser_fakepng = subparsers.add_parser('remove_fakepng_bg')
    parser_fakepng.add_argument('src', help='The PNG path with fake transparent background')
    parser_fakepng.add_argument('dst', help='The path to save the edited image')
    parser_fakepng.set_defaults(func=fakepng_removebg)
    
    if len(sys.argv) <= 1:
        find_blur()
        find_duplicate()
    else:
        args = parser.parse_args()
        args.func(args)

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
if __name__ == '__main__':
    main()

import dhash
import glob
import os
import cv2
import numpy
import warnings
from PIL import Image
from timeit import default_timer as timer
from datetime import timedelta
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager
from alive_progress import alive_bar
from itertools import chain

warnings.simplefilter('ignore', Image.DecompressionBombWarning)

IMG_FILTER = '*.jpg'
FOLDER_DUP = 'duplicate/'
FOLDER_BLUR = 'blur/'
DUP_PREFIX = 'DUPLICATED_'


# Main Functions
def find_duplicate(folder: str = FOLDER_DUP, prefix: str = DUP_PREFIX):
    print("Start finding duplicates")
    if os.path.exists(folder) and listdir_nohidden(folder):
        print("ERROR: Blur folder exists and not empty. Halting")
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
                val = numpy.max(cv2.convertScaleAbs(cv2.Laplacian(gray, 3)))
                if(val < threshold):
                    cnt += 1
                    os.rename(i, folder + i)
                bar()

        print(cnt, "blur photos processed, moved to " + folder)

        end = timer()
        print_elapsed(end-start)


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


def main():
    print("Image Toolkit loaded")


if __name__ == '__main__':
    main()

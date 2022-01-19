# Image Toolkit

This is an image tool package for organizing photos. Main features are:

- **Find visually duplicated photos**: by comparing the photo hashes, the script can identify visually identical photos
- **Find blurred photos**: by calculating Laplacian value of the photos, the script can also identify blurred photos

Note: Only JPEG images are tested and supported at this version.

## Basic Usage

```
from imgtoolkit import tools

if __name__ == '__main__':
  # Find blur photos
	tools.find_blur()

  # Find duplicated photos
	tools.find_duplicate()
```

**Sample Output**

```
Start finding blurs
|████████████████████████████████████████| 12148/12148 [100%] in 18:38.0 (10.87/s)
11 blur photos processed, moved to blur/
Elapsed Time:  0:18:38.067728
Start finding duplicates
Phase 1 - Hashing
|████████████████████████████████████████| 12137/12137 [100%] in 2:25.1 (83.63/s)
Phase 2 - Find Duplicates
Phase 3 - Move Duplicates
93 duplicated images moved to duplicate/
```

## Parameters
```
find_blur(folder='blur/', threshold=20)
```
- `folder` (string): the script will create a folder with specified name and move blurred photos to the folder.
- `threshold` (integer): the lower the value, the stricter the check. The default value 20 is generally okay for most cases.

```
find_duplicate(folder='duplicate/', prefix='DUPLICATED_')
```
- `folder` (string): the script will create a folder with specified name and move duplicated photos to the folder.
- `prefix` (string): the script will append the prefix to the filename when moving to the duplicate folder. Set it to empty string to avoid this behavior.

## Installation

If you have installed `pip`, you can install this package via this command:

```
pip install imgtoolkit
```

## Questions or Suggestions

Please open an issue if you find problems using this script. Suggestions or feature requests are also welcomed.

## Donation

Donations are welcomed. We accept ETH or SOL.

ETH: 0x5B3318109932c8EDc6297197895afDD68567672D
SOL: GLBLjrYxhbncTFR6CbRTrpPjtaNJax13A82C8F3ceSAX

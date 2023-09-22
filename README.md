# Image Toolkit v0.1.1

This is an image tool package for organizing photos. The main features are:

- **Find visually duplicated photos**: by comparing the photo hashes, the script can identify visually identical photos
- **Find blurred photos**: by calculating Laplacian value of the photos, the script can also identify blurred photos
- **Remove fake transparent background**: we use various image processing methods to remove fake checkerboard transparent background
- **Remove duplicated images prefix**: after processing the duplicated photos, there is a prefix added to the duplicated images; you can use our tool to undo the renaming.

Note: For blurry and duplicated photo checks, only JPEG images are tested and supported in this version. For fake transparent background removal, we only support PNG at this moment.

## Basic Usage

### Function 1: Identify Blurry and Duplicated JPEG Images
In the command line, you can just use the following command:
```
imgtoolkit
```
Blurred and duplicated image checks on the current folder will be automatically executed; `blur` and `duplicate` folders will be created to store blurry and duplicated images.

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

### Function 2 (Available since v0.1.1): Remove Duplicated Images' Prefix (after using Function 1)
To remove the prefix of the duplicated images in the `duplicate` folder, you can execute the following command in the folder containing the `duplicate` folder:
```
imgtoolkit remove_duplicate_prefix
```

### Function 3 (Available since v0.1.1): Remove Fake PNG Background
To remove the fake PNG background, you can use the following command:
```
imgtoolkit remove_fakepng_bg source.png save.png
```
where `source.png` is the PNG that requires background removal, while `save.png` is the path you want to save the fixed image.

---

### Using Our Toolkit in Python

In Python, you can find blurry and duplicated photos as follows:
```
from imgtoolkit import tools

if __name__ == '__main__':
  # Find blur photos
	tools.find_blur()

  # Find duplicated photos
	tools.find_duplicate()
```

## Parameters used in Python
```
find_blur(folder='blur/', threshold=20)
```
- `folder` (string): the script will create a folder with a specified name and move blurred photos to the folder.
- `threshold` (integer): the lower the value, the stricter the check. The default value of 20 is generally okay for most cases.

```
find_duplicate(folder='duplicate/', prefix='DUPLICATED_')
```
- `folder` (string): the script will create a folder with the specified name and move duplicated photos to the folder.
- `prefix` (string): the script will append the prefix to the filename when moving to the duplicate folder. Set it to an empty string to avoid this behavior.

## Installation

If you have installed `pip`, you can install this package via this command:

```
pip install imgtoolkit
```

## Upgrade

To upgrade an existing installation, you can use the following command:
```
pip install imgtoolkit --upgrade
```

## Questions or Suggestions

Please open an issue if you find problems using this script. Suggestions or feature requests are also welcomed.

## Future Development

- More command line parameters

## Donation

Donations are welcomed. We accept ETH or SOL.

- ETH: 0x5B3318109932c8EDc6297197895afDD68567672D
- SOL: GLBLjrYxhbncTFR6CbRTrpPjtaNJax13A82C8F3ceSAX

import os
import tifffile
import numpy as np
import re

def numerical_sort(value):
    numbers = re.findall(r'\d+', value)
    return int(numbers[0]) if numbers else 0

def tiff_stacker(dir_path, output_path):
    # Get a list of all TIFF files in the directory
    tiff_files = [file for file in os.listdir(dir_path) if file.endswith('.tiff')]

    # Sort the TIFF files numerically
    tiff_files.sort(key=numerical_sort)

    # Read the first image to determine its shape and data type
    first_image = tifffile.imread(os.path.join(dir_path, tiff_files[0]))

    # Initialize an empty stack with appropriate dimensions and data type
    stack = np.zeros((len(tiff_files), first_image.shape[0], first_image.shape[1]), dtype=first_image.dtype)

    # Read each TIFF file and add it to the stack
    for i, tiff_file in enumerate(tiff_files):
        image = tifffile.imread(os.path.join(dir_path, tiff_file))
        stack[i] = image

    # Save the stack as a multi-image TIFF file
    tifffile.imwrite(output_path, stack)

    print(f"Multi-image TIFF stack saved at {output_path}")

input_dir = r"D:\WormSpy_video\ASH1_19-02-2025_17-11"
output_dir = r"D:\WormSpy_video\ASH1_19-02-2025_17-11"
for foldername in os.listdir(input_dir):
    input_path = os.path.join(input_dir, foldername)
    if os.path.isdir(input_path):  # Ensure input_path is a directory
        output_path = os.path.join(output_dir, 'BLUE_5_.tiff')
        tiff_stacker(input_path, output_path)
    else:
        print(f"{input_path} is not a directory")
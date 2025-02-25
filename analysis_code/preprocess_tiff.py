import os
import glob
import argparse
import tifffile
import numpy as np

def crop_image_around_max(image_array, crop_size):
    """
    Finds the brightest pixel in the image and crops a region of size crop_size x crop_size
    centered around it. Pads the image if necessary.
    """
    half = crop_size // 2

    # Pad the image to handle boundaries
    padded = np.pad(image_array, pad_width=half, mode="constant", constant_values=0)

    # Find the index of the maximum intensity in the original image
    max_idx = np.argmax(image_array)
    max_coords = np.unravel_index(max_idx, image_array.shape)
    row, col = max_coords

    # Adjust center coordinates for the padded image
    pad_row, pad_col = row + half, col + half

    # Crop the region from padded image
    cropped = padded[pad_row - half: pad_row + half,
                     pad_col - half: pad_col + half]
    return cropped

def process_images(input_folder, output_folder):
    # Make sure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Get all tiff files in the input folder
    pattern = os.path.join(input_folder, "*.tiff")
    image_files = glob.glob(pattern)
    
    if not image_files:
        print("No .tiff files found in the provided folder.")
        return

    for image_file in image_files:
        print(f"Processing: {image_file}")
        
        # Open the image using tifffile
        img = tifffile.imread(image_file)
        img = img.astype(np.uint16)
        img_array = np.array(img)
        
        # Crop the image around the brightest pixel
        cropped_array = crop_image_around_max(img_array, crop_size=80)
        
        # Save as an uncompressed 16-bit TIFF file using tifffile
        basename = os.path.basename(image_file)
        output_path = os.path.join(output_folder, basename)
        tifffile.imwrite(output_path, cropped_array.astype(np.uint16), compression=None)
    
    print(f"Processing complete. Cropped images saved to {output_folder}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pre-process .tiff images by cropping around the brightest pixel and saving as uncompressed 16-bit TIFF files.")
    parser.add_argument("input_folder", help="Path to the folder containing .tiff images")
    args = parser.parse_args()
    
    output_folder = os.path.join(args.input_folder, "cropped")
    process_images(args.input_folder, output_folder)
import os
import glob
import argparse
import tifffile
import numpy as np
import cv2
from skimage.filters import threshold_yen
from skimage.measure import label, regionprops

def crop_image_around_brightest_object(image_array, crop_size):
    """
    Finds the brightest object (at least min_object_size pixels) in the image
    and crops a region of size crop_size x crop_size centered around its centroid.
    """
    half = crop_size // 2
    min_object_size = 10
    
    # Check for extreme values and clip if necessary
    min_val = image_array.min()
    max_val = image_array.max()
    
    if max_val > 65535:
        print(f"Warning: Image contains extreme values: min={min_val}, max={max_val}")
        image_array = np.clip(image_array, 0, 65535).astype(np.uint16)
    
    # Apply Yen thresholding with error handling
    try:
        thresh_val = threshold_yen(image_array)
    except Exception as e:
        print(f"Thresholding error: {e}")
        print("Falling back to simple thresholding")
        # Use a simpler threshold method
        thresh_val = np.mean(image_array) + 2 * np.std(image_array)
    
    binary = image_array > thresh_val
    binary = image_array > thresh_val
    
    # Label connected components
    labeled = label(binary)
    regions = regionprops(labeled, image_array)
    
    # Filter regions by size and find the brightest one
    valid_regions = [r for r in regions if r.area >= min_object_size]
    
    # Create a visualization image
    # Normalize the original image for display
    norm_image = cv2.normalize(image_array, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    
    if not valid_regions:
        # If no objects of sufficient size, revert to brightest pixel
        print("No objects of sufficient size found, using brightest pixel instead")
        max_idx = np.argmax(image_array)
        row, col = np.unravel_index(max_idx, image_array.shape)
        
        # Mark brightest pixel on visualization
        vis_image = cv2.cvtColor(norm_image, cv2.COLOR_GRAY2BGR)
        cv2.circle(vis_image, (col, row), 5, (0, 0, 255), -1)  # Red circle
    else:
        # Find the region with highest mean intensity
        brightest_region = max(valid_regions, key=lambda r: r.mean_intensity)
        row, col = brightest_region.centroid
        row, col = int(row), int(col)
        print(f"Found brightest object with size {brightest_region.area} pixels and mean intensity {brightest_region.mean_intensity}")
        
        # Create colored visualization of the region
        vis_image = cv2.cvtColor(norm_image, cv2.COLOR_GRAY2BGR)
        
        # Get region mask for visualization
        region_mask = labeled == brightest_region.label
        region_mask_display = region_mask.astype(np.uint8) * 255
        
        # Add a colored overlay for the region
        vis_image[region_mask] = [0, 255, 0]  # Green overlay
        
        # Add a circle at centroid
        cv2.circle(vis_image, (col, row), 5, (0, 0, 255), -1)  # Red circle
    
    # Display binary mask and visualization
    # cv2.imshow("Object Detection", vis_image)
    # cv2.waitKey(50)  # Show for a short time (100ms)
    
    # Pad the image to handle boundaries
    padded = np.pad(image_array, pad_width=half, mode="constant", constant_values=0)

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
        
        # Crop the image around the brightest object
        cropped_array = crop_image_around_brightest_object(img_array, crop_size=80)
        
        # Save as an uncompressed 16-bit TIFF file using tifffile
        basename = os.path.basename(image_file)
        output_path = os.path.join(output_folder, basename)
        tifffile.imwrite(output_path, cropped_array.astype(np.uint16), compression=None)
    
    # Close all windows
    cv2.destroyAllWindows()
    print(f"Processing complete. Cropped images saved to {output_folder}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pre-process .tiff images by cropping around the brightest object and saving as uncompressed 16-bit TIFF files.")
    parser.add_argument("input_folder", help="Path to the folder containing .tiff images")
    args = parser.parse_args()
    
    output_folder = os.path.join(args.input_folder, "cropped")
    process_images(args.input_folder, output_folder)
"""
Convert TIFF stacks to JPG image sequences while maintaining dynamic range.
This script processes all .tif/.tiff files in a directory and converts each stack
to a series of JPG images in individual folders.
"""
import os
import cv2
import numpy as np
import tifffile
from tqdm import tqdm

# Directory configuration. Usually you only need to edit RESULTS_ROOT and RUN_ID.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_ROOT = os.path.join(SCRIPT_DIR, "results")
RUN_ID = "old"

STACK_SUBDIR = "01_tiff_stack"
JPG_SUBDIR = "02_tiff_jpg"

INPUT_DIRECTORY = os.path.join(RESULTS_ROOT, RUN_ID, STACK_SUBDIR)
OUTPUT_DIRECTORY = os.path.join(RESULTS_ROOT, RUN_ID, JPG_SUBDIR)


def normalize_to_8bit(image, method='minmax'):
    """
    Normalize image to 8-bit while preserving dynamic range.

    Args:
        image (np.ndarray): Input image
        method (str): Normalization method ('minmax', 'percentile', 'global')

    Returns:
        np.ndarray: 8-bit normalized image
    """
    if image.dtype == np.uint8:
        return image

    if method == 'minmax':
        img_min = image.min()
        img_max = image.max()
        if img_max > img_min:
            normalized = ((image - img_min) / (img_max - img_min) * 255).astype(np.uint8)
        else:
            normalized = np.zeros_like(image, dtype=np.uint8)

    elif method == 'percentile':
        p_low, p_high = np.percentile(image, [1, 99])
        if p_high > p_low:
            normalized = np.clip((image - p_low) / (p_high - p_low) * 255, 0, 255).astype(np.uint8)
        else:
            normalized = np.zeros_like(image, dtype=np.uint8)

    elif method == 'global':
        normalized = image.astype(np.uint8)

    return normalized


# [NEW] Returns a set of base names (without extension) of TIFF stacks that have
# already been converted, by checking for existing subfolders in output_dir.
def get_processed_stacks(output_dir):
    processed = set()

    if os.path.isdir(output_dir):
        for d in os.listdir(output_dir):
            if os.path.isdir(os.path.join(output_dir, d)):
                processed.add(d)
    else:
        print(f"Output directory not found yet: {output_dir} (will be created on first run)")

    return processed


def convert_tiff_stack_to_jpg(tiff_path, output_base_dir, normalization='minmax', quality=95):
    """
    Convert a single TIFF stack to JPG sequence.

    Args:
        tiff_path (str): Path to TIFF stack file
        output_base_dir (str): Base directory for output
        normalization (str): Normalization method
        quality (int): JPG quality (0-100)
    """
    try:
        print(f"Loading TIFF stack: {tiff_path}")
        tiff_stack = tifffile.imread(tiff_path)

        if tiff_stack.ndim == 2:
            tiff_stack = tiff_stack[np.newaxis, ...]
        elif tiff_stack.ndim == 4:
            print(f"Multi-channel stack detected with shape {tiff_stack.shape}")
            if tiff_stack.shape[-1] == 3:
                tiff_stack = np.mean(tiff_stack, axis=-1).astype(tiff_stack.dtype)
            else:
                tiff_stack = tiff_stack[..., 0]

        n_frames = tiff_stack.shape[0]
        print(f"Stack contains {n_frames} frames with shape {tiff_stack.shape[1:]}")
        print(f"Data type: {tiff_stack.dtype}, Range: {tiff_stack.min()} - {tiff_stack.max()}")

        base_name = os.path.splitext(os.path.basename(tiff_path))[0]
        output_dir = os.path.join(output_base_dir, base_name)
        os.makedirs(output_dir, exist_ok=True)

        if normalization == 'global':
            global_min = tiff_stack.min()
            global_max = tiff_stack.max()
            print(f"Using global normalization: {global_min} - {global_max}")

        for i in tqdm(range(n_frames), desc=f"Converting {base_name}"):
            frame = tiff_stack[i]

            if normalization == 'global':
                if global_max > global_min:
                    normalized_frame = ((frame - global_min) / (global_max - global_min) * 255).astype(np.uint8)
                else:
                    normalized_frame = np.zeros_like(frame, dtype=np.uint8)
            else:
                normalized_frame = normalize_to_8bit(frame, method=normalization)

            output_path = os.path.join(output_dir, f"{i:06d}.jpg")
            success = cv2.imwrite(output_path, normalized_frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            if not success:
                print(f"Warning: Failed to save frame {i} to {output_path}")

        print(f"Successfully converted {n_frames} frames to {output_dir}")

        metadata_path = os.path.join(output_dir, "conversion_info.txt")
        with open(metadata_path, 'w') as f:
            f.write(f"Original file: {tiff_path}\n")
            f.write(f"Original shape: {tiff_stack.shape}\n")
            f.write(f"Original dtype: {tiff_stack.dtype}\n")
            f.write(f"Original range: {tiff_stack.min()} - {tiff_stack.max()}\n")
            f.write(f"Normalization method: {normalization}\n")
            f.write(f"JPG quality: {quality}\n")
            f.write(f"Number of frames: {n_frames}\n")

        return True

    except Exception as e:
        print(f"Error processing {tiff_path}: {str(e)}")
        return False


def process_tiff_directory(input_dir, output_dir, normalization='minmax', quality=100):
    """
    Process all TIFF files in a directory.

    Args:
        input_dir (str): Directory containing TIFF files
        output_dir (str): Directory to save JPG sequences
        normalization (str): Normalization method ('minmax', 'percentile', 'global')
        quality (int): JPG quality (0-100)
    """
    tiff_files = []
    for ext in ['.tif', '.tiff', '.TIF', '.TIFF']:
        tiff_files.extend([f for f in os.listdir(input_dir) if f.endswith(ext)])

    if not tiff_files:
        print(f"No TIFF files found in {input_dir}")
        return

    # [NEW] Load already-processed stack names from the output directory.
    processed_stacks = get_processed_stacks(output_dir)

    # [NEW] Split files into pending and skipped, keyed by base name (without extension).
    pending = [f for f in tiff_files if os.path.splitext(f)[0] not in processed_stacks]
    skipped = [f for f in tiff_files if os.path.splitext(f)[0] in processed_stacks]

    total = len(tiff_files)
    n_skip = len(skipped)
    n_todo = len(pending)

    # [NEW] Print a summary before processing begins.
    print(f"Total TIFF files  : {total}")
    print(f"Already processed (skipping): {n_skip}")
    print(f"To be processed   : {n_todo}")
    print(f"Normalization method: {normalization}")
    print(f"JPG quality: {quality}")
    print(f"Output directory: {output_dir}")

    # [NEW] Print numbered list of skipped files.
    if skipped:
        print("\nSkipping the following files:")
        for i, f in enumerate(skipped, 1):
            print(f"  [{i}/{n_skip}] {f}")

    # [NEW] Print numbered list of files queued for processing.
    if pending:
        print("\nFiles queued for processing:")
        for i, f in enumerate(pending, 1):
            print(f"  [{i}/{n_todo}] {f}")

    print()

    os.makedirs(output_dir, exist_ok=True)

    successful = 0
    failed = 0

    # [CHANGED] Iterate over pending only; show [i/n_todo] numbering per file.
    for i, tiff_file in enumerate(pending, 1):
        tiff_path = os.path.join(input_dir, tiff_file)
        print(f"\n{'=' * 60}")
        print(f"[{i}/{n_todo}] Processing: {tiff_file}")  # [CHANGED] Added numbering
        print(f"{'=' * 60}")

        if convert_tiff_stack_to_jpg(tiff_path, output_dir, normalization, quality):
            successful += 1
        else:
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"Conversion complete!")
    print(f"Skipped (already processed): {n_skip} file(s)")  # [NEW]
    print(f"Successfully processed: {successful} file(s)")
    print(f"Failed: {failed} file(s)")
    print(f"{'=' * 60}")


def main():
    """Main function with configurable parameters."""

    normalization_method = 'minmax'
    jpg_quality = 100

    if not os.path.exists(INPUT_DIRECTORY):
        print(f"Input directory '{INPUT_DIRECTORY}' does not exist.")
        print("Please create the directory and place your TIFF files there.")
        return

    print("TIFF to JPG Converter")
    print("=" * 40)
    print(f"Input directory: {INPUT_DIRECTORY}")
    print(f"Output directory: {OUTPUT_DIRECTORY}")
    print(f"Normalization: {normalization_method}")
    print(f"JPG quality: {jpg_quality}")
    print("=" * 40)

    process_tiff_directory(INPUT_DIRECTORY, OUTPUT_DIRECTORY, normalization_method, jpg_quality)


if __name__ == "__main__":
    main()

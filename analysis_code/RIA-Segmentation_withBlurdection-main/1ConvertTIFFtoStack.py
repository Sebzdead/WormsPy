import os
import re
import sys

import tifffile
from tqdm import tqdm

# Directory configuration. Raw input can stay on H:, while results are local.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_ROOT = r"H:\MMH245_TG\raw_data"
RESULTS_ROOT = os.path.join(SCRIPT_DIR, "results")
RUN_ID = "old"
for _i, _arg in enumerate(sys.argv[1:], 1):
    if _arg.startswith("--run-id="):
        RUN_ID = _arg.split("=", 1)[1].strip()
    elif _arg == "--run-id" and _i + 1 < len(sys.argv):
        RUN_ID = sys.argv[_i + 1].strip()

RAW_SUBDIR = "00_raw"
STACK_SUBDIR = "01_tiff_stack"
RIGHTCAM_SUBDIR = "rightcam_tiffs"

LOCAL_RAW_DIRECTORY = os.path.join(RESULTS_ROOT, RUN_ID, RAW_SUBDIR)
BASE_DIRECTORY = LOCAL_RAW_DIRECTORY if os.path.isdir(LOCAL_RAW_DIRECTORY) else os.path.join(RAW_ROOT, RUN_ID)
STACK_DIRECTORY = os.path.join(RESULTS_ROOT, RUN_ID, STACK_SUBDIR)


def natural_sort_key(value):
    parts = re.split(r'(\d+)', value)
    return [int(part) if part.isdigit() else part.lower() for part in parts]


def get_processed_folders(stack_directory):
    processed = set()
    if os.path.isdir(stack_directory):
        for f in os.listdir(stack_directory):
            if f.endswith("_stack.tiff"):
                folder_name = f[:-len("_stack.tiff")]
                processed.add(folder_name)
    return processed


def tiff_files_in_directory(directory):
    if not os.path.isdir(directory):
        return []
    files = [file for file in os.listdir(directory) if file.lower().endswith((".tif", ".tiff"))]
    files.sort(key=natural_sort_key)
    return files


def resolve_input_tiff_directory(base_directory, subdir):
    direct_path = os.path.join(base_directory, subdir)
    if tiff_files_in_directory(direct_path):
        return direct_path
    rightcam_path = os.path.join(direct_path, RIGHTCAM_SUBDIR)
    if tiff_files_in_directory(rightcam_path):
        return rightcam_path
    return rightcam_path


def write_tiff_stack_streaming(input_path, tiff_files, output_path):
    temp_output_path = output_path + ".part.tiff"
    if os.path.exists(temp_output_path):
        os.remove(temp_output_path)

    first_image = tifffile.imread(os.path.join(input_path, tiff_files[0]))
    expected_shape = first_image.shape
    expected_dtype = first_image.dtype

    with tifffile.TiffWriter(temp_output_path, bigtiff=True) as writer:
        for i, tiff_file in enumerate(tqdm(tiff_files, desc=os.path.basename(output_path), leave=True)):
            image = first_image if i == 0 else tifffile.imread(os.path.join(input_path, tiff_file))
            if image.shape != expected_shape:
                raise ValueError(
                    f"Frame shape mismatch in {tiff_file}: expected {expected_shape}, got {image.shape}"
                )
            if image.dtype != expected_dtype:
                raise ValueError(
                    f"Frame dtype mismatch in {tiff_file}: expected {expected_dtype}, got {image.dtype}"
                )
            writer.write(image, contiguous=True, compression=None)

    os.replace(temp_output_path, output_path)
    return len(tiff_files), expected_shape, expected_dtype


def process_all_folders(base_directory, stack_directory):
    subdirs = sorted(
        [d for d in os.listdir(base_directory) if os.path.isdir(os.path.join(base_directory, d))],
        key=natural_sort_key,
    )
    if not subdirs:
        print(f"No subdirectories found in {base_directory}")
        return

    os.makedirs(stack_directory, exist_ok=True)
    processed_folders = get_processed_folders(stack_directory)
    skipped = 0
    successful = 0
    failed = 0

    for folder_idx, subdir in enumerate(subdirs, 1):
        output_filename = f"{subdir}_stack.tiff"
        output_path = os.path.join(stack_directory, output_filename)

        if subdir in processed_folders:
            skipped += 1
            print(f"[{folder_idx}/{len(subdirs)}] Skipping already processed folder: {subdir}")
            continue

        input_path = resolve_input_tiff_directory(base_directory, subdir)
        if not os.path.isdir(input_path):
            failed += 1
            print(f"[{folder_idx}/{len(subdirs)}] Missing TIFF input folder: {input_path}")
            continue

        tiff_files = tiff_files_in_directory(input_path)
        if not tiff_files:
            failed += 1
            print(f"[{folder_idx}/{len(subdirs)}] No TIFF files found in: {input_path}")
            continue

        try:
            print(f"\n[{folder_idx}/{len(subdirs)}] Processing {subdir}: {len(tiff_files)} frame(s)")
            n_frames, shape, dtype = write_tiff_stack_streaming(input_path, tiff_files, output_path)
            print(f"Saved {output_path}")
            print(f"Frames: {n_frames}, shape: {shape}, dtype: {dtype}")
            successful += 1
        except Exception as e:
            failed += 1
            print(f"\nError processing {subdir}: {e}")

    print("\nDone.")
    print(f"Successful: {successful}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")


if __name__ == "__main__":
    print(f"RUN_ID: {RUN_ID}")
    print(f"Input root: {BASE_DIRECTORY}")
    print(f"Output stack directory: {STACK_DIRECTORY}")
    if os.path.isdir(BASE_DIRECTORY):
        process_all_folders(BASE_DIRECTORY, STACK_DIRECTORY)
    else:
        print(f"{BASE_DIRECTORY} is not a directory")

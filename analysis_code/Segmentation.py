import os
import tifffile
import numpy as np
import cv2
import csv
import imageio
from PIL import Image
threshold = 5 # decrease this number for more selective thresholding
subtraction = -3 # decrease this number (more negative) for more selective thresholding
directory = "D:\WormSpy_video\ASH_GlycerolFeb25"
name = "worm4R"
segmented_csv_path = os.path.join(directory, name + '.csv') #input file

def find_largest_area_and_brightest_pixels(raw, eightbit, prev_centroid=None, distance_threshold=20):

    denoised = cv2.fastNlMeansDenoising(eightbit, None, h=25, templateWindowSize=7, searchWindowSize=11) # decrease h for more denoising

    thresh = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        threshold, 
        subtraction) 

    # Morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)

    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter contours by area
    min_area = 4
    max_area = 100
    valid_contours = [cnt for cnt in contours if min_area <= cv2.contourArea(cnt) <= max_area]

    # Copy the eightbit image for display
    output = eightbit.copy()
    output_color = cv2.cvtColor(output, cv2.COLOR_GRAY2BGR)

    # Initialize mask
    mask = np.zeros_like(eightbit)

    if valid_contours:
        # Find the largest contour based on area
        # largest_contour = max(contours, key=cv2.contourArea)
        sorted_contours = sorted(valid_contours, key=cv2.contourArea, reverse=True)
        
        # add contours to image
        cv2.drawContours(output_color, sorted_contours, -1, (0, 255, 0), 2)
        
        largest_contour = sorted_contours[0]

        # Find the centroid of the largest contour
        moment = cv2.moments(largest_contour)
        if moment["m00"] != 0:
            centroid_x = int(moment["m10"] / moment["m00"])
            centroid_y = int(moment["m01"] / moment["m00"])
            
            # if previous centroid is further away than the threshold, then set the centroid to 0,0
            if prev_centroid:
                distance = np.sqrt((centroid_x - prev_centroid[0])**2 + (centroid_y - prev_centroid[1])**2)
                if distance >= distance_threshold:
                    return None, None, prev_centroid, None, None
                else:
                    prev_centroid = (centroid_x, centroid_y)
            centroid = (centroid_x, centroid_y)
            # print(centroid)
            # Draw a circle with a radius of 10 pixels around the centroid in red
            cv2.circle(output_color, centroid, 10, (0, 0, 255), thickness=2)

            # Create a mask with a filled circle at the centroid
            cv2.circle(mask, centroid, 10, (255), thickness=-1)

    # Display the image with the circle
    cv2.imshow("Thresholded Image", output_color)
    cv2.waitKey(1)
    frames.append(output_color)

    # Apply the mask to the original image
    masked_image = cv2.bitwise_and(raw, raw, mask=mask)

    # Flatten the image and sort the pixel values in descending order
    sorted_pixels = np.sort(masked_image.flatten())[::-1]
    
    #discard pixels that are zero
    sorted_pixels = sorted_pixels[sorted_pixels != 0]

    # Take the brightest 25 pixels
    sorted_pixels = sorted_pixels[:25]
    sorted_pixels10 = sorted_pixels[:10]

    # Calculate ROI sum and mean
    ROI_sum = np.sum(sorted_pixels)
    mean = np.mean(sorted_pixels)
    ROI_sum10 = np.sum(sorted_pixels10)
    mean10 = np.mean(sorted_pixels10)

    return ROI_sum, mean, prev_centroid, ROI_sum10, mean10
    
def CLAHE(image, clip_limit=2.0, tile_grid_size=(8, 8)):
    # Create a CLAHE object
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    # Apply CLAHE
    equalized = clahe.apply(image)
    return equalized

if __name__ == "__main__":
    stack_in = os.path.join(directory, name + ".tiff")
    print(stack_in)
    stack = tifffile.imread(stack_in)

    # Ensure the image data is 16-bit
    stack = stack.astype(np.uint16)

    output_filename = name + '_thresh.gif'

    # Check if the output file already exists and delete it
    if os.path.exists(output_filename):
        os.remove(output_filename)

    frames = []  # List to store frames for the GIF

    prev_start_point = None
    if os.path.exists(segmented_csv_path):
        os.remove(segmented_csv_path)

    with open(segmented_csv_path, "a", newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["frame", "25px_sum", "25px_mean", "10px_sum", "10px_mean"])

        frame_number = 0
        prev_cent = None
        # Loop through each image in the stack
        for i, frame in enumerate(stack):
            # Convert to gray, median filter, threshold
            raw = frame
            curr_min = np.min(frame)
            curr_max = np.max(frame)
            # clipped = np.clip(frame, tot_min, tot_max)
            clipped = np.clip(frame, curr_min, curr_max)
            eightbit = ((clipped - curr_min) / (curr_max - curr_min)) * 255
            eightbit = eightbit.astype(np.uint8)
            adjusted = CLAHE(eightbit)
            # eightbit = adaptive_histogram_equalization(frame)
            #call the function to find the largest area and brightest pixels
            ROI_sum, mean, prev_cent, ROI_sum10, mean10 = find_largest_area_and_brightest_pixels(raw,adjusted, prev_centroid=prev_cent, distance_threshold=10)
            # ROI_sum, mean, ROI_sum10, mean10 = GPT_version(raw,eightbit)
            csv_writer.writerow([frame_number, ROI_sum, mean, ROI_sum10, mean10])
            frame_number += 1

        # Save frames as a GIF
        output_path = os.path.join(directory, output_filename)
        # Reduce the number of frames (e.g., take every 2nd frame)
        frames_reduced = frames[::2]

        # Resize frames to smaller dimensions
        width, height = 960, 600  # Example dimensions, adjust as needed
        frames_resized = [
            np.array(Image.fromarray(frame).resize((width, height)))
            for frame in frames_reduced]

        # Save the GIF with optimization settings
        imageio.mimsave(
            output_path,
            frames_resized,
            format='GIF',
            duration=100,                 # 100uS per frame
            palettesize=64,         # Reduce color palette to 64 colors
            subrectangles=True      # Enable subrectangle optimization
        )
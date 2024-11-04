
import cv2
import math
import cProfile
import pathlib as pl
from skimage.measure import label, regionprops
from zaber_motion import Library, Units
from zaber_motion.ascii import Connection, Device


# SET UP CONFIGURATION
TOTAL_MM_X = 1.3125  # total width of the FOV in mm
TOTAL_MM_Y = 1.05  # total height of the FOV in mm
MM_MST = 20997  # millimeters per microstep
# Zaber device boundaries
MAXIMUM_DEVICE_XY_POSITION = 1066667 # initialized, wil be updated by the motors
MAXIMUM_DEVICE_Z_POSITION = 209974 # may vary if using different motors
MINIMUM_DEVICE_POSITION = 0
ZABER_ORIENTATION_X = 1 # whether the x direction of the zaber is inverted from the video feed (-1 if they are inverted)
ZABER_ORIENTATION_Y = -1 # whether the y direction of the zaber is inverted from the video feed (-1 if they are inverted)




def main():
    # import .tif image with opencv
    file_path = pl.Path(r'd:\WormSpy_video\\testing_frames') # \bottomleft.tif
    for file in file_path.iterdir():
        img = cv2.imread(file_path / file, cv2.IMREAD_GRAYSCALE)
        cProfile
    

def iteration(frame):
    resolution = (frame.shape[1], frame.shape[0])
    initial_coords = [(resolution[0]/2), resolution[1]/2]
    calculated_worm_coords = initial_coords

def Thresh_Light_Background(frame):
    blurred_frame = cv2.GaussianBlur(frame, (33, 33), 99)
    # Convert the image to a binary image
    thresh = cv2.adaptiveThreshold(blurred_frame, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 69, 3)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    eroded_image = cv2.erode(thresh, kernel, iterations=3)
    processed_frame = cv2.dilate(eroded_image, kernel, iterations=1)
    return processed_frame

def find_worm_cms(processed_frame, factor, initial_coords):
    labeled_image = label(processed_frame)  #scans binary image and groups connected pixels with the value 1 into labeled regions
    regions = regionprops(labeled_image) #calculates properties of the labelled region, returns a list of regionProperties objects, each corresponding to properties of one of the labelled regions.
    regions_by_area = sorted(regions, key=lambda x: x.area, reverse=True)
    if regions_by_area:
        coords = regions_by_area[0].centroid
    else:
        coords = initial_coords  # center of FOV
    coords = (round(coords[1]), round(coords[0])) # flip x and y coordinates to match the video feed
    coords = (coords[0] * factor, coords[1] * factor)
    return coords

def simpleToCenter(centroidX, centroidY,resolution):
    # calculate the percent the position is from the edge of the frame
    percentX = float(centroidX) / float(resolution[0])
    percentY = float(centroidY) / float(resolution[1])
    # millimeters the position is from the edge
    millisX = percentX * TOTAL_MM_X
    millisY = percentY * TOTAL_MM_Y
    # millimeters the stage needs to move to catch up to the worm's position
    millisMoveX = ZABER_ORIENTATION_X * (millisX - TOTAL_MM_X/2)
    millisMoveY = ZABER_ORIENTATION_Y * (millisY - TOTAL_MM_Y/2)
    return millisMoveX, millisMoveY 

def trackWorm(input, deviceX: Device, deviceY: Device, deviceXPos, deviceYPos, resolution):
    global MAXIMUM_DEVICE_XY_POSITION, MINIMUM_DEVICE_POSITION
    # check if the input is NaN float value and return if so  
    if math.isnan(input[0]):
        return 0, 0
    # relative worm position is relative to the (0, 0) of the video feed
    master = simpleToCenter(input[0], input[1], resolution)
    # convert the millimeters back to microsteps
    xCmdAmt = master[0] * MM_MST
    yCmdAmt = master[1] * MM_MST

    # move device if the bounds of the device are not exceeded
    if (deviceXPos + xCmdAmt < MAXIMUM_DEVICE_XY_POSITION
    or deviceXPos + xCmdAmt > MINIMUM_DEVICE_POSITION
    or deviceYPos + yCmdAmt < MAXIMUM_DEVICE_XY_POSITION
    or deviceYPos + yCmdAmt > MINIMUM_DEVICE_POSITION):
        # move the device to the new position.
        x_data =int(xCmdAmt/5)
        # print(x_data)
        y_data =int(yCmdAmt/5)
        # print(y_data)
        deviceX.move_relative(x_data, unit = Units.NATIVE, wait_until_idle = False, velocity = 0, velocity_unit = Units.NATIVE, acceleration = 4, acceleration_unit = Units.NATIVE)
        deviceY.move_relative(y_data, unit = Units.NATIVE, wait_until_idle = False, velocity = 0, velocity_unit = Units.NATIVE, acceleration = 5, acceleration_unit = Units.NATIVE)
    return (deviceXPos + xCmdAmt), (deviceYPos + yCmdAmt)#, xCmdAmt, yCmdAmt
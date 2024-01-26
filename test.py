import EasyPySpin
import cv2
import numpy as np
from matplotlib import pyplot as plt
import os

# specify your path
path = 'D:\WormSpy_video\Calcium\Tracking_Video_Fluorescent_25-01-2024_16-20-59'

# get a list of all the image file names in the folder
images = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

# sort the images by name
images.sort()

# loop through the images
for image in images:
    # read the image
    img = cv2.imread(os.path.join(path, image))
    
    # display the image
    cv2.imshow('image', img)
    hist_frame_8bit = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

    # Calculate the frequency of pixels in the brightness range 0 - 255
    hist = cv2.calcHist([img], [0], None, [256], [0, 256])
    norm_hist = cv2.normalize(hist, hist, 1, 255, cv2.NORM_MINMAX)

    # Plot the histogram
    plt.hist(hist_frame_8bit.ravel(), 256, [0, 256])
    plt.show()
    cv2.waitKey(0)  # waits until a key is pressed
    cv2.destroyAllWindows()  # destroys the window showing image

#cap = EasyPySpin.VideoCapture(1)
#cap2 = EasyPySpin.VideoCapture(0)
    

import cv2
import EasyPySpin
import numpy as np
from skimage.filters import threshold_yen

cap = EasyPySpin.VideoCapture(1)

while (cap.isOpened()):
    # Read a frame from the video capture
    success, frame = cap.read()
    resolution = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    if frame.dtype != np.uint8: #check if frame is 8 bit and grayscale and convert if not
        frame = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

    frame_downsample = cv2.resize(frame, (int(frame.shape[1] / 2), int(frame.shape[0] / 2)), interpolation = cv2.INTER_AREA) # Downsample the frame to 1/4 of the original size
    height, width = frame_downsample.shape
    downsample_size = (int(height), int(width))

    inv_gamma = 1.5
    table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    gamma = cv2.LUT(frame, table)
    # Apply Gaussian blur to the frame
    blurred_frame = cv2.GaussianBlur(gamma, (1, 1), 11)
    # resize the frame to 1/4 of the original size
    resized_frame = cv2.resize(blurred_frame, downsample_size, interpolation = cv2.INTER_AREA)
    # Apply Yen's thresholding
    thresh = threshold_yen(resized_frame)
    # Create a binary image by applying the threshold
    processed_frame = resized_frame > thresh
    processed_frame = processed_frame.astype(np.uint8) * 255

    # Convert the grayscale frame to a color frame
    color_frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

    # Display the frame
    cv2.imshow("Frame", frame)
    cv2.imshow("Processed Frame", processed_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

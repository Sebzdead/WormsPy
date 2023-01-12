import cv2
import EasyPySpin

# Initialize the camera capture object
cap = EasyPySpin.VideoCapture(2)
if not cap.isOpened():
    print("Error opening video stream or file")
    exit()

# Define the codec and create VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'Y42B')
# fourcc = -1
out = cv2.VideoWriter()
out.open('test.avi', fourcc, 10.0, (1024,1024), isColor=False)
print(out.isOpened())

isRecording = False
while(True):
    # Capture the frame
    ret, frame = cap.read()

    # Write the frame if isRecording is True
    if isRecording:
        #print('is recording')
        frame = cv2.resize(frame,(1024,1024))
        out.write(frame)

    # Display the frame
    cv2.imshow("Frame", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('r'):
        if not isRecording:
            print("Start Recording")
            isRecording = True
        else:
            print("Stop Recording")
            out.release()
            isRecording = False

# Release everything if job is finished
cap.release()
cv2.destroyAllWindows()
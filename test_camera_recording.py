import cv2
import EasyPySpin
import imageio_ffmpeg as ffmpeg

# Initialize the camera capture object
cap = EasyPySpin.VideoCapture(0)
if not cap.isOpened():
    print("Error opening video stream or file")
    exit()

# Define the codec and create VideoWriter object
# fourcc = cv2.VideoWriter_fourcc(*'DIB ')
# fourcc = -1
# out = cv2.VideoWriter()
# out.open('test.mov', fourcc, 10.0, (1024,1024), isColor=True)
# writer = ffmpeg.write_frames("D:\WormSpy_video\Calcium\temp\test%03d.tiff", (1024,1024), fps=10, codec="DIB ")
# print(out.isOpened())
# writer.send(None)
frame_count = 0
isRecording = False
folder_name = 'D:\\WormSpy_video\\Calcium\\temp\\'
while(True):
    # Capture the frame
    ret, frame = cap.read()

    # Write the frame if isRecording is True
    if isRecording:
        #print('is recording')
        frame = cv2.resize(frame,(1024,1024))
        # out.write(frame)
        # writer.send(frame)
        # gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # gray_frame = np.array(gray_frame, dtype=np.uint16)
        cv2.imwrite(f"{folder_name}\\frame_{frame_count}.tiff", frame)
        frame_count += 1

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
            # out.release()
            isRecording = False
            frame_count = 0


# Release everything if job is finished
cap.release()
cv2.destroyAllWindows()
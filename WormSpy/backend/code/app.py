from flask import Flask, request, Response, jsonify, render_template, abort
from flask_cors import CORS, cross_origin
import EasyPySpin
import cv2
import math
from zaber_motion.ascii import Connection, Device
from zaber_motion import Library, Units
import numpy as np
import pytz
from datetime import datetime
import pathlib
import copy
from skimage.measure import label, regionprops
from skimage import filters
from Controller import start_controller
# from flask_sockets import Sockets
# from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='production\\templates',
            static_folder='production\\static')
CORS(app, origins=['http://localhost:4200', 'http://localhost:5000', 'https://4dfklk7l-4200.use.devtunnels.ms'])
app.config['CORS_HEADERS'] = 'Content-Type'
# sockets = Sockets(app)
# socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize the device database for Zaber communication
Library.enable_device_db_store()

# Start the Flask app locally on host IP address 127.0.0.1
# python -m flask run --host=127.0.0.1

# HARD CODED VARIABLES vvv

# SET UP CONFIGURATION
TOTAL_MM_X = 1.3125  # total width of the FOV in mm
TOTAL_MM_Y = 1.05  # total height of the FOV in mm

# whether the x direction of the zaber is inverted from the video feed (-1 if they are inverted)
ZABER_ORIENTATION_X = 1
# whether the y direction of the zaber is inverted from the video feed (-1 if they are inverted)
ZABER_ORIENTATION_Y = -1

# UNIT CONVERSIONS
MM_MST = 20997  # millimeters per microstep

# Zaber device boundaries
MAXIMUM_DEVICE_XY_POSITION = 1066667
MAXIMUM_DEVICE_Z_POSITION = 209974
MINIMUM_DEVICE_POSITION = 0

# Global Variables for recording
stop_stream = False
start_recording = False
stop_recording = False
start_recording_fl = False
stop_recording_fl = False

timeZone = pytz.timezone("US/Eastern")
settings = {
    "fps": 10,
    "filepath": str(pathlib.Path.home() / 'WormSpy_video'),
    "filename": 'default',
    # "fps_fl": 10,
    # "filename_fl": 'default_fluorescent'
}

# DLC Live Settings
# from dlclive import DLCLive, Processor
# Import the DLC NN model
# dlc_proc = Processor()
# dlc_live = DLCLive(r'C:\Users\User\Documents\WormSpy\DLC_models/3-node',
#                    processor=dlc_proc, display=False)

# Autofocus settings
af_enabled = False
start_af = False

# Intial Camera Settings
leftCam = None
rightCam = None
XYmotorport = 'COM6'
Zmotorport = 'COM3'

# Tracking Variables
track_algorithm = 0
is_tracking = False
start_tracking = False
nodeIndex = 0

# variables for histogram
hist_frame = None
 
# Fluorescent Camera Settings
fluorExposure = 40000
fluorGain = 0

@app.route("/")
@cross_origin()
def home():
    return render_template('index.html')

@cross_origin()
@app.route('/video_feed')
def video_feed():
    global leftCam
    # Open the video capture
    cap = EasyPySpin.VideoCapture(leftCam)
    # Check if the camera is opened successfully
    if not cap.isOpened():
        print("Camera can't open\nexit")
        return -1
    
    # function to generate a stream of image frames for the tracking video feed
    def gen():
        global xMotor, yMotor, zMotor, start_recording, stop_recording, settings, is_tracking, start_tracking, serialPort, af_enabled, start_af, stop_stream, nodeIndex, track_algorithm
        start_af = False
        start_recording = False
        stop_recording = False
        is_recording = False
        worm_coords = [0, 0]
        xPos = 0
        yPos = 0
        xCmd = 0
        yCmd = 0
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter()
        with Connection.open_serial_port(XYmotorport) as connection:
            with Connection.open_serial_port(Zmotorport) as connection2:
                connection.enable_alerts()
                connection2.enable_alerts()
                horizontal_motors = connection.detect_devices()
                vertical_motor = connection2.detect_devices()
                print("Found {} devices on " + XYmotorport.format(len(horizontal_motors)))
                print("Found {} devices on " + Zmotorport.format(len(vertical_motor)))

                device_X = horizontal_motors[0]
                device_Y = horizontal_motors[1]
                device_Z = vertical_motor[0]

                xMotor = device_X.get_axis(1)
                yMotor = device_Y.get_axis(1)
                zMotor = device_Z.get_axis(1)
                
                firstIt = True
                counter = 0
                while (cap.isOpened()):
                    # Read a frame from the video capture
                    success, frame = cap.read()
                    resolution = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    # Check if the frame was successfully read
                    if stop_stream:
                        abort(200)
                    if success:
                        previous_worm_coords = None
                        if start_tracking:
                            xPos = xMotor.get_position(unit=Units.NATIVE)
                            yPos = yMotor.get_position(unit=Units.NATIVE)
                            start_tracking = False
                        if is_tracking and counter % 1 == 0:
                            if track_algorithm == 0:
                                worm_coords = tracking_light_thresh(frame, previous_worm_coords)
                            elif track_algorithm == 1:
                                worm_coords = tracking_dark_thresh(frame, previous_worm_coords)
                            elif track_algorithm == 2:
                                dlc_live = None
                                poseArr = DLC_tracking(dlc_live,firstIt,frame)
                                posArr = poseArr[:, [0, 1]]
                                worm_coords[0] = posArr[nodeIndex, 0]
                                worm_coords[1] = posArr[nodeIndex, 1]
                            previous_worm_coords = worm_coords  
                            xPos, yPos, xCmd, yCmd = trackWorm(
                                (worm_coords[0], worm_coords[1]), xMotor, yMotor, xPos, yPos, resolution)
                        counter += 1
                        # Reinitialize file recording
                        if start_recording:
                            print("Start Recording")
                            dt = datetime.now(tz=timeZone)
                            dtstr = '_' + dt.strftime("%d-%m-%Y_%H-%M-%S")
                            recording_folder = settings["filename"] + dtstr
                            project_path: pathlib.Path = filepathToDirectory(settings["filepath"]) / recording_folder
                            if not project_path.exists(): 
                                project_path.mkdir(parents=True, exist_ok=False)
                            avi_file = settings["filename"] + dtstr + '.avi'
                            out.open(str(project_path / avi_file),
                                     fourcc, settings["fps"], resolution, isColor=False)
                            start_recording = False
                            is_recording = True
                            csvDump = np.zeros((1, 2))
                        # add frame to recording buffer if currently recording
                        if is_recording:
                            csvDump = np.append(
                                csvDump, [[xCmd, yCmd]], axis=0)
                            out.write(frame)
                        # convert recording buffer to file
                        if stop_recording:
                            print("Stopped Recording")
                            out.release()
                            dt = datetime.now()
                            dtstr = '_' + dt.strftime("%d-%m-%Y_%H-%M-%S")
                            csv_file = settings["filename"] + dtstr + ".csv"
                            np.savetxt(
                                str(project_path / csv_file), csvDump, delimiter=",")
                            is_recording = False
                            stop_recording = False

                        #factor = cap.get(3) / (cap.get(3) * (1/downsample_by))
                        # posArr = [
                        #     tuple(map(lambda x: int(abs(x) * factor), i)) for i in posArr]
                        
                        # Change color to rgb from bgr to allow for the coloring of circles
                        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
                        # Scale the CMS position up to the original frame size and draw on frame
                        if worm_coords is not None:
                            original_cms = (int(worm_coords[1] * 4), int(worm_coords[0] * 4))
                            cv2.circle(frame, (int(original_cms[1]), int(original_cms[0])), 9, (0, 255, 0), -1)

                        # add skeleton overlay to image for DLC
                        #frame = draw_skeleton(frame, posArr)

                        ret, jpeg = cv2.imencode('.png', frame)
                        # Yield the encoded frame
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
                    else:
                        # If the frame was not successfully read, yield a "blank frame
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n\r\n')
    # Return the video feed as a multipart/x-mixed-replace response
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@cross_origin()
@app.route('/video_feed_fluorescent')
def video_feed_fluorescent():
    global rightCam, stop_stream
    cap2 = EasyPySpin.VideoCapture(rightCam)
    # Check if the camera is opened successfully
    if not cap2.isOpened():
        print("Camera can't open\nexit")
        return -1
    if stop_stream:
        abort(200)
    def gen():
        global start_recording_fl, stop_recording_fl, settings, is_tracking, serialPort, fluorExposure, fluorGain, fluorFPS, hist_frame
        is_recording = False
        cap2.set(cv2.CAP_PROP_EXPOSURE, fluorExposure)
        cap2.set(cv2.CAP_PROP_GAIN, fluorGain)
        while (cap2.isOpened()):
            # Read a frame from the video capture
            success, frame = cap2.read()
            cap2_x = cap2.get(cv2.CAP_PROP_FRAME_WIDTH)
            cap2_y = cap2.get(cv2.CAP_PROP_FRAME_HEIGHT)
            # Check if the frame was successfully read
            if success:
                # Apply the jet color map to the frame
                frame_8bit = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                #frame_8bit_c = cv2.applyColorMap(frame_8bit, cv2.COLORMAP_JET)
                # hist_frame = frame
                hist_frame = copy.copy(frame_8bit)
                if start_recording_fl:
                    print("Start Fluorescent Recording")
                    # out.open(settings["filepath_fl"] + settings["filename_fl"], fourcc, float(settings["fps_fl"]), settings["resolution_fl"], isColor=False)
                    start_recording_fl = False
                    is_recording = True
                    frame_count = 0
                    dt = datetime.now(tz=timeZone)
                    dtstr = dt.strftime("%d-%m-%Y_%H-%M-%S")
                    folder_name = settings["filename"] + '_' + dtstr
                    project_path: pathlib.Path = filepathToDirectory(settings["filepath"]) / folder_name / 'fluorescent_tiffs'
                    if not project_path.exists(): 
                        project_path.mkdir(parents=True, exist_ok=False)
                    # path = os.path.join(settings["filepath"], folder_name)
                    # os.mkdir(path)
                if is_recording:
                    frame_count += 1
                    frame = cv2.resize(frame, [cap2_x,cap2_y])
                    frame_name = f"frame_{frame_count}.tiff"
                    cv2.imwrite(
                        str(project_path / frame_name), frame)
                if stop_recording_fl:
                    print("Stopped Fluorescent Recording")
                    # out.release()
                    is_recording = False
                    stop_recording_fl = False

                ret, jpeg = cv2.imencode('.png', frame_8bit)
                # Yield the encoded frame
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            else:
                # If the frame was not successfully read, yield a blank frame
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n\r\n')
    # Return the video feed as a multipart/x-mixed-replace response
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Function to process the frame and find the worm center of mass, might need to change it for your use case
def tracking_light_thresh(frame, previous_cms):
    # Apply gamma correction to the frame
    gamma_inv = 1.5
    table = np.array([((i / 255.0) ** gamma_inv) * 255 for i in np.arange(0, 256)]).astype("uint8")
    gamma_corrected_frame =  cv2.LUT(frame, table)
    # Apply Gaussian blur to the frame
    blurred_frame = cv2.GaussianBlur(gamma_corrected_frame, (9, 9), 0)
    grayscale_image = cv2.cvtColor(blurred_frame, cv2.COLOR_BGR2GRAY) if len(blurred_frame.shape) == 3 else blurred_frame
    # Convert the image to a binary image
    table = np.array([((i / 255.0) ** (1/gamma_inv)) * 255 for i in np.arange(0, 256)]).astype("uint8")
    adjusted_gamma_image =  cv2.LUT(grayscale_image, table)
    _, thresholded_image = cv2.threshold(adjusted_gamma_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # turn invert off for dark background, on for light
    inverted_image = cv2.bitwise_not(thresholded_image)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9,9))
    eroded_image = cv2.erode(inverted_image, kernel, iterations=1)
    processed_frame = cv2.dilate(eroded_image, kernel, iterations=1)
    # find center of mass of the worm
    labeled_image = label(processed_frame)  #scans binary image and groups connected pixels with the value 1 into labeled regions
    regions = regionprops(labeled_image) #calculates properties of the labelled region, returns a list of regionProperties objects, each cor
    #corresponding to properties of one of the labelled regions.
    
    # If there's a previous CMS, use it to find the closest blob
    if previous_cms is not None:
        distances = [] #empty list to store distances from the previous CMS to centroid of the current blobs. 
        for region in regions:
            # Calculate Euclidean distance from the previous CMS
            distance = np.linalg.norm(np.array(region.centroid) - np.array(previous_cms))
            distances.append((distance, region.centroid))
        # Get the centroid with the minimum distance
        if distances:
            cms = min(distances, key=lambda x: x[0])[1]
        else:
            cms = None  # or some other default value
        #after calculating distances for all regions, the one with the smallest distance to the previous CMS is considered to be the actual position of the worm (because of high frame rate)
        #key=lambda x,  x[0] part is so that the min function uses the first element of each tuple (the distance) to find the minimum value. The [1] at the end extracts the centroid part of the tuple, which is the CMS.
    else:
        # If no previous CMS, assume the largest blob is the worm
        regions_by_area = sorted(regions, key=lambda x: x.area, reverse=True)
        #sort in descending order
        # Keep the largest region
        if regions_by_area:
            cms = regions_by_area[0].centroid
        else:
            cms = None
    return cms

def DLC_tracking(dlc_live,firstIt,frame):
    downsample_by = 4
    # Resize the image to be 256x256
    img_tracking = cv2.resize(
        frame, None, fx=1/downsample_by, fy=1/downsample_by)
    if firstIt: 
        dlc_live.init_inference(img_tracking)
        firstIt = False
    poseArr = dlc_live.get_pose(img_tracking)
    return poseArr

def tracking_dark_thresh(frame):

    color_frame = cv2.cvtColor(cv2.convertScaleAbs(frame, alpha=255/65535), cv2.COLOR_GRAY2BGR)
    blurred = filters.gaussian(frame, sigma=3.0, preserve_range=True)
    blurred_8bit = cv2.convertScaleAbs(blurred, alpha=(255/65535))
    mean_value = np.mean(blurred_8bit)
    _, thresh = cv2.threshold(blurred_8bit, mean_value, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    eroded = cv2.erode(thresh, kernel, iterations=3)
    contours, _ = cv2.findContours(eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    worm_contour = max(contours, key=cv2.contourArea)


@cross_origin()
@app.route("/get_hist")
def get_hist():
    def gen():
        global hist_frame
        current_frame = np.zeros((1200, 1920, 1), dtype=np.uint8)
        first = True
        while True: 
            # if first:
            #     first = False
            #     print(hist_frame)
            # if hist_frame is not None:
            #     current_frame = hist_frame
            current_frame = hist_frame
                
            if current_frame is not None:
                # print(hist_frame.shape[0])
                # buffer = io.BytesIO()
                #hist_frame_8bit = cv2.normalize(current_frame, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                hist_size = 256
                hist_w = 512
                hist_h = 400
                bin_w = int(round(hist_w / hist_size))
                hist = cv2.calcHist(current_frame, [0], None, [hist_size], (0, 256), accumulate=False)
                
                norm_hist = cv2.normalize(hist, hist, 0, hist_h, cv2.NORM_MINMAX)
                histImage = np.zeros((hist_h, hist_w, 3), dtype=np.uint8)
                # # Create an empty image
                # h = np.ones((256, 256, 3)) * 255  # Here, 300 is the height and 256 is the width
                for i in range(1, hist_size):
                    cv2.line(histImage, (bin_w * (i - 1), hist_h - int(norm_hist[i - 1])),
                             (bin_w * (i), hist_h - int(norm_hist[i])), (0, 255, 0), thickness=2)
                
                ret, image_data = cv2.imencode('.png', histImage)
                png = image_data.tobytes()
                # image_data = buffer.getvalue()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + png + b'\r\n')
            else:
                # If the frame was not successfully read, yield a blank frame
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n\r\n')
    # Return the video feed as a multipart/x-mixed-replace response
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')


@cross_origin()
@app.route("/start_recording", methods=['POST'])
def start_recording():
    global start_recording, start_recording_fl, settings
    # Update the settings with the data from the request body
    settings["filepath"] = request.json["filepath"]
    settings["filename"] = request.json["filename"]
    # settings["fps"] = request.json["fps"]
    # settings["resolution"] = (
    #     request.json["resolution"], request.json["resolution"])
    # settings["filepath_fl"] = request.json["filepath_fl"]
    # settings["filename_fl"] = request.json["filename_fl"]
    # settings["fps_fl"] = request.json["fps_fl"]
    # settings["resolution_fl"] = (
    #     request.json["resolution_fl"], request.json["resolution_fl"])
    # Set the recording flag to True
    start_recording = True
    start_recording_fl = True
    # return jsonify({"message": "Recording started"})
    return str(settings)

@cross_origin()
@app.route("/stop_recording", methods=['POST'])
def stop_recording():
    global stop_recording, stop_recording_fl
    # Stop the recording of both video feeds
    stop_recording = True
    stop_recording_fl = True
    return jsonify({"message": "Recording stopped"})

@cross_origin()
@app.route("/stop_live_stream", methods=['POST'])
def stop_live_stream():
    global stop_stream
    # Stop both video feeds
    stop_stream = True
    return jsonify({"message": "Streams stopped"})

@cross_origin()
@app.route("/camera_settings", methods=['POST'])
def camera_settings():
    global leftCam, rightCam, serialPort
    # Set the camera settings before starting the video feeds
    leftCam = request.json['leftCam']
    rightCam = request.json['rightCam']
    serialPort = request.json['serialInput']
    return jsonify({"message": "Recording stopped"})

@cross_origin()
@app.route("/flour_settings", methods=['POST'])
def flour_settings():
    global fluorExposure, fluorGain, fluorFPS
    # Set the camera settings before starting the video feeds
    fluorExposure = request.json['exposure']
    fluorGain = request.json['gain']
    fluorFPS = request.json['fps']
    return jsonify({"message": "Fluorescent Settings Updated"})

@cross_origin()
@app.route("/node_index", methods=['POST'])
def node_index():
    global nodeIndex
    # Set the camera settings before starting the video feeds
    nodeIndex = request.json['index']
    return jsonify({f"message": "NodeIndex Recieved: {nodeIndex}"})

@cross_origin()
@app.route("/toggle_tracking", methods=['POST'])
def toggle_tracking():
    global is_tracking, start_tracking, track_algorithm
    is_tracking = request.json['is_tracking'] == "True"
    track_algorithm = request.json['tracking_algorithm']
    # start tracking if tracking has been requested
    start_tracking = is_tracking
    return str(is_tracking)


@cross_origin()
@app.route("/toggle_af", methods=['POST'])
def toggle_af():
    global af_enabled, start_af
    af_enabled = request.json['af_enabled'] == "True"
    # start focuslock if tracking has been requested
    start_af = af_enabled
    return str(af_enabled)

@cross_origin()
@app.route("/toggle_manual", methods=['POST'])
def toggle_manual():
    manual_mode = request.json['toggle_manual'] == "True"
    start_controller(manual_mode)
    return str(manual_mode)
    # return str(
    #     request.json['toggle_manual']
    # )


def determineFocus(image):
    # determine focus using thresholding
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    abs_sobelx = cv2.convertScaleAbs(sobelx)
    focus_measure = int(cv2.Laplacian(abs_sobelx, cv2.CV_64F).var())
    return focus_measure


def setFocus(zMotor: Device, focus: int, afRollingAvg, afMotorPos):
    step = 30  # The amount the z motor moves with each call of the function
    mPos = afMotorPos[-1]
    if len(afRollingAvg) > 1 and len(afMotorPos) > 1:
        mPosDiff = afMotorPos[-1] - afMotorPos[-2]
        # current focus is worse than previous focus
        if focus < np.mean(afRollingAvg):
            # move towards previous position
            if mPosDiff <= 0 and mPos + step < MAXIMUM_DEVICE_Z_POSITION:
                zMotor.move_relative(step, unit = Units.NATIVE, wait_until_idle = False, velocity = 0, velocity_unit = Units.NATIVE, acceleration = 0, acceleration_unit = Units.NATIVE)
                return (mPos + step)
            elif mPosDiff > 0 and mPos - step > MINIMUM_DEVICE_POSITION:
                zMotor.move_relative(-step, unit = Units.NATIVE, wait_until_idle = False, velocity = 0, velocity_unit = Units.NATIVE, acceleration = 0, acceleration_unit = Units.NATIVE)
                return (mPos - step)
        # current focus is better than previous focus
        elif focus > np.mean(afRollingAvg):
            if mPosDiff <= 0 and mPos - step > MINIMUM_DEVICE_POSITION:
                zMotor.move_relative(-step, unit = Units.NATIVE, wait_until_idle = False, velocity = 0, velocity_unit = Units.NATIVE, acceleration = 0, acceleration_unit = Units.NATIVE)
                return (mPos - step)
            elif mPosDiff > 0 and mPos + step < MAXIMUM_DEVICE_Z_POSITION:
                zMotor.move_relative(step, unit = Units.NATIVE, wait_until_idle = False, velocity = 0, velocity_unit = Units.NATIVE, acceleration = 0, acceleration_unit = Units.NATIVE)
                return (mPos + step)
    return mPos


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
    # check if the input is NaN float value and return if so  
    if math.isnan(input[0]):
        return 0, 0

    # relative worm position is relative to the (0, 0) of the video feed
    master = simpleToCenter(input[0], input[1], resolution)

    # convert the millimeters back to microsteps
    xCmdAmt = master[0] * MM_MST
    yCmdAmt = master[1] * MM_MST

    # chill factor is used to slow down the movement of the stage
    chill_factor = 15
    # move device if the bounds of the device are not exceeded
    if (deviceXPos + xCmdAmt/10 < MAXIMUM_DEVICE_XY_POSITION
    or deviceXPos + xCmdAmt/10 > MINIMUM_DEVICE_POSITION
    or deviceYPos + yCmdAmt/10 < MAXIMUM_DEVICE_XY_POSITION
    or deviceYPos + yCmdAmt/10 > MINIMUM_DEVICE_POSITION):
        # move the device to the new position. replace chill facor with velocity manipulation
        x_data =int(xCmdAmt/chill_factor)
        y_data =int(yCmdAmt/chill_factor)
        deviceX.move_relative(x_data, unit = Units.NATIVE, wait_until_idle = False, velocity = 0, velocity_unit = Units.NATIVE, acceleration = 0, acceleration_unit = Units.NATIVE)
        deviceY.move_relative(y_data, unit = Units.NATIVE, wait_until_idle = False, velocity = 0, velocity_unit = Units.NATIVE, acceleration = 0, acceleration_unit = Units.NATIVE)
    return (deviceXPos + xCmdAmt/10), (deviceYPos + yCmdAmt/10), xCmdAmt, yCmdAmt

def draw_skeleton(frame, posArr):
    # Line and circle attributes
    linecolor = (0, 0, 0)
    lineThickness = 2
    circleThickness = -1
    circleRadius = 5

    # Colors of the different worm parts
    noseTipColor = (0, 0, 255)
    pharynxColor = (0, 128, 255)
    nerveRingColor = (0, 255, 255)
    # confArr = poseArr[:, 2]
    # Overlay the tracking data onto the image
    # line from nose tip to pharynx
    cv2.line(frame, posArr[0], posArr[1], linecolor, lineThickness)
    # line from pharynx to nerve_ring
    cv2.line(frame, posArr[1], posArr[2], linecolor, lineThickness)

    # draw circles on top of each worm part
    cv2.circle(frame, posArr[0], circleRadius, noseTipColor, circleThickness)
    cv2.circle(frame, posArr[1], circleRadius, pharynxColor, circleThickness)
    cv2.circle(frame, posArr[2], circleRadius, nerveRingColor, circleThickness)
    return frame

def filepathToDirectory(str_path: str):
    # global record_path
    path = pathlib.Path(str_path)

    if not path.exists():
        path.mkdir(parents=True)
    
    return path

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)
    # socketio.run(app, host='127.0.0.1', port=5000, debug=False)
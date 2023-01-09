import EasyPySpin
import cv2
from dlclive import DLCLive, Processor
import math
from zaber_motion import Library, Units
from zaber_motion.binary import Connection, CommandCode, Device

# ToDo
# 1. Finish tracking software
# 2. Integrate with frontend GUI
# 3. Enable video recording
# 4. Allow CSV writing of all commands that are sent to zabers
# 5. Autofocus
# 6. Trace worm movements based on zaber positions 


Library.enable_device_db_store()
# PREFERENCES, these change how the code will act in aesthetic ways
LOG_SENT_COMMANDS = True  # whether or not to print to console when a command is sent to zaber
SENT_COMMAND_PRECISION = 4  # places after the decimal to include in logged commands
PRE_CODE = "A-"  # a string put before all logged messages

# COMMONLY USED CONFIGURATION
# CURRENT_HEIGHT = 4  #millimeters height of camera
TRACKING_MODE = "simpleToCenter"  # the mode for how the camera should track, default is "simpleToCenter"
COM_PORT = "COM4"  # which com port to connect to for the zaber connection, format "COM#"
CONNECTED_TO_ZABER = True  # whether or not the program should try to connect to the zaber (False for debugging)

# SET UP CONFIGURATION -- config to be changed more rarely
# BASE_HEIGHT = 1  #millimeters camera is up
TOTAL_MM_X = 1.3125  # total width of the FOV in mm
TOTAL_MM_Y = 1.05  # total height of the FOV in mm

ZABER_ORIENTATION_X = 1  # whether the x direction of the zaber is inverted from the video feed (-1 if they are inverted)
ZABER_ORIENTATION_Y = 1  # whether the y direction of the zaber is inverted from the video feed (-1 if they are inverted)

TOTAL_PIXELS_X = 256  # pixels across of the video feed
TOTAL_PIXELS_Y = 256  # pixels across of the video feed

# UNIT CONVERSIONS
MM_MST = 20997  # millimeters per microstep
MM_TOT = 50.8  # total millimeters that the zaber can extend

def main(deviceList):
    # cap = EasyPySpin.VideoCapture(2)
    cap = cv2.VideoCapture('test.mp4')

    if not cap.isOpened():
        print("Camera can't open\nexit")
        return -1

    cap.set(cv2.CAP_PROP_EXPOSURE, -1)  # -1 sets exposure_time to auto
    cap.set(cv2.CAP_PROP_GAIN, -1)  # -1 sets gain to auto

    dlc_proc = Processor()
    dlc_live = DLCLive('DLC_models', processor=dlc_proc, display=False)

    firstIt = True
    while True:
        ret, frame = cap.read()
        # frame = cv2.cvtColor(frame, cv2.COLOR_BayerBG2BGR)  # for RGB camera demosaicing

        if not ret:
          break

        # img_show = cv2.resize(frame, None, fx=0.25, fy=0.25)
        # cv2.imwrite('testout.png', frame)
        img_show = cv2.resize(frame, None, fx=0.25, fy=0.25)

        if firstIt:
          dlc_live.init_inference(img_show)
          firstIt = False
        poseArr = dlc_live.get_pose(img_show)
        posArr = poseArr[:, [0, 1]]
        posArr =  [list( map(int, i) ) for i in posArr]
        # Overlay the tracking data onto the image
        # Lien and circle attributes
        linecolor = (0, 0, 0)
        lineThickness = 2
        circleThickness = -1
        circleRadius = 2
        
        # Colors of the different worm parts
        noseTipColor = (0, 0, 255)
        pharynxColor = (0, 128, 255)
        nerveRingColor = (0, 255, 255)
        midbody1Color = (0, 255, 0)
        midbody2Color = (255, 0, 0)
        midbody3Color = (255, 0, 255)
        tailBaseColor = (0, 0, 255)
        tailTipColor = (255, 0, 0)
        
        # line from nose tip to pharynx 
        cv2.line(img_show, posArr[0], posArr[1], linecolor, lineThickness)
        # line from pharynx to nerve_ring
        cv2.line(img_show, posArr[1], posArr[2], linecolor, lineThickness)
        # line from nerve ring to midbody1
        cv2.line(img_show, posArr[2], posArr[3], linecolor, lineThickness)
        # line from midbody1 to midbody2
        cv2.line(img_show, posArr[3], posArr[4], linecolor, lineThickness)
        # line from midbody2 to midbody3
        cv2.line(img_show, posArr[4], posArr[5], linecolor, lineThickness)
        # line from midbody3 to tail_base
        cv2.line(img_show, posArr[5], posArr[6], linecolor, lineThickness)
        # line from tail_base to tail_tip
        cv2.line(img_show, posArr[6], posArr[7], linecolor, lineThickness)
        
        # draw circles on top of each worm part
        cv2.circle(img_show, posArr[0], circleRadius, noseTipColor, circleThickness)
        cv2.circle(img_show, posArr[1], circleRadius, pharynxColor, circleThickness)
        cv2.circle(img_show, posArr[2], circleRadius, nerveRingColor, circleThickness)
        cv2.circle(img_show, posArr[3], circleRadius, midbody1Color, circleThickness)
        cv2.circle(img_show, posArr[4], circleRadius, midbody2Color, circleThickness)
        cv2.circle(img_show, posArr[5], circleRadius, midbody3Color, circleThickness)
        cv2.circle(img_show, posArr[6], circleRadius, tailBaseColor, circleThickness)
        cv2.circle(img_show, posArr[7], circleRadius, tailTipColor, circleThickness)

        cv2.imshow("Spying on the worm", img_show)
        if cv2.waitKey(25) & 0xFF == ord('q'):
          break
        # print("Position Array: ", poseArr)
        # nerveringX = poseArr[2, 0]
        # nerveringY = poseArr[2, 1]
        # # print("(", nerveringX, ',', nerveringY, ')')
        # trackOut1, trackOut2 = trackWorm((nerveringX, nerveringY), deviceList)
        # if trackOut1 == 0 and trackOut2 == 0:
        #     print("Worm tracking failed or worm isn't moving")

        # break
        # key = cv2.waitKey(30)
        # if key == ord("q"):
        #     break

    # cap.release()
    # cv2.destroyAllWindows()

# def dlcLive(frame):
    
#     return 

def trackWorm(input, deviceList):
	# check if the input is NaN float value and return if so
  if math.isnan(input[0]):
    return 0, 0

	# convert pixels to millimeters
  inpX = input[0]
  inpY = input[1]

	# create master list value that will contain [command move x, command move y, relative worm position x, relative worm position y]
	# relative worm position is relative to the (0, 0) of the video feed
  master = [0, 0, 0, 0]
  
	# set master to the correct values
  if TRACKING_MODE == "simpleToCenter":
    master = simpleToCenter(inpX, inpY)
  else:
    print("[EERR] Unknown movement type provided.")
    return 0, 0

	# convert the millimeters back to microsteps
  xCmdAmt = master[0] * MM_MST
  yCmdAmt = master[1] * MM_MST

  # get devices from connection
  
	#send the commands
  if CONNECTED_TO_ZABER:
    deviceX = device_list[0]
    deviceY = device_list[1]
    deviceX.move_relative(xCmdAmt/100000, Units.LENGTH_MILLIMETRES)
    deviceY.move_relative(yCmdAmt/100000, Units.LENGTH_MILLIMETRES)
    # xCmd = zs.BinaryCommand(1, 21, xCmdAmt/10)  # create x command
    # yCmd = zs.BinaryCommand(2, 21, yCmdAmt/10)  # create y command

  
    # send the two commands to the zaber
    # port.write(xCmd)
    # port.write(yCmd)
  
	# write the report to the console
  if LOG_SENT_COMMANDS and False:
    print(str(PRE_CODE) + "Sent " + str(round(millis[0], SENT_COMMAND_PRECISION)) + " & " + str(round(millis[1], SENT_COMMAND_PRECISION)))

  
	# return the absolute position of the worm (where 0, 0 is zaber's 0, 0)
  # if CONNECTED_TO_ZABER:
  #   # return calculateWormPosition(master[2], master[3])
  # else:
  return 0, 0

# input is the centroid position in millimeters (relative to video feed)
# def calculateWormPosition(centroidX, centroidY):
#   # reads the current position from the zaber (note it's possible this could overflow if the framerate is too fast, but that would only cause small variances)
#   # xZab = float(port.read().data) / float(MM_MST)  # zaber x in mm
#   # yZab = float(port.read().data) / float(MM_MST)  # zaber y in mm

#   # calculate the worm's absolute positions
#   xPos = xZab + centroidX - TOTAL_MM_X/2
#   yPos = yZab + centroidY - TOTAL_MM_Y/2

#   print("X-"+str(xPos)+"\nY-"+str(yPos))

#   # returns the values
#   return xPos, yPos

# TRACKING MODE METHODS
# These should all return tuples with four items (stage move x, stage move y, rel worm pos x, rel worm pos y)

# intakes the xy of the centroid in pixels
def simpleToCenter(centroidX, centroidY):
  # calculate the percent the position is from the edge of the frame
  percentX = float(centroidX) / float(TOTAL_PIXELS_X)
  percentY = float(centroidY) / float(TOTAL_PIXELS_Y)

  # millimeters the position is from the edge
  millisX = percentX * TOTAL_MM_X
  millisY = percentY * TOTAL_MM_Y

  # millimeters the stage needs to move to catch up to the worm's position
  millisMoveX = ZABER_ORIENTATION_X * (millisX - TOTAL_MM_X/2)
  millisMoveY = ZABER_ORIENTATION_Y * (millisY - TOTAL_MM_Y/2)

  return millisMoveX, millisMoveY, millisMoveX, millisMoveY

if __name__ == "__main__":
  with Connection.open_serial_port("COM4") as connection:
    # CONNECT TO THE ZABER PORT
    #if not port.isOpen():
    #    port.open()

    device_list = connection.detect_devices()
    # print(device_list)
    main(device_list)
    #port.close()

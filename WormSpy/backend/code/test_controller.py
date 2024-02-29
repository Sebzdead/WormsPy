import pygame
from zaber_motion import Units
from zaber_motion.binary import Connection
from zaber_motion.binary import CommandCode
from pyzaber.serial import ZaberSerial

pygame.init()
pygame.joystick.init()

# Zaber device boundaries
MAXIMUM_DEVICE_XY_POSITION = 1066667
MAXIMUM_DEVICE_Z_POSITION = 209974
MINIMUM_DEVICE_POSITION = 0
XYmotorport = 'COM4'
Zmotorport = 'COM3'
manual_mode = False
tracking = False
recording = False

# Check if any joystick is connected
if pygame.joystick.get_count() > 0:
    # Get the first joystick
    joystick = pygame.joystick.Joystick(0)
    joystick.init()

    # Get the number of axes
    num_axes = joystick.get_numaxes()
    print("Number of axes:", num_axes)

    # Check if the joystick has at least 2 axes
    if num_axes >= 2:
        # Get the x and y input of the left joystick
        sticks_good = True
    else:
        print("Joystick does not have enough axes")
else:
    print("No joystick connected.")

with Connection.open_serial_port(XYmotorport) as connection:
    with Connection.open_serial_port(Zmotorport) as connection2:
        device_listXY = connection.detect_devices()
        device_listZ = connection2.get_device(1)

        while True:
            if joystick.get_button(0):
                manual_mode = not manual_mode
            if joystick.get_button(2):
                tracking = not tracking
            if joystick.get_button(1):
                recording = not recording
            
            xMotor = device_listXY[0]
            yMotor = device_listXY[1]
            zMotor = device_listZ[1]
            axis = zMotor.get_axis(1)

            xPos = xMotor.get_position(unit=Units.NATIVE)
            yPos = yMotor.get_position(unit=Units.NATIVE)
            zPos = zMotor.get_position(unit=Units.NATIVE)

            if sticks_good == True:
                input_x = joystick.get_axis(0)
                input_y = joystick.get_axis(1) * -1
                input_z = joystick.get_axis(4)
                #print("Joystick input - X:", input_x, "Y:", input_y)

                if (xPos < MAXIMUM_DEVICE_XY_POSITION
                or xPos > MINIMUM_DEVICE_POSITION
                or yPos < MAXIMUM_DEVICE_XY_POSITION
                or yPos > MINIMUM_DEVICE_POSITION
                or zPos < MAXIMUM_DEVICE_Z_POSITION
                or zPos > MINIMUM_DEVICE_POSITION):
                    xMotor.generic_command_no_response(
                        command=CommandCode.MOVE_RELATIVE, data=int(input_x * 1000))
                    yMotor.generic_command_no_response(
                        command=CommandCode.MOVE_RELATIVE, data=int(input_y * 1000))
                    axis.move_relative(input_z * 100)
            # Break the loop upon keypress
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        break
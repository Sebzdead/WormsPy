import pygame
from zaber_motion.ascii import Connection
from zaber_motion import Units

pygame.init()
pygame.joystick.init()

# Zaber device boundaries
MAXIMUM_DEVICE_XY_POSITION = 1066667
MAXIMUM_DEVICE_Z_POSITION = 209974
MINIMUM_DEVICE_POSITION = 0
XYmotorport = 'COM6'
Zmotorport = 'COM3'
manual_mode = False
tracking = False
recording = False

def start_controller(manual_mode: bool):
    # Check if any joystick is connected
    if pygame.joystick.get_count() > 0:
        # Get the first joystick
        joystick = pygame.joystick.Joystick(0)
        joystick.init()

        # Get the number of axes
        num_axes = joystick.get_numaxes()

        # Check if the joystick has at least 2 axes
        if num_axes >= 2:
            sticks_good = True
            print("Joystick count: ", pygame.joystick.get_count())
            print("Joystick axes: ", joystick.get_numaxes())
        else:
            print("Joystick does not have enough axes")
    else:
        print("No joystick connected.")

    with Connection.open_serial_port(XYmotorport) as connection:
        with Connection.open_serial_port(Zmotorport) as connection2:
            #connection.enable_alerts()

            horizontal_motors = connection.detect_devices()
            vertical_motor = connection2.detect_devices()
            print("Found {} devices on COM6".format(len(horizontal_motors)))
            print("Found {} devices on COM3".format(len(vertical_motor)))

            device_X = horizontal_motors[0]
            device_Y = horizontal_motors[1]
            device_Z = vertical_motor[0]

            xMotor = device_X.get_axis(1)
            print("X Motor: ", xMotor)
            yMotor = device_Y.get_axis(1)
            print("Y Motor: ", yMotor)
            zMotor = device_Z.get_axis(1)
            print("Z Motor: ", zMotor)

            try: 
                while manual_mode:
                    pygame.event.pump()

                    xPos = xMotor.get_position(unit=Units.NATIVE)
                    yPos = yMotor.get_position(unit=Units.NATIVE)
                    zPos = zMotor.get_position(unit=Units.NATIVE)

                    if sticks_good == True:
                        input_x = joystick.get_axis(0)
                        input_y = joystick.get_axis(1)
                        input_z = joystick.get_axis(3)
                        x_data = int(input_x * 2000)
                        y_data = int(input_y * 2000) * -1
                        z_data = int(input_z * 100)
                      
                    if (xPos + x_data < MAXIMUM_DEVICE_XY_POSITION
                    or xPos + x_data > MINIMUM_DEVICE_POSITION):
                        #print("Joystick input - X:", x_data)
                        xMotor.move_relative(x_data, unit = Units.NATIVE, wait_until_idle = False, velocity = 0, velocity_unit = Units.NATIVE, acceleration = 5, acceleration_unit = Units.NATIVE)

                    if (yPos + y_data < MAXIMUM_DEVICE_XY_POSITION
                    or yPos + y_data > MINIMUM_DEVICE_POSITION):
                        #print("Joystick input - Y:", y_data)
                        yMotor.move_relative(y_data, unit = Units.NATIVE, wait_until_idle = False, velocity = 0, velocity_unit = Units.NATIVE, acceleration = 5, acceleration_unit = Units.NATIVE)

                    if (zPos + z_data < MAXIMUM_DEVICE_Z_POSITION
                    or zPos + z_data > MINIMUM_DEVICE_POSITION):
                        #print("Joystick input - Z:", z_data)
                        zMotor.move_relative(z_data, unit = Units.NATIVE, wait_until_idle = False, velocity = 0, velocity_unit = Units.NATIVE, acceleration = 5, acceleration_unit = Units.NATIVE)

            except KeyboardInterrupt:
                print("Exiting...")
                pygame.quit()

if __name__=='__main__':
    start_controller(True)
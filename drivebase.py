from pybricks.hubs import InventorHub
from pybricks.robotics import DriveBase
from pybricks.tools import StopWatch, wait
import umath

from gyro import Gyro
from other import coroutine
from lightSensor import LightSensor


class Drivebase:
    """
    Handles all robot drive movements

    Includes:
    straight line, turning, line following, and more
    """
    def __init__(self, config, gyro, leftMotor, rightMotor, wheelDiameter, axleTrack):
        self.config = config
        self.hub: InventorHub = config.hub

        self.gyro: Gyro = gyro

        self.leftMotor = leftMotor
        self.rightMotor = rightMotor

        self.wheelDiameter = wheelDiameter
        self.axleTrack = axleTrack

        self.drive = DriveBase(self.leftMotor, self.rightMotor,
                               self.wheelDiameter, self.axleTrack)
        self.SPEEDLIST = [self.getSpeed(dist)
                          for dist in range(0, config.SPEED_LIST_COUNT)]

    def getSpeed(self, distance):
        return round(umath.sqrt(distance*2*self.config.ACCELERATION + self.config.STARTSPEED**2))

    def getHead(self):
        """
        Gets current heading
        """
        return (self.gyro.heading() + 180) % 360 - 180

    def setHead(self, angle=0):
        """
        Sets current heading
        """
        self.gyro.reset_heading(round(angle / self.gyro.multiplier))

    def sign(self, x):
        return 1 if x >= 0 else -1

    def limit(self, input, bound):
        return max(min(input, bound[1]), bound[0])

    def stop(self):
        self.drive.stop()

    def turnSpeed(self, angle):
        turn_speed = angle / 180 * (self.config.TURN_SPEED_MAX - self.config.TURN_SPEED_MIN) +\
            self.sign(angle) * self.config.TURN_SPEED_MIN
        return turn_speed

    def turnAngle(self, heading):
        return (heading - self.getHead() + 180) % 360 - 180

    @coroutine
    def turnTo(self, heading, tolerance=1, timeout=4000):
        """
        Turns the robot on the spot to a given heading
        """
        def _turnTo():
            angle = self.turnAngle(heading)
            runTime = StopWatch()
            while round(angle) not in range(-tolerance, tolerance) and runTime.time() < timeout:
                self.drive.drive(0, self.turnSpeed(angle))
                angle = self.turnAngle(heading)
                yield True
            self.stop()
            yield False
        return _turnTo

    def rampSpeed(self, distance, curr_distance, speedLimit):
        if curr_distance > distance / 2:
            delta_distance = round(abs(distance - curr_distance))
        else:
            delta_distance = round(abs(curr_distance))
        speed = self.SPEEDLIST[min(
            delta_distance, self.config.SPEED_LIST_COUNT-1)]
        return self.sign(speedLimit) * min(speed, abs(speedLimit))

    @coroutine
    def moveDist(self, distance, speed=500, heading=None, turn=True, up=True, down=True, timeout=None):
        """
        Moves the robot in a straight line for a given distance in a given heading

        Ramp up and down can be controlled by up and down flags
        """

        def _moveDist():
            posDistance = abs(distance)
            if speed < 0:
                print("Error Negative speed", speed)
                return
            
            if heading is None:
                head = self.getHead()
            else:
                head = heading
                if turn and abs(self.turnAngle(head)) > 5:
                    self.turnTo(head)

            rampSpeed_max = self.rampSpeed(posDistance, posDistance/2, speed)
            if timeout is None:
                # * 2000 to double time and convert to milliseconds
                time = (posDistance / rampSpeed_max) * 2 * 1000 + 500
            else:
                time = timeout
            # logData = []

            self.drive.reset()
            timer = StopWatch()
            while timer.time() < time:
                # print(runState.getStopFlag(), runButton.pressed())
                curr_distance = abs(self.drive.distance())
                if curr_distance >= posDistance:
                    break
                if up == False and curr_distance < posDistance/2:
                    drive_speed = speed
                elif down == False and curr_distance > posDistance/2:
                    drive_speed = speed
                else:
                    drive_speed = self.rampSpeed(posDistance, curr_distance, speed)

                self.drive.drive(drive_speed*self.sign(distance),
                                self.turnAngle(head) * self.config.TURN_CORRECTION_SPEED)

                yield True
                # print("Speed, drive_speed, distance: ", speed, drive_speed, \
                #        curr_distance)
                # logData.append([drive_speed, curr_distance])
            # print("MoveDist timeout=", timeout, "ms")
            self.stop()
            yield False

        return _moveDist

    @coroutine
    def lineFollower(self, distance: int, sensor: LightSensor, speed=250, side=1, kp=1.2, ki=0, kd=10):
        """
        Follows a line for a certain distance

        Requires a LightSensor object

        side is either 1 or -1, controls which side of the line it will follow

        PID constants can be tweaked through kp, ki, kd.
        """
        def _lineFollower():
            self.drive.reset()

            lastError = 0
            integral = 0

            curr_distance = abs(self.drive.distance())
            while curr_distance < distance:
                error = 60 - sensor.readLight()

                derivative = error - lastError
                lastError = error
                integral = (integral / 2) + error

                turnRate = (error * kp) + (derivative * kd) + (integral * ki)

                ramp_speed = self.rampSpeed(distance, curr_distance, speed)

                self.drive.drive(ramp_speed, turnRate * side)

                curr_distance = abs(self.drive.distance())

                yield True
            self.stop()
            yield False

        return _lineFollower

    @coroutine
    def moveArc(self, radius, heading, speed=100, timeout=10000):
        """
        Given a radius and end heading, moves the robot in an arc.

        sign of radius controls turning to left or right
        """
        def _moveArc():
            turn_rate = (360 * speed) / (umath.pi * 2 * radius)
            tolerance = int(2 * abs(speed) / 100)

            runTime = StopWatch()
            self.drive.drive(speed, turn_rate)
            while round(self.turnAngle(heading)) not in range(-tolerance, tolerance) and runTime.time() < timeout:
                yield True
            self.stop()
            yield False
        
        return _moveArc

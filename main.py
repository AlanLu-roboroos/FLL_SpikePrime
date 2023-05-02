from pybricks.hubs import InventorHub
from pybricks.pupdevices import Motor, ColorSensor, UltrasonicSensor
from pybricks.parameters import Button, Color, Direction, Port, Side, Stop, Icon
from pybricks.robotics import DriveBase
from pybricks.tools import wait, StopWatch

from micropython import const
from menu import menu
from config import Config

import other

m_config = Config()


m_menu = menu(m_config, [m_config.page1, m_config.page2], 50)

while True:
    m_menu.update()

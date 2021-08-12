"""
MInstance class
Independent instance of a minesweeper game
contains information about a single game of minesweeper on the screen

"""

import cv2
import numpy as np
import MLogicPlugin
import time
import pyautogui
from MCoordinate import MCoordinate
from MLogicPlugin import MLogicPlugin


class MInstance:
    id = 0

    def __init__(self, location_tuple):
        # locations (low,high)
        self.my_window_location, self.my_grid_location, tile_dims = location_tuple
        self.tile_width, self.tile_height = tile_dims
        self.grid_array = np.empty([30, 16])
        self.flags = 0
        self.is_complete = False

        self.id = MInstance.id
        MInstance.id += 1

    def get_id(self):
        print(self.id)

    def update(self, screen_snapshot):
        # 1) Receives screen snapshot
        # 2) Updates own array
        # 3) Uses logic plugin
        # 4) Cursor action
        k = MLogicPlugin(1, 1)
        self.cursor_control(k[0], k[1])

        #self.cursor_control((5, 5), 'left')

    def reset(self):
        self.grid_array = np.empty([30, 16])
        self.flags = 0
        self.is_complete = False

    def cursor_control(self, location, action):  # tells cursor to perform action at specific array[x,y] location.

        CURSOR_OFFSET_CORRECTION = MCoordinate(1, 1)
        lower_window_real_location = self.my_window_location[0]
        lower_grid_real_location = lower_window_real_location + self.my_grid_location[0]
        x_target = lower_grid_real_location.x + CURSOR_OFFSET_CORRECTION.x + self.tile_width * location[0]
        y_target = lower_grid_real_location.y + CURSOR_OFFSET_CORRECTION.y + self.tile_height * location[1]
        print("--------------------")
        print(x_target)
        print(y_target)
        print("--------------------")

        pyautogui.moveTo(x_target, y_target, duration=0)

        pyautogui.click(button=action)

    @staticmethod
    def update_array(grid_array):
        return grid_array

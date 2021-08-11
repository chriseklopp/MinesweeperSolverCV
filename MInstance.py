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


class MInstance:
    id = 0

    def __init__(self, location_tuple):

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

        self.cursor_control(*MLogicPlugin.logic_plugin(self.grid_array, self.flags))


    def reset(self):
        self.grid_array = np.empty([30, 16])
        self.flags = 0
        self.is_complete = False


    def cursor_control(self, location, action):  # tells cursor to perform action at specific array[x,y] location.

        self.my_window_location

    @staticmethod
    def update_array(grid_array):
        return grid_array


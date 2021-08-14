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
    feature_definitions = {'flag': ([0, 77, 188], [59, 255, 255]),
                           '0': ([0, 0, 0], [1, 1, 1]),
                           '1': ([0, 0, 0], [1, 1, 1]),
                           '2': ([44, 162, 87], [66, 255, 158]),
                           '3': ([0, 0, 0], [1, 1, 1]),
                           '4': ([97, 232, 64], [161, 255, 217]),
                           '5': ((0, 62, 107), (37, 255, 144)),
                           '6': ((63, 175, 96), (101, 255, 188)),
                           '7': ([0, 0, 0], [1, 1, 1]),
                           '8': ([0, 0, 0], [1, 1, 1]),
                           'mine': ([0, 0, 0], [1, 1, 1])
                           }
    id = 0

    def __init__(self, location_tuple):
        # locations (low,high)
        self.my_window_location, self.my_grid_location, self.tile_length = location_tuple
        self.grid_array = np.empty([30, 16])
        self.flags = 0
        self.is_complete = False

        self.id = MInstance.id
        MInstance.id += 1

    def get_id(self):
        print(self.id)

    def update(self, screen_snapshot):

        if self._detect_window_popup(screen_snapshot):
            # if this hits true trigger reset sequence.
            print("Window Detected")
            pass

        self.update_array(screen_snapshot)

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
        self.cursor_control([0, 0], 'left')  # ensures the correct window is selected
        pyautogui.press('escape')  # pressing escape while a window popup is active will start a new game.
        # pyautogui.press('n')

    def cursor_control(self, location, action):  # tells cursor to perform action at specific array[x,y] location.

        cursor_offset_correction = MCoordinate(self.tile_length/2, self.tile_length/2)
        lower_window_real_location = self.my_window_location[0]
        lower_grid_real_location = lower_window_real_location + self.my_grid_location[0]
        x_target = lower_grid_real_location.x + cursor_offset_correction.x + self.tile_length * location[0]
        y_target = lower_grid_real_location.y + cursor_offset_correction.y + self.tile_length * location[1]

        print("--------------------")
        print(x_target)
        print(y_target)
        print("--------------------")

        pyautogui.moveTo(x_target, y_target, duration=0)
        pyautogui.click(button=action)

    def update_array(self, screen_snapshot):

        #  process new screenshot into usable form
        lower_window_coords, upper_window_coords = self.my_window_location
        lower_grid_coords, upper_grid_coords = self.my_grid_location
        window = screen_snapshot[lower_window_coords.y:upper_window_coords.y,
                 lower_window_coords.x:upper_window_coords.x]
        grid_crop = window[lower_grid_coords.y:upper_grid_coords.y,
                    lower_grid_coords.x:upper_grid_coords.x]
        snapshot_hsv = cv2.cvtColor(grid_crop, cv2.COLOR_BGR2HSV)

        # detect locations of each feature, and insert into grid_array
        for feature, values in MInstance.feature_definitions.items():
            print(feature, values)
            feature_locations = self._detect_feature(values, snapshot_hsv)
            for location in feature_locations:
                array_x = round(location.x / self.tile_length)
                array_y = round(location.y / self.tile_length)
                self.grid_array[array_x, array_y] = 69
            print(self.grid_array)

    def _detect_window_popup(self, screen_snapshot):  # this would occur on a won or lost game. Must differentiate between win / lose
        print(screen_snapshot)
        return False

    @staticmethod
    def _detect_feature(values, snapshot_hsv):
        # temporary test purposes (hardcoded)

        lower = np.array(values[0])
        upper = np.array(values[1])
        mask = cv2.inRange(snapshot_hsv, lower, upper)

        #snapshot_gray = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)  # set to grayscale
        snapshot_blur = cv2.GaussianBlur(mask, (15, 15), 0)  # blur
        snapshot_bw = cv2.threshold(snapshot_blur, 50, 255, cv2.THRESH_BINARY)[1]
        snapshot_bw_inverted = cv2.bitwise_not(snapshot_bw)

        # cv2.imshow("mask", mask)
        # cv2.imshow("BW", snapshot_bw)
        # cv2.imshow("blurr", snapshot_blur)
        # cv2.imshow("inv", snapshot_bw_inverted)
        # cv2.waitKey(0)

        contours, hierarchy = cv2.findContours(snapshot_bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        detected_coordinates = []
        for cont in contours:
            area = cv2.contourArea(cont)
            if area > 10:
                moment = cv2.moments(cont)
                avg_x = int(moment["m10"] / moment["m00"])
                avg_y = int(moment["m01"] / moment["m00"])
                cv2.drawContours(mask, cont, -1, (0, 255, 0), 1)
                peri = cv2.arcLength(cont, True)
                approx = cv2.approxPolyDP(cont, .2 * peri, True)
                detected_coordinates.append(MCoordinate(avg_x, avg_y))

        # cv2.imshow("mask", mask)
        # cv2.waitKey(0)

        return detected_coordinates




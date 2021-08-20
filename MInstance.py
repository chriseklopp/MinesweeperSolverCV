"""
MInstance class
Independent instance of a minesweeper game
contains information about a single game of minesweeper on the screen

"""
import cv2
import numpy as np
import MLogicPlugin
import math
import time
import pyautogui
from MCoordinate import MCoordinate
from MLogicPlugin import MLogicPlugin


class MInstance:
    # flag must be last or 1 will (sometimes) overwrite it, this is a hacky solution but it should work fine
    # feature definiton value is tuple of (lower-hsv, upper-hsv, symmetry[TB,LR] )
    feature_definitions = {'0': ([0, 0, 0], [255, 255, 255], [0, 0]),
                           '1': ([95, 95, 162], [147, 255, 255], [0, 0]),  # 1 is still sometimes not being detected :(
                           '2': ([44, 162, 87], [66, 255, 158], [0, 0]),
                           '3': ([0, 101, 144], [37, 255, 202], [1, 0]),
                           '4': ([97, 232, 64], [161, 255, 217], [0, 0]),
                           '5': ((0, 62, 107), (37, 255, 144), [0, 0]),
                           '6': ((63, 175, 96), (101, 255, 188), [0, 0]),
                           '7': ([0, 0, 0], [255, 255, 255], [0, 0]),
                           '8': ([0, 0, 0], [255, 255, 255], [1, 1]),
                           '99': ([0, 77, 188], [59, 255, 255], [0, 0])
                           }
            # need to add definition for 0.
    id = 0

    def __init__(self, location_tuple):
        # locations (low,high)
        self.my_window_location, self.my_grid_location, self.tile_length = location_tuple
        self.grid_array = np.empty([30, 16])
        self.grid_array[:] = np.NaN
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
        self.debugarray = self.grid_array.transpose()
        # 1) Receives screen snapshot
        # 2) Updates own array
        # 3) Uses logic plugin
        # 4) Cursor action
        k = MLogicPlugin(1, 1)
        self.cursor_control(k[0], k[1])

        # self.cursor_control((5, 5), 'left')

    def reset(self):
        print(self.grid_array)
        # self.grid_array = np.empty([30, 16])
        # self.grid_array[:] = np.NaN
        self.flags = 0
        self.is_complete = False
        self.cursor_control([0, 0], 'left')  # ensures the correct window is selected
        pyautogui.press('escape')  # pressing escape while a window popup is active will start a new game.
        # pyautogui.press('n')

    def cursor_control(self, location, action):  # tells cursor to perform action at specific array[x,y] location.

        cursor_offset_correction = MCoordinate(self.tile_length / 2, self.tile_length / 2)
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
        # cv2.imwrite(r"images\masktest.png", grid_crop)                  #MASK DEBUGGING
        # detect locations of each feature, and insert into grid_array
        for feature, values in MInstance.feature_definitions.items():
            # print(feature, values)
            feature_locations = self._detect_feature(values, snapshot_hsv)
            for location in feature_locations:
                array_x = math.floor(location.x / self.tile_length)
                array_y = math.floor(location.y / self.tile_length)
                self.grid_array[array_x, array_y] = int(feature)  # FLAGS ARE GETTING PLACED IN SLIGHTLY WRONG SPOTS
            print(self.grid_array)

    def _detect_window_popup(self,
                             screen_snapshot):  # this would occur on a won or lost game. Must differentiate between win / lose
        print(screen_snapshot)
        return False

    def _detect_feature(self, values, snapshot_hsv):

        lower = np.array(values[0])
        upper = np.array(values[1])
        symmetry = np.array(values[2])
        mask = cv2.inRange(snapshot_hsv, lower, upper)

        # snapshot_gray = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)  # set to grayscale
        snapshot_blur = cv2.GaussianBlur(mask, (13, 13), 0)  # blur
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
            if 10 < area < self.tile_length ** 2:
            # if 10 < area:  # TEMPORARY DEBUG SWITCH BACK TO ORIGINAL
                moment = cv2.moments(cont)
                avg_x = int(moment["m10"] / moment["m00"])
                avg_y = int(moment["m01"] / moment["m00"])

                if symmetry[0] or symmetry[1]:
                    x, y, w, h = cv2.boundingRect(cont)
                    # if x and y:
                    tile_of_interest = snapshot_bw[y:y + h, x:x + w]
                    nrow, ncol = tile_of_interest.shape
                    # removes a row or col if total is odd, otherwise it will break
                    if nrow % 2 != 0:
                        tile_of_interest = tile_of_interest[:-1, :]
                    if ncol % 2 != 0:
                        tile_of_interest = tile_of_interest[:, :-1]

                    top_bottom_symmetry = self._detect_symmetry(tile_of_interest, 1)
                    left_right_symmetry = self._detect_symmetry(tile_of_interest, 0)

                    # if only top-bottom symmetry required
                    if symmetry[0] and not symmetry[1]:
                        if top_bottom_symmetry > .75 and left_right_symmetry < .75:
                            detected_coordinates.append(MCoordinate(avg_x, avg_y))
                        continue

                    # if only left-right symmetry required
                    if symmetry[1] and not symmetry[0]:
                        if left_right_symmetry > .75 and top_bottom_symmetry < .75:
                            detected_coordinates.append(MCoordinate(avg_x, avg_y))
                        continue

                    # if both symmetry required
                    if symmetry[0] and symmetry[1]:
                        if left_right_symmetry > .75 and top_bottom_symmetry > .75:
                            detected_coordinates.append(MCoordinate(avg_x, avg_y))
                        continue

                # cv2.drawContours(snapshot_hsv, cont, -1, (255, 255, 0), 2)
                peri = cv2.arcLength(cont, True)
                approx = cv2.approxPolyDP(cont, .05 * peri, True)
                # cv2.drawContours(snapshot_hsv, [approx], -1, (255, 255, 0), 2)
                # cv2.circle(snapshot_hsv, (avg_x, avg_y), radius=8, color=(255, 255, 0), thickness = -1)
                detected_coordinates.append(MCoordinate(avg_x, avg_y))

        # cv2.imshow("blah", snapshot_hsv)
        # cv2.imshow("mask", mask)
        # cv2.waitKey(0)

        return detected_coordinates

    @staticmethod
    def _detect_symmetry(tile_of_interest, is_vertical):
        nrow, ncol = tile_of_interest.shape
        # removes a row or col if total is odd, otherwise it will break
        if nrow % 2 != 0:
            tile_of_interest = tile_of_interest[:-1, :]
        if ncol % 2 != 0:
            tile_of_interest = tile_of_interest[:, :-1]
        nrow, ncol = tile_of_interest.shape

        rsplit, csplit = nrow // 2, ncol // 2

        top_bottom_symmetry = 0
        left_right_symmetry = 0

        if is_vertical:
            tile_upperhalf = tile_of_interest[:rsplit, :]
            tile_lowerhalf = tile_of_interest[rsplit:, :]
            tile_upperhalf_flipped = np.flip(tile_upperhalf, 0)
            top_bottom_intersection = cv2.bitwise_and(tile_lowerhalf, tile_upperhalf_flipped)
            top_bottom_union = cv2.bitwise_or(tile_lowerhalf, tile_upperhalf_flipped)
            top_bottom_symmetry = cv2.countNonZero(top_bottom_intersection) / \
                                  cv2.countNonZero(top_bottom_union)
            return top_bottom_symmetry

        if not is_vertical:
            tile_lefthalf = tile_of_interest[:, :csplit]
            tile_righthalf = tile_of_interest[:, csplit:]
            tile_lefthalf_flipped = np.flip(tile_lefthalf, 1)
            left_right_intersection = cv2.bitwise_and(tile_righthalf, tile_lefthalf_flipped)
            left_right_union = cv2.bitwise_or(tile_righthalf, tile_lefthalf_flipped)
            left_right_symmetry = cv2.countNonZero(left_right_intersection) / \
                                  cv2.countNonZero(left_right_union)
            return left_right_symmetry
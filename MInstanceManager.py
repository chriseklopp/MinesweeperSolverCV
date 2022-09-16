"""
MInstanceManager class
THIS CLASS IS A SINGLETON.
A single instance of this class is created on program startup.
Contains and manages all MInstance objects.
Handles creation/deletion of MInstance objects.

Currently, instances are only created on startup. This may change in the future

THIS WILL EVENTUALLY BE THE ONLY PUBLIC FACING CLASS
"""
import os

import cv2
import numpy as np
import random
import matplotlib
import pyautogui
import time
import pickle
from sklearn import svm

import MInstance
from MCoordinate import MCoordinate


class MInstanceManager:

    instances = []

    def __init__(self):
        my_screenshot = pyautogui.screenshot()  # takes and saves screenshot
        my_screenshot.save("images\sc.png")
        self.screenshot = cv2.imread("images\sc.png")  # debug, display basic screenshot

        # Try to find and load a SVM pickle for detecting mines and time.
        try:
            pickle_file = "MinesTime_SVM_model.sav"
            mines_time_model = pickle.load(open(os.path.join(os.getcwd(),pickle_file), 'rb'))
        except FileNotFoundError as e:
            raise FileNotFoundError(f"ERROR: SVM pickle not found in {os.getcwd()}.")

        self.mines_time_svm = pickle.load(open(r"C:\pyworkspace\minesweeper_proj\MinesTime_SVM_model.sav", 'rb'))
        self.potential_window_locations = []
        self.valid_window_locations = []
        self.valid_grid_locations = []
        self.valid_tile_dims = []
        self.frame_number = 0
        self._detect_windows()
        self._detect_grids()

        for i, window_loc in enumerate(self.valid_window_locations):
            grid_loc = self.valid_grid_locations[i]
            tile_dims = self.valid_tile_dims[i]
            time_loc, mines_remaining_loc = self._detect_mines_and_time(window_loc)
            new_instance = MInstance.MInstance((window_loc,
                                                grid_loc,
                                                tile_dims,
                                                mines_remaining_loc,
                                                time_loc,
                                                self.mines_time_svm))
            self.instances.append(new_instance)

            #DEBUG WILL BE REMOVED LATER
            # print("------------------------------------------------------")
            # print(window_loc)
            # print("------------------------------------------------------")
            # print(grid_loc)
            # print("------------------------------------------------------")
            # print("------------------------------------------------------")

    def update_all(self):  # updates ALL instances.
        self.frame_number += 1
        if self.instances:
            for instance in self.instances:
                if not instance.is_complete:
                    instance.update(self.screenshot)
                else:
                    instance.reset()

        else:
            print("FAILED TO UPDATE. NO ACTIVE INSTANCES")

    def reset_all(self):  # resets ALL instances. This message is passed up the chain
        if self.instances:
            for instance in self.instances:
                instance.reset()

    def _detect_windows(self):
        # Detect potential windows on the screen
        img_gray = cv2.cvtColor(self.screenshot, cv2.COLOR_BGR2GRAY)         # set to grayscale
        img_blurr = cv2.GaussianBlur(img_gray, (15, 15), 0)       # blur
        img_canny = cv2.Canny(img_blurr, 15, 255)  # edge detect
        contours, hierarchy = cv2.findContours(img_canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        cv2.drawContours(self.screenshot, contours[3], -1, (0, 255, 0), 3)

        for cont in contours:
            area = cv2.contourArea(cont)
            if area > 2000:
                cv2.drawContours(self.screenshot, cont, -1, (0, 255, 0), 1)
                peri = cv2.arcLength(cont, True)
                approx = cv2.approxPolyDP(cont, .2 * peri, True)

                lower_window_coords = MCoordinate(approx[0][0][0], approx[0][0][1])
                upper_window_coords = MCoordinate(approx[1][0][0], approx[1][0][1])
                self.potential_window_locations.append((lower_window_coords, upper_window_coords))

    def _detect_grids(self):
        for window_location in self.potential_window_locations:
            lower_window_coords, upper_window_coords = window_location

            window = self.screenshot[lower_window_coords.y:upper_window_coords.y,
                                     lower_window_coords.x:upper_window_coords.x]

            # Detect Grid Location within the window
            imgHSV = cv2.cvtColor(window, cv2.COLOR_BGR2HSV)
            imgGray = cv2.cvtColor(window, cv2.COLOR_BGR2GRAY)
            mask = cv2.inRange(imgHSV, np.array([0, 0, 120]), np.array([179, 254, 255]))
            mask = cv2.bitwise_not(mask)
            kernel = np.ones((1, 5), np.uint8)
            contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            for cont in contours:
                area = cv2.contourArea(cont)
                if area > 2000:
                    cv2.drawContours(window, cont, -1, (0, 255, 0), 1)
                    peri = cv2.arcLength(cont, True)
                    approx = cv2.approxPolyDP(cont, .2 * peri, True)

            lower_grid_coords = MCoordinate(approx[0][0][0]+1, approx[0][0][1])  # +1 is for a line detection correction
            upper_grid_coords = MCoordinate(approx[1][0][0], approx[1][0][1])
            # Calculate size of the tiles within the grid
            grid_width = upper_grid_coords.x - lower_grid_coords.x
            grid_height = upper_grid_coords.y - lower_grid_coords.y

            tile_width = round(grid_width / 30)
            tile_height = round(grid_height / 16)

            tile_length = max(tile_height, tile_width)  #  ensuring h and w are equal prevents drift from occuring

            # print(tile_width)
            # print(tile_height)

            self.valid_window_locations.append((lower_window_coords, upper_window_coords))
            self.valid_grid_locations.append((lower_grid_coords, upper_grid_coords))
            self.valid_tile_dims.append(tile_length)

            #BELOW IS DEBUG AND WILL BE REMOVED
            grid_crop = window[lower_grid_coords.y:upper_grid_coords.y,
                               lower_grid_coords.x:upper_grid_coords.x]

            tile_test = grid_crop[tile_height * 0:tile_height * 1, tile_width * 0:tile_width * 1]

            # window_BGR = cv2.cvtColor(window, cv2.COLOR_HSV2RGB)
            # cv2.imshow("window",window)
            # #cv2.imshow("window_bgr", window_BGR)
            # cv2.imshow("screenshot", self.screenshot)
            # cv2.imshow("grid", grid_crop)
            # cv2.imshow("tile", tile_test)
            cv2.imwrite(r"images\masktest.png", grid_crop)

    def _detect_mines_and_time(self, window_loc):
        # these are in the bottom ~7% of the window
        lower_win, upper_win = window_loc
        window = self.screenshot[lower_win.y:upper_win.y,
                                 lower_win.x:upper_win.x]

        window_height = upper_win.y - lower_win.y

        vertical_offset = round(.93*window_height)

        window = window[round(.93*window_height):, :]
        # Detect Grid Location within the window
        imgHSV = cv2.cvtColor(window, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(imgHSV, np.array([0, 67, 0]), np.array([179, 254, 255]))
        snapshot_blur = cv2.GaussianBlur(mask, (13, 13), 0)  # blur
        snapshot_bw = cv2.threshold(snapshot_blur, 50, 255, cv2.THRESH_BINARY)[1]
        kernel = np.ones((11, 11), np.uint8)
        eroded = cv2.erode(snapshot_bw, kernel)
        dilated = cv2.dilate(eroded, kernel)


        contours, hierarchy = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        detected_boxes = []
        for cont in contours:
            area = cv2.contourArea(cont)
            if 100 < area < 10000:  # TODO: Un-hardcode this and adjust bounds to make sense
                cv2.drawContours(window, cont, -1, (0, 255, 0), 1)
                peri = cv2.arcLength(cont, True)
                approx = cv2.approxPolyDP(cont, .2 * peri, True)
                detected_boxes.append(approx)

        ret_locations = []
        for box in detected_boxes:
            lower_mine_loc_coords = MCoordinate(box[0][0][0]+1, box[0][0][1]+vertical_offset)  # +1 is for a line detection correction
            upper_mine_loc_coords = MCoordinate(box[1][0][0], box[1][0][1]+vertical_offset+1)
            ret_locations.append((lower_mine_loc_coords, upper_mine_loc_coords))

        if len(ret_locations) != 2:
            print(f"WARNING: Mines and time not detected, num boxes found: {len(ret_locations)}")
        else:
            if ret_locations[1][0].x > ret_locations[0][1].x:
                ret_locations.reverse()

        # [Time location, Mines location]
        return ret_locations


if __name__ == "__main__":
    time.sleep(3)
    print("Running from MInstanceManager")
    print("DEBUG PURPOSES ONLY")
    manager = MInstanceManager()
    manager.update_all()
    cv2.waitKey(0)
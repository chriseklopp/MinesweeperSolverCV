"""
MInstanceManager class
THIS CLASS IS A SINGLETON.
A single instance of this class is created on program startup.
Contains and manages all MInstance objects.
Handles creation/deletion of MInstance objects.

Currently, instances are only created on startup. This may change in the future

THIS WILL EVENTUALLY BE THE ONLY PUBLIC FACING CLASS
"""


import cv2
import numpy as np
import random
import matplotlib
import pyautogui
import time

import MInstance


class MInstanceManager:

    instances = []

    def __init__(self):
        my_screenshot = pyautogui.screenshot()  # takes and saves screenshot
        my_screenshot.save("images\sc.png")
        self.screenshot = cv2.imread("images\sc.png")  # debug, display basic screenshot

        self.potential_window_locations = []
        self.valid_window_locations = []
        self.valid_grid_locations = []
        self.valid_tile_dims = []

        self._detect_windows()  # list of tuples of coordinates for each location
        self._detect_grids()  # list of tuple pairs of win,grid coord

        for i, window_loc in enumerate(self.valid_window_locations):
            grid_loc = self.valid_grid_locations[i]
            tile_dims = self.valid_tile_dims[i]
            new_instance = MInstance.MInstance((window_loc, grid_loc, tile_dims))
            self.instances.append(new_instance)


            print("------------------------------------------------------")
            print(window_loc)
            print("------------------------------------------------------")
            print(grid_loc)
            print("------------------------------------------------------")
            print(tile_dims[0], tile_dims[1])
            print("------------------------------------------------------")


    def update_all(self): # updates ALL instances.
        if self.instances:
            for instance in self.instances:
                if not instance.is_complate():
                    instance.update()

        else:
            print("FAILED TO UPDATE. NO ACTIVE INSTANCES")

    def reset_all(self): # resets ALL instances. This message is passed up the chain
        if self.instances:
            for instance in self.instances:
                instance.reset()

    def _detect_windows(self):
        # my_screenshot = pyautogui.screenshot() # takes and saves screenshot
        # my_screenshot.save("images\sc.png")
        # # my_screenshot.save("E:\PythonProjects\minesweeper_proj\sc.png")
        # img = cv2.imread("images\sc.png")         # debug, display basic screenshot
        # # cv2.imshow("Testerino",img)

        img_gray = cv2.cvtColor(self.screenshot, cv2.COLOR_BGR2GRAY)         # set to grayscale
        img_blurr = cv2.GaussianBlur(img_gray, (15, 15), 0)       # blurr
        img_canny = cv2.Canny(img_blurr, 15, 255) # edge detect

        contours, hierarchy = cv2.findContours(img_canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        cv2.drawContours(self.screenshot, contours[3], -1, (0, 255, 0), 3)

        for cont in contours:
            area = cv2.contourArea(cont)
            if area > 2000:
                cv2.drawContours(self.screenshot, cont, -1, (0, 255, 0), 1)
                peri = cv2.arcLength(cont, True)
                approx = cv2.approxPolyDP(cont, .2 * peri, True)

                low_window = approx[0][0]  # low and high contain coordinates to the minesweeper window
                high_window = approx[1][0]
                print(low_window)
                print(high_window)
                window = self.screenshot[low_window[1]:high_window[1], low_window[0]:high_window[0]]
                self.potential_window_locations.append((low_window, high_window))
        # crops to minesweeper window

                cv2.imwrite(r"images\cropwindow.png", window)

    def _detect_grids(self):
        # A valid minesweeper grid must be detected in the window.
        valid_grids_locations = []
        for window_location in self.potential_window_locations:
            low_window, high_window = window_location
        # for low_window, high_window in self.potential_window_locations:
            window = self.screenshot[low_window[1]:high_window[1], low_window[0]:high_window[0]]
            # get grid location within window
            #img = cv2.imread(r"images\cropwindow.png")
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
                    # print(peri)
                    # print(approx)

            low_grid = approx[0][0]  # low and high contains coordinates to the play grid within window
            high_grid = approx[1][0]  # each is list of [height,width] values
            print(low_grid)
            print(high_grid)

            # crop window to grid
            #window = self.screenshot[low_window[1]:high_window[1], low_window[0]:high_window[0]]
            grid_crop = window[low_grid[1]:high_grid[1], low_grid[0] + 1:high_grid[0]]  # +1 is for a line detection correction.

            grid_width = high_grid[0] - low_grid[0]  # width of grid
            grid_height = high_grid[1] - low_grid[1]  # height of grid  # MINESWEEPER GRID IS 30 x 16 (w x h)

            tile_width = int(grid_width / 30)
            tile_height = int(grid_height / 16)
            # print(grid_width, grid_height)
            # print(tile_width, tile_height)

            tile_test = grid_crop[tile_height * 0:tile_height * 1, tile_width * 0:tile_width * 1]

            print(grid_crop)

            # print(type(tile_test))
            # print(tile_test)
            # print(np.shape(tile_test))
            # print(np.average(tile_test))
            # tile_average = np.mean(tile_test)
            # print(np.mean((np.mean(tile_test, axis=2))))

            grid_BGR = cv2.cvtColor(window, cv2.COLOR_HSV2RGB)

            cv2.imshow("grid_bgr", grid_BGR)
            cv2.imshow("screenshot", self.screenshot)
            cv2.imshow("grid", grid_crop)
            cv2.imshow("tile", tile_test)
            cv2.imwrite(r"images\masktest.png", grid_crop)

            self.valid_window_locations.append((low_window, high_window))
            self.valid_grid_locations.append((low_grid, high_grid))
            self.valid_tile_dims.append((tile_width, tile_height))

if __name__ == "__main__":
    time.sleep(3)
    print("Running from MInstanceManager")
    print("DEBUG PURPOSES ONLY")
    manager = MInstanceManager()
    cv2.waitKey(0)
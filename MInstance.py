"""
MInstance class
Independent instance of a minesweeper game
contains information about a single game of minesweeper on the screen

"""
import cv2
import numpy as np

import datetime
import os
from MDataTypes import ActionTypes
from MDataTypes import MCoordinate

from MDataTypes import MAction
from MLogicPlugin import MLogicPlugin
import time
import win32api
import win32con
from MTileArray import MTileArray
from multiprocessing import shared_memory

# TODO: Add the crop locations instead of cropping twice, should be more optimal this way.


class MInstance:
    # flag must be last or 1 will (sometimes) overwrite it, this is a hacky solution but it should work fine
    # feature definiton value is tuple of (lower-hsv, upper-hsv, symmetry[TB,LR] )

    feature_definitions = {'1': ([85, 66, 130], [117, 255, 255], [0, 0]),
                           '2': ([44, 162, 87], [66, 255, 158], [0, 0]),
                           '3': ([0, 101, 144], [37, 255, 202], [1, 0]),  # 3 SOMETIMES SHOWN AS 7
                           '4': ([97, 232, 64], [161, 255, 217], [0, 0]),
                           '5': ([0, 62, 107], [37, 255, 144], [0, 0]),
                           '6': ([63, 175, 96], [101, 255, 188], [0, 0]),
                           '8': ([0, 101, 144], [37, 255, 202], [1, 1]),
                           '7': ([0, 101, 144], [37, 255, 202], [0, 0]),
                           '99': ([0, 77, 188], [59, 255, 255], [0, 0])  # FLAG DETECTION SOMETIMES FAILING
                           }

    # feature_definitions = {'1':  ([85, 66, 130], [117, 255, 255], [0, 0])}

    def __init__(self, instance_id,
                 location_tuple,
                 screenshot_shape,
                 instance_action_queue,  # Queue shared btwn processes
                 screenshot_published,  # Shared event
                 queue_unlocked,  # Shared event
                 sync_lock  # Shared event
                 ):

        self.SCREENSHOT_DIMENSIONS = screenshot_shape

        # SET SHARED PROCESS OBJECTS
        self.screenshot_memory = shared_memory.SharedMemory(name="ms_mem_share")  # Init access to our shared memory block.

        # Recreate the screenshot from the shared memory and save for use.
        self.screenshot = np.ndarray(screenshot_shape, dtype=np.uint8, buffer=self.screenshot_memory.buf)

        self.instance_action_queue = instance_action_queue
        self.screenshot_published = screenshot_published
        self.queue_unlocked = queue_unlocked
        self.sync_lock = sync_lock

        # SET GAME INSTANCE VARIABLES
        # locations (low,high)
        self.my_window_location, self.my_grid_location, self.tile_length, \
        self.my_time_location, self.my_mines_remaining_location, \
        self.mines_time_svm = location_tuple

        self.grid_array = MTileArray((16, 30))
        self.debugarray = self.grid_array.grid_array[:, :, 0].transpose()  # DEBUG PURPOSES
        self.flags = 0
        self.is_complete = False
        self.my_logic_plugin = MLogicPlugin(self.grid_array)
        self.id = instance_id

        # Begin the instance loop
        self.run()

    def run(self):
        # This is where interfacing between this process and the main process (MInstanceManager) will take place.
        while True:
            # TODO: Add Condition to kill process when necessary.

            # Wait for screenshot published event to continue
            self.screenshot_published.wait()

            # Now update our screenshot with the newly published one from shared_memory
            self.screenshot = np.ndarray(self.SCREENSHOT_DIMENSIONS, dtype=np.uint8, buffer=self.screenshot_memory.buf)

            # Update our mines_remaining and game time elapsed counters
            mines_remaining = self._detect_mines_remaining(self.screenshot)
            game_time = self._detect_game_time(self.screenshot)

            # Check for a window popup (indicating win or loss)
            if self._detect_window_popup(self.screenshot):
                status = ""
                if mines_remaining == 0:
                    status = "Win"
                    print("YOU WON!!")
                else:
                    print("YOU LOSE!!")
                    status = "Loss"
                time.sleep(5)
                #     self.grid_array = MTileArray((16, 30))  # this definitely shouldnt be hardcoded.
                #     self.flags = 0
                #     self.is_complete = False
                #
                action = MAction(ActionTypes.RESET, self.id, [status])

            else:

                results = self.update(self.screenshot)  # Update with the latest screenshot from MInstanceManager
                action = MAction(ActionTypes.SOLVE, self.id, results)

            # Wait if entry to queue is locked.
            self.queue_unlocked.wait()

            self.instance_action_queue.put(action)  # Put action in the shared queue

            # Wait if sync lock is closed
            self.sync_lock.wait()

    def get_id(self):
        print(self.id)

    def update(self, screen_snapshot):
        # 1) Receives screen snapshot
        # 2) Updates own array
        # 3) Uses logic plugin

        self.update_array(screen_snapshot)  # DEBUG: OLD METHOD ~.32 SEC
        self.debugarray = self.grid_array.grid_array[:, :, 0]  # DEBUG PURPOSES
        results = self.my_logic_plugin.update(self.grid_array)

        # Need to convert array coordinates to screen pixel coordinates.
        pixel_location_return = []
        for i in range(len(results)):
            y_location, x_location = results[i][0].values()
            cursor_offset_correction = MCoordinate(self.tile_length / 2, self.tile_length / 2)
            lower_window_real_location = self.my_window_location[0]
            lower_grid_real_location = lower_window_real_location + self.my_grid_location[0]
            x_target = lower_grid_real_location.x + cursor_offset_correction.x + self.tile_length * x_location + 1
            y_target = lower_grid_real_location.y + cursor_offset_correction.y + self.tile_length * y_location + 1

            pixel_location_return.append([MCoordinate(x_target, y_target), results[i][1]])

        return pixel_location_return

    def update_array(self, screen_snapshot):
        new_array = np.zeros((16, 30))
        #  process new screenshot into usable form
        lower_window_coords, upper_window_coords = self.my_window_location
        lower_grid_coords, upper_grid_coords = self.my_grid_location
        window = screen_snapshot[lower_window_coords.y:upper_window_coords.y,
                 lower_window_coords.x:upper_window_coords.x]
        grid_crop = window[lower_grid_coords.y:upper_grid_coords.y,
                    lower_grid_coords.x:upper_grid_coords.x]

        x = grid_crop.shape
        new_height = (x[0] + 16) - (x[0] % 16)
        new_width = (x[1] + 30) - (x[1] % 30)

        resized = cv2.resize(grid_crop, (new_width, new_height), interpolation=cv2.INTER_AREA)
        resized_hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
        tt = resized.shape

        tile_height = round(new_height / 16)
        tile_width = round(new_width / 30)

        # create feature masks for whole grid that can be sliced to the individual tiles
        feature_masks = {}
        for feature, values in MInstance.feature_definitions.items():
            lower = np.array(values[0])
            upper = np.array(values[1])
            grid_mask = cv2.inRange(resized_hsv, lower, upper)
            # snapshot_gray = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)  # set to grayscale
            grid_blur = cv2.GaussianBlur(grid_mask, (13, 13), 0)  # blur
            grid_bw = cv2.threshold(grid_blur, 50, 255, cv2.THRESH_BINARY)[1]
            feature_masks[feature] = grid_bw
            # cv2.imshow("grid_masks", grid_bw)
            # cv2.waitKey(0)

        # create mask for empty tile, as its a special case it is separate

        lower = np.array([58, 0, 0])
        upper = np.array([177, 62, 255])
        grid_mask = cv2.inRange(resized_hsv, lower, upper)
        grid_blur = cv2.GaussianBlur(grid_mask, (13, 13), 0)  # blur
        grid_bw_empty_tile = cv2.threshold(grid_blur, 50, 255, cv2.THRESH_BINARY)[1]

        # DEBUG: ABOVE HERE TAKES APPROX .0737
        # DEBUG: TOTAL TIME FOR BELOW SECTION IS .35
        # DEBUG: APPROX TIME FOR 1 TILE OF BELOW CODE IS : .000978

        for row in range(0, 16):
            tile_list = []
            for column in range(0, 30):
                x_target = tile_width * (row + 1)
                y_target = tile_height * (column + 1)
                # cv2.imshow("tile", tile_crop)
                # cv2.waitKey(0)
                match = False
                for feature, values in MInstance.feature_definitions.items():
                    tile_crop = feature_masks[feature][row * tile_width:x_target, column * tile_height:y_target]
                    match = self._detect_feature(values, tile_crop)
                    if match:
                        new_array[row, column] = int(feature)
                        end = time.time()
                        break

                if not match:
                    # detecting 0 tiles requires an alternative method since contour detection fucks shit up fam.
                    tile_bw = grid_bw_empty_tile[row * tile_width:x_target, column * tile_height:y_target]
                    tile_mean = tile_bw.mean()
                    if tile_mean / 255 > .95:
                        new_array[row, column] = int(0)
                    else:
                        new_array[row, column] = 77
        self.grid_array.update(new_array)

    def _detect_window_popup(self,
                             screen_snapshot):  # this would occur on a won or lost game.
        lower_window_coords, upper_window_coords = self.my_window_location
        lower_grid_coords, upper_grid_coords = self.my_grid_location
        window = screen_snapshot[lower_window_coords.y:upper_window_coords.y,
                 lower_window_coords.x:upper_window_coords.x]
        grid_crop = window[lower_grid_coords.y:upper_grid_coords.y,
                    lower_grid_coords.x:upper_grid_coords.x]
        grid_hsv = cv2.cvtColor(grid_crop, cv2.COLOR_BGR2HSV)
        lower = np.array([0, 0, 218])
        upper = np.array([179, 1, 255])
        grid_mask = cv2.inRange(grid_hsv, lower, upper)
        grid_blur = cv2.GaussianBlur(grid_mask, (13, 13), 0)
        grid_bw = cv2.threshold(grid_blur, 50, 255, cv2.THRESH_BINARY)[1]
        contours, hierarchy = cv2.findContours(grid_bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        for cont in contours:
            area = cv2.contourArea(cont)
            if (self.tile_length * 10) ** 2 > area > (self.tile_length * 3) ** 2:
                return True
        return False

    def _detect_feature(self, values, tile_bw):

        # lower = np.array(values[0])
        # upper = np.array(values[1])
        symmetry = np.array(values[2])
        # mask = cv2.inRange(tile_hsv, lower, upper)
        #
        # # snapshot_gray = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)  # set to grayscale
        # tile_blur = cv2.GaussianBlur(mask, (13, 13), 0)  # blur
        # tile_bw = cv2.threshold(tile_blur, 50, 255, cv2.THRESH_BINARY)[1]
        #

        # cv2.imshow("BW", tile_bw)
        # cv2.waitKey(0)

        contours, hierarchy = cv2.findContours(tile_bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        for cont in contours:
            area = cv2.contourArea(cont)
            peri = cv2.arcLength(cont, True)
            approx = cv2.approxPolyDP(cont, .05 * peri, True)
            # cv2.drawContours(tile_hsv, [approx], -1, (0, 255, 0), 3)
            if (self.tile_length ** 2) / 15 < area < (self.tile_length ** 2) / 2:

                # if 10 < area:  # TEMPORARY DEBUG SWITCH BACK TO ORIGINAL
                moment = cv2.moments(cont)
                avg_x = int(moment["m10"] / moment["m00"])
                avg_y = int(moment["m01"] / moment["m00"])

                if symmetry[0] or symmetry[1]:

                    x, y, w, h = cv2.boundingRect(cont)
                    tile_feature_crop = tile_bw[y:y + h, x:x + w]
                    # cv2.drawContours(tile_hsv, [approx], -1, (0, 255, 0), 3)

                    top_bottom_symmetry = self._detect_symmetry(tile_feature_crop, 1)
                    left_right_symmetry = self._detect_symmetry(tile_feature_crop, 0)

                    # if only top-bottom symmetry required
                    if symmetry[0] and not symmetry[1]:
                        if top_bottom_symmetry > .6 and left_right_symmetry < .75:
                            # detected_coordinates.append(MCoordinate(avg_x, avg_y))
                            return True
                        else:
                            # cv2.imshow("tile", tile_bw)
                            # cv2.waitKey(0)
                            return False

                    # if only left-right symmetry required
                    if symmetry[1] and not symmetry[0]:
                        if left_right_symmetry > .75 and top_bottom_symmetry < .6:
                            # detected_coordinates.append(MCoordinate(avg_x, avg_y))
                            return True
                        else:
                            return False

                    # if both symmetry required
                    if symmetry[0] and symmetry[1]:
                        if left_right_symmetry > .75 and top_bottom_symmetry > .6:
                            # detected_coordinates.append(MCoordinate(avg_x, avg_y))
                            return True
                        else:
                            return False
                # cv2.circle(snapshot_hsv, (avg_x, avg_y), radius=8, color=(255, 255, 0), thickness = -1)
                return True
                # detected_coordinates.append(MCoordinate(avg_x, avg_y))

        return False

    def _detect_mines_remaining(self, screen_snapshot):
        # Detect digits, use our trained model to classify them.

        lower_window_coords, upper_window_coords = self.my_window_location
        window = screen_snapshot[lower_window_coords.y:upper_window_coords.y,
                 lower_window_coords.x:upper_window_coords.x]

        lower_mine_coords, upper_mine_coords = self.my_mines_remaining_location
        mine_widget = window[lower_mine_coords.y:upper_mine_coords.y,
                      lower_mine_coords.x:upper_mine_coords.x]

        imgHSV = cv2.cvtColor(mine_widget, cv2.COLOR_BGR2HSV)
        bw_mask = cv2.inRange(imgHSV, np.array([0, 0, 199]), np.array([179, 254, 255]))

        contours, hierarchy = cv2.findContours(bw_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detected_digits = []  # type: list(tuple(image, x_location))
        for cont in contours:
            area = cv2.contourArea(cont)

            if 20 < area < 500:
                [x, y, w, h] = cv2.boundingRect(cont)
                digit_crop = bw_mask[y:y + h, x:x + w]
                digit_crop_normalized = cv2.resize(digit_crop, (10, 10))
                detected_digits.append((digit_crop_normalized, x))

                # # SAVE AND CREATE TRAINING DATA.
                # im_path = os.path.join(os.getcwd(),r"training\digits")
                # im_path = os.path.join(im_path, str(datetime.datetime.now().timestamp()))
                # im_path += ".png"
                # # print(im_path)
                # cv2.imwrite(im_path, digit_crop_normalized)

        mines = ""
        detected_digits.sort(key=lambda tup: tup[1])
        for digit in detected_digits:
            predicted = self.mines_time_svm.predict(digit[0].flatten().reshape(1, -1))
            mines += str(predicted[0])
        if not mines:
            print("ERROR: Mine counter failed to resolve properly!!")
            return 99  # As far as I can tell should be an unproblematic default value. It shouldnt really happen anyway
        return int(mines)

    def _detect_game_time(self, screen_snapshot):
        # Detect digits, use our trained model to classify them.

        lower_window_coords, upper_window_coords = self.my_window_location
        window = screen_snapshot[lower_window_coords.y:upper_window_coords.y,
                 lower_window_coords.x:upper_window_coords.x]

        lower_mine_coords, upper_mine_coords = self.my_time_location
        mine_widget = window[lower_mine_coords.y:upper_mine_coords.y,
                      lower_mine_coords.x:upper_mine_coords.x]

        imgHSV = cv2.cvtColor(mine_widget, cv2.COLOR_BGR2HSV)
        bw_mask = cv2.inRange(imgHSV, np.array([0, 0, 199]), np.array([179, 254, 255]))

        contours, hierarchy = cv2.findContours(bw_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detected_digits = []  # type: list(tuple(image, x_location))
        for cont in contours:
            area = cv2.contourArea(cont)

            if 20 < area < 500:
                [x, y, w, h] = cv2.boundingRect(cont)
                digit_crop = bw_mask[y:y + h, x:x + w]
                digit_crop_normalized = cv2.resize(digit_crop, (10, 10))
                detected_digits.append((digit_crop_normalized, x))

                # # SAVE AND CREATE TRAINING DATA.
                # im_path = os.path.join(os.getcwd(),r"training\digits")
                # im_path = os.path.join(im_path, str(datetime.datetime.now().timestamp()))
                # im_path += ".png"
                # # print(im_path)
                # cv2.imwrite(im_path, digit_crop_normalized)

        time_remaining = ""
        detected_digits.sort(key=lambda tup: tup[1])
        for digit in detected_digits:
            predicted = self.mines_time_svm.predict(digit[0].flatten().reshape(1, -1))
            time_remaining += str(predicted[0])
        if not time_remaining:
            print("ERROR: Time counter failed to resolve properly!!")
            return 0  # As far as I can tell should be an unproblematic default value. It shouldnt really happen anyway
        print(time_remaining)
        return int(time_remaining)

    @staticmethod
    def _detect_symmetry(tile_of_interest, is_vertical):

        # cv2.imshow("tileofinterest", tile_of_interest)
        # cv2.waitKey(0)

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

            # cv2.imshow("tile_upperhalf_flipped", tile_upperhalf_flipped)
            # cv2.imshow("tile_lowerhalf", tile_lowerhalf)
            # cv2.waitKey(0)
            return top_bottom_symmetry

        if not is_vertical:
            tile_lefthalf = tile_of_interest[:, :csplit]
            tile_righthalf = tile_of_interest[:, csplit:]
            tile_lefthalf_flipped = np.flip(tile_lefthalf, 1)
            left_right_intersection = cv2.bitwise_and(tile_righthalf, tile_lefthalf_flipped)
            left_right_union = cv2.bitwise_or(tile_righthalf, tile_lefthalf_flipped)
            left_right_symmetry = cv2.countNonZero(left_right_intersection) / \
                                  cv2.countNonZero(left_right_union)

            # cv2.imshow("tile_lefthalg_flipped", tile_lefthalf_flipped)
            # cv2.imshow("tile_righthalf", tile_righthalf)
            # cv2.waitKey(0)
            return left_right_symmetry

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

import pyautogui
import time
import pickle
from sklearn import svm
import MInstance
from MDataTypes import MCoordinate
import multiprocessing as mp
from multiprocessing import shared_memory
from MDataTypes import MAction
from MDataTypes import ActionTypes
import win32api
import win32con


class MInstanceManager:
    instances = []

    def __init__(self, memory_shared):
        my_screenshot = pyautogui.screenshot()  # takes and saves screenshot
        my_screenshot.save("images\sc.png")

        screenshot_array = cv2.cvtColor(np.array(my_screenshot), cv2.COLOR_RGB2BGR)

        # Necessary to know how to reconstruct our array inside instances.
        self.SCREENSHOT_DIMENSIONS = screenshot_array.shape

        # Now create a NumPy array backed by shared memory
        self.shared_block = np.ndarray(self.SCREENSHOT_DIMENSIONS, dtype=screenshot_array.dtype, buffer=memory_shared.buf)
        self.shared_block[:] = screenshot_array[:]  # Copy the original data into shared memory

        self.screenshot = screenshot_array

        # Try to find and load a SVM pickle for detecting mines and time.
        try:
            pickle_file = "MinesTime_SVM_model.sav"
            self.mines_time_svm = pickle.load(open(os.path.join(os.getcwd(), pickle_file), 'rb'))
        except FileNotFoundError as e:
            raise FileNotFoundError(f"ERROR: SVM pickle not found in {os.getcwd()}.")

        self.instance_action_queue = mp.Queue()
        self.screenshot_published = mp.Event()
        self.sync_lock = mp.Event()
        self.queue_unlocked = mp.Event()

        self.potential_window_locations = []
        self.valid_window_locations = []
        self.valid_grid_locations = []
        self.valid_tile_dims = []
        self.frame_number = 0
        self._detect_windows()
        self._detect_grids()

        # Map of (InstanceId : window_safe_point_location), used to ensure correct window selected.
        # In practice this location is simply the time_loc because we know its "safe" to click as it wont cause any
        # Windows (the OS) funkiness and isnt at risk of affecting the board.
        self.id_location_map = {}
        self.instance_count = 0
        instance_id = 0

        for i, window_loc in enumerate(self.valid_window_locations):
            instance_id += 1
            grid_loc = self.valid_grid_locations[i]
            tile_dims = self.valid_tile_dims[i]
            time_loc, mines_remaining_loc = self._detect_mines_and_time(window_loc)
            self.id_location_map[instance_id] = time_loc[0] + window_loc[0]

            # Create process for each instance.
            p = mp.Process(target=MInstance.MInstance, args=(instance_id,
                                                             (window_loc,
                                                              grid_loc,
                                                              tile_dims,
                                                              mines_remaining_loc,
                                                              time_loc,
                                                              self.mines_time_svm
                                                              ),
                                                             self.SCREENSHOT_DIMENSIONS,  # Screenshot dims
                                                             self.instance_action_queue,  # Queue shared btwn processes
                                                             self.screenshot_published,  # Shared event
                                                             self.queue_unlocked,  # Shared event
                                                             self.sync_lock  # Shared event
                                                             )
                           )
            p.start()
            self.instance_count += 1

    def run(self, refresh_rate):  # This is the main loop where cursor actions are taken and instances are syncronized.
        start_time = time.process_time()
        self.sync_lock.clear()
        self.screenshot_published.set()
        self.queue_unlocked.set()
        previous_id = 0
        frame = 0
        if self.instance_count == 0:
            print("EXITING: No active instances")
            return
        while True:  # TODO: While number of active instances > 0.
            # print(f"FRAME: {frame}")
            self.frame_number += 1
            actions_consumed = 0
            time.sleep(.01)
            # Lock queue to prevent any more instances from joining the wait for a screenshot.
            self.queue_unlocked.clear()

            # Remove the screenshot_published event to prevent instances from skipping a publishing
            self.screenshot_published.clear()

            # Open the sync lock to allow waiting instances to progress to waiting for the screenshot_published event
            self.sync_lock.set()

            # Consume the actions from instance_action_queue

            while not self.instance_action_queue.empty():
                # Each item in queue is MAction
                action = self.instance_action_queue.get()
                if previous_id != action.instance_id:
                    # Set necessary window to active on windows, otherwise our action clicks will not go through.
                    time.sleep(.01)
                    self.cursor_control(self.id_location_map[action.instance_id], "left")
                    time.sleep(.01)
                    previous_id = action.instance_id

                # A single return from an instance may contain multiple actions
                if action.atype == ActionTypes.SOLVE:
                    for cursor_loc, action in action.data:
                        self.cursor_control(cursor_loc, action)  # Carry out the action at given location
                        actions_consumed += 1
                elif action.atype == ActionTypes.RESET:
                    status = action.data[0]  # TODO: Utilize this when I implement logging.
                    self.reset_active_instance()
                    actions_consumed += 1
                else:
                    print("Unsupported Action Received.")
            # Make and publish screenshot
            if actions_consumed:
                win32api.SetCursorPos((0, 0))  # Return cursor to edge of screen so it doesn't get in the way.

            my_screenshot = pyautogui.screenshot()  # takes and saves screenshot
            screenshot_array = cv2.cvtColor(np.array(my_screenshot), cv2.COLOR_RGB2BGR)
            self.shared_block[:] = screenshot_array[:]  # Copy the original data into shared memory

            image = cv2.cvtColor(np.array(my_screenshot), cv2.COLOR_RGB2BGR)
            self.screenshot = image

            # Send screenshot published event to free waiting instances
            self.screenshot_published.set()

            # Close the sync lock to prevent instances from skipping out the end.
            self.sync_lock.clear()

            # Unlock the queue once more to allow for actions to be added.
            self.queue_unlocked.set()

            # If necessary, wait until next refresh, determined by refresh rate.
            end_time = time.process_time()
            if end_time - start_time < 1 / refresh_rate:
                time.sleep(1 / refresh_rate - (end_time - start_time))
            frame += 1

    @staticmethod
    def reset_active_instance():
        # Reset the target instance.
        time.sleep(.01)
        win32api.keybd_event(0x1B, 0, 0, 0)  # escape key
        time.sleep(.01)

    @staticmethod
    def cursor_control(location: MCoordinate, action='left'):
        # tells cursor to perform action at specific array[x,y] location.
        x_location,  y_location = location.values()
        win32api.SetCursorPos((int(x_location), int(y_location)))
        time.sleep(.01)
        if action == 'left':
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x_location, y_location, 0, 0)
            time.sleep(.01)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x_location, y_location, 0, 0)

        elif action == 'right':
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, x_location, y_location, 0, 0)
            time.sleep(.01)
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, x_location, y_location, 0, 0)

        elif action == 'double_left':
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x_location, y_location, 0, 0)
            time.sleep(.01)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x_location, y_location, 0, 0)
            time.sleep(.01)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x_location, y_location, 0, 0)
            time.sleep(.01)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x_location, y_location, 0, 0)

        else:
            print("---------------------------")
            print("INVALID ACTION SPECIFIED")
            print("---------------------------")
        time.sleep(.01)

    def _detect_windows(self):
        # Detect potential windows on the screen
        img_gray = cv2.cvtColor(self.screenshot, cv2.COLOR_BGR2GRAY)  # set to grayscale
        img_blurr = cv2.GaussianBlur(img_gray, (15, 15), 0)  # blur
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

            lower_grid_coords = MCoordinate(approx[0][0][0] + 1,
                                            approx[0][0][1])  # +1 is for a line detection correction
            upper_grid_coords = MCoordinate(approx[1][0][0], approx[1][0][1])
            # Calculate size of the tiles within the grid
            grid_width = upper_grid_coords.x - lower_grid_coords.x
            grid_height = upper_grid_coords.y - lower_grid_coords.y

            tile_width = round(grid_width / 30)
            tile_height = round(grid_height / 16)

            tile_length = max(tile_height, tile_width)  # ensuring h and w are equal prevents drift from occuring

            # print(tile_width)
            # print(tile_height)

            self.valid_window_locations.append((lower_window_coords, upper_window_coords))
            self.valid_grid_locations.append((lower_grid_coords, upper_grid_coords))
            self.valid_tile_dims.append(tile_length)

            # BELOW IS DEBUG AND WILL BE REMOVED
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

        vertical_offset = round(.93 * window_height)

        window = window[round(.93 * window_height):, :]
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
            lower_mine_loc_coords = MCoordinate(box[0][0][0] + 1,
                                                box[0][0][1] + vertical_offset)  # +1 is for a line detection correction
            upper_mine_loc_coords = MCoordinate(box[1][0][0]+5, box[1][0][1] + vertical_offset + 5)
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

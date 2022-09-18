"""
___________________MineSweeper AI _________________________
Detect MineSweeper Puzzles
Solve Puzzles
Record position of "guessing" spaces
Record Starting Position
    Fast and able to run repeatedly for many intervals
    Expert Minesweeper grid is 30x16 WxH
    """


import cv2
import numpy as np
import pyautogui
import time
from multiprocessing import shared_memory

import MInstanceManager


def main(memory_block):
    time.sleep(3)

    print("MineSweeper Bot V-0.5")

    manager = MInstanceManager.MInstanceManager(memory_block)

    print("Initialized Instances")
    print(manager.instance_count, " Game Instances Detected")

    manager.run(60)


if __name__ == "__main__":
    my_screenshot = pyautogui.screenshot()  # takes and saves screenshot
    screenshot_array = cv2.cvtColor(np.array(my_screenshot), cv2.COLOR_RGB2BGR)
    memory_share = shared_memory.SharedMemory(create=True, size=screenshot_array.nbytes, name="ms_mem_share")
    main(memory_share)


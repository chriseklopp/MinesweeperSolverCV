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
import random
import matplotlib
import pyautogui
import time
import cProfile


import MInstanceManager


def main():
    time.sleep(3)

    print("MineSweeper Bot V-0.5")

    manager = MInstanceManager.MInstanceManager()

    print("Initialized Instances")
    print(len(manager.instances), " Game Instances Detected")

    for i in range(0, 5000):
        my_screenshot = pyautogui.screenshot()  # takes and saves screenshot
        # my_screenshot.save("images\sc.png")
        # manager.screenshot = cv2.imread("images\sc.png")  # debug, display basic screenshot
        image = cv2.cvtColor(np.array(my_screenshot), cv2.COLOR_RGB2BGR)
        manager.screenshot = image
        manager.update_all()
        print("frame: ", manager.frame_number)
        print("-------------------------")
        print()


if __name__ == "__main__":
    # cProfile.run(main())
    main()

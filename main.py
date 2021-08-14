"""
___________________MineSweeper AI _________________________
Detect MineSweeper Puzzles
Solve Puzzles
Record position of "guessing" spaces
Complete Mode that will use guessing to attempt to finish the puzzle
Record Starting Position
Fast and able to run repeatedly for many intervals

Use monte carlo sims to predict probability of a mine in each square

Expert Minesweeper grid is 30x16 WxH
"""




import cv2
import numpy as np
import random
import matplotlib
import pyautogui
import time


import MInstanceManager


if __name__ == "__main__":
    time.sleep(3)
    print("MineSweeper Bot V-0.5")
    manager = MInstanceManager.MInstanceManager()
    print("Initializaed Instances")
    print(len(manager.instances), " Game Instances Detected")
    for i in range(0, 10):
        manager.update_all()
    manager.reset_all()
    #cv2.waitKey(0)

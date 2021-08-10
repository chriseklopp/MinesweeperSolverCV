"""
MInstance class
Independent instance of a minesweeper game
contains information about a single game of minesweeper on the screen
THIS IS TEMPORARILY PUBLIC FACING FOR DEBUG
"""

import MWindow
import MBoardState


class MInstance:
    id = 0

    def __init__(self):
        #on initialize, attempt to create unique MWindow object
        self.window
        self.grid
        self.window = MWindow.MWindow()
        self.boardState = MBoardState.MBoardState()
        self.id = MInstance.id
        self.is_complete = False
        MInstance.id +=1

    def get_id(self):
        print(self.id)

    def update(self):
        # Updates state of this minesweeper instance
        pass




m = MInstance()
m.get_id()
m.window.get_coords()

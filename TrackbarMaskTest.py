
import cv2
import trackbars
trackbars.hsvtrackbar(r"images\masktest.png")


img = cv2.imread(r"E:\PythonProjects\minesweeper_proj\masktest.png")

cv2.imshow("mask", img)
cv2.waitKey(0)




# [  0  77 188] [ 59 253 255] red flags mask
# [  0 101 144] [ 37 255 202] 3,7,8 mask (3,7,8 are same color figure this out)
# [ 63 175  96] [101 255 188] 6 mask
# [ 97 232  64] [161 255 217] 4 mask
# [ 44 162  87] [ 66 255 158] 2 mask
# [  0  62 107] [ 37 255 144] 5 mask
# [ 85  54 130] [117 255 255] 1 is somewhere in here. find a way to extract from unrevealed
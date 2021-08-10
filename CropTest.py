import trackbars
import cv2
import numpy as np

# trackbars.hsvtrackbar(r"E:\PythonProjects\minesweeper_proj\images\cropwindow.png")

# get grid location within window
img = cv2.imread(r"images\cropwindow.png")
imgHSV = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
imgGray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
mask = cv2.inRange(imgHSV, np.array([0,0,120]), np.array([179,254,255]))
mask = cv2.bitwise_not(mask)
kernel = np.ones((1,5),np.uint8)
contours, hierarchy = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
for cont in contours:
    area = cv2.contourArea(cont)
    if area > 2000:
        cv2.drawContours(img,cont,-1,(0,255,0),1)
        peri = cv2.arcLength(cont,True)
        approx = cv2.approxPolyDP(cont,.2*peri,True)
        # print(peri)
        print(approx)

low_grid = approx[0][0]  #low and high contains coordinates to the play grid within window
high_grid = approx[1][0] #each is list of [height,width] values
print(low_grid)
print(high_grid)

# crop window to grid
grid_crop = img[low_grid[1]:high_grid[1], low_grid[0]+1:high_grid[0]] # +1 is for a line detection correction.

grid_width = high_grid[0]-low_grid[0] # width of grid
grid_height = high_grid[1]-low_grid[1] # height of grid  # MINESWEEPER GRID IS 30 x 16 (w x h)
tile_width = int(grid_width/30)
tile_height = int(grid_height/16)
print(grid_width,grid_height)
print(tile_width,tile_height)
tile_test = grid_crop[tile_height*0:tile_height*1, tile_width*0:tile_width*1]
cv2.imshow("croppy",grid_crop)
cv2.imshow("tile",tile_test)

cv2.imwrite(r"E:\PythonProjects\minesweeper_proj\images\masktest.png",grid_crop)

cv2.waitKey(0)







# # mask = cv2.inRange(imgHSV, lower, upper)

# # [53 71 21] [179 239  77]
# # apply this mask


#soncider blur to hsv

def hsvtrackbar(img_path):

    import cv2
    import numpy as np
    # create window
    cv2.namedWindow("TrackBarWindow")
    cv2.resizeWindow('TrackBarWindow', 640,240)

    #trackbars
    def track(x):
        print(lower,upper)
    cv2.createTrackbar("huemin","TrackBarWindow",0,179,track)
    cv2.createTrackbar("huemax","TrackBarWindow",179,179,track)
    cv2.createTrackbar("satmin","TrackBarWindow",0,255,track)
    cv2.createTrackbar("satmax","TrackBarWindow",255,255,track)
    cv2.createTrackbar("valmin","TrackBarWindow",0,255,track)
    cv2.createTrackbar("valmax","TrackBarWindow",255,255,track)

    while True:
        img = cv2.imread(img_path)
        imgHSV = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
        h_min = cv2.getTrackbarPos("huemin","TrackBarWindow")
        h_max = cv2.getTrackbarPos("huemax","TrackBarWindow")
        s_min = cv2.getTrackbarPos("satmin","TrackBarWindow")
        s_max = cv2.getTrackbarPos("satmax","TrackBarWindow")
        v_min = cv2.getTrackbarPos("valmin","TrackBarWindow")
        v_max = cv2.getTrackbarPos("valmax","TrackBarWindow")
        lower = np.array([h_min,s_min,v_min])
        upper = np.array([h_max,s_max,v_max])
        mask = cv2.inRange(imgHSV,lower,upper)
        imgResult = cv2.bitwise_and(img,img,mask=mask)
        cv2.imshow("OG", img)
        cv2.imshow("Mask",mask)
        cv2.imshow("Result",imgResult)
        if cv2.waitKey(1) &0xFF == ord('t'):
            cv2.imwrite(r"images\mask.png", mask)
            print(mask)
            return (mask)

        if cv2.waitKey(1) &0xFF == ord('q'):
            break

def gbetrackbar(img):
    #greyscale,apply blurr, edge detect, dilate/erode.
    import cv2
    import numpy as np
    # create window
    cv2.namedWindow("TrackBarWindow")
    cv2.resizeWindow('TrackBarWindow', 640, 240)
    # trackbars
    def track(x):
        pass

    cv2.createTrackbar("Blur1", "TrackBarWindow", 1, 20, track)
    cv2.createTrackbar("Blur2", "TrackBarWindow", 1, 20, track)
    cv2.createTrackbar("Edgemin", "TrackBarWindow", 0, 500, track)
    cv2.createTrackbar("Edgemax", "TrackBarWindow", 0, 500, track)
    cv2.createTrackbar("erode", "TrackBarWindow", 0, 15, track)
    cv2.createTrackbar("dilate", "TrackBarWindow", 0, 15, track)

    while True:
        # img = cv2.imread(img_path)
        imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        imgGray = cv2.bitwise_not(imgGray)
        gray_filtered = cv2.bilateralFilter(imgGray, 7, 50, 50)
        blur1 = cv2.getTrackbarPos("Blur1","TrackBarWindow")
        blur2 = cv2.getTrackbarPos("Blur2","TrackBarWindow")
        edgemin = cv2.getTrackbarPos("Edgemin","TrackBarWindow")
        edgemax = cv2.getTrackbarPos("Edgemax","TrackBarWindow")
        erode = cv2.getTrackbarPos("erode","TrackBarWindow")
        dilate = cv2.getTrackbarPos("dilate","TrackBarWindow")

        if blur1 % 2 == 0:
            blur1 += 1
        if blur2 % 2 == 0:
            blur2 += 1

        imgBlur = cv2.GaussianBlur(gray_filtered, (blur1, blur2), 0)

        imgCanny = cv2.Canny(imgBlur, edgemin, edgemax)
        kernel = np.ones((5,5),np.uint8)
        imgerdil = imgCanny.copy()

        if dilate > 0:
            imgerdil = cv2.dilate(imgerdil, kernel, iterations=dilate)
        if erode > 0:
            imgerdil = cv2.erode(imgerdil, kernel, iterations=erode)
        cv2.imshow("gray", imgGray)
        cv2.imshow("Result", imgerdil)
        if cv2.waitKey(1) &0xFF == ord('q'):
            break
# print(img)
# print(img.shape)
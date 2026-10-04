import numpy as np
import mss
import cv2

class ScreenCapture:
    def __init__(self):
        self.sct = mss.mss()

    def grab_region(self, x: int, y: int, width: int, height: int) -> np.ndarray:
        monitor = {
            "top": int(y),
            "left": int(x),
            "width": int(width),
            "height": int(height)
        }
        screenshot = self.sct.grab(monitor)
        frame_bgra = np.array(screenshot)
        frame_bgr = cv2.cvtColor(frame_bgra, cv2.COLOR_BGRA2BGR)
        return frame_bgr

    def close(self):
        self.sct.close()
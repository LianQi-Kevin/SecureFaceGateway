import cv2
import numpy as np


# png to jpg with opencv
def png_to_jpg(img_blob: bytes) -> bytes:
    """Convert PNG to JPG"""
    img = cv2.imdecode(np.frombuffer(img_blob, np.uint8), cv2.IMREAD_UNCHANGED)
    _, img_encoded = cv2.imencode(".jpg", img)
    return img_encoded.tobytes()

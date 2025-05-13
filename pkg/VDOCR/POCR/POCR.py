# POCR - PaddleOCR (Text Detection)

# ----- Usage -----
# from pkg.VDOCR.POCR.POCR import Process_POCR
# bboxes = Process_POCR("_test/img_0.jpg", padding_ratio=0.2)

# ====================================================================================================

from onnxruntime import InferenceSession
from PIL import Image
import numpy as np
import math
import cv2

# ====================================================================================================

class POCR_Detection:
    def __init__(self, onnx_path):
        self.session = InferenceSession(onnx_path)
        self.inputs = self.session.get_inputs()[0]
        self.min_size = 3
        self.max_size = 960
        self.box_thresh = 0.8
        self.mask_thresh = 0.8
        self.mean = np.array([123.675, 116.28, 103.53]).reshape(1, -1).astype('float64')   # imagenet mean
        self.std  = 1 / np.array([58.395, 57.12, 57.375]).reshape(1, -1).astype('float64') # imagenet std

    def util_filter_polygon(self, points, shape):
        width = shape[1]
        height = shape[0]
        filtered_points = []
        for point in points:
            if type(point) is list:
                point = np.array(point)
            point = self.clockwise_order(point)
            point = self.clip(point, height, width)
            w = int(np.linalg.norm(point[0] - point[1]))
            h = int(np.linalg.norm(point[0] - point[3]))
            if w <= 3 or h <= 3:
                continue
            filtered_points.append(point.astype(np.int32))
        return filtered_points

    def util_boxes_from_bitmap(self, output, mask, dest_width, dest_height):
        mask = (mask * 255).astype(np.uint8)
        height, width = mask.shape
        outs = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        if len(outs) == 2:
            contours = outs[0]
        else:
            contours = outs[1]
        boxes = []
        scores = []
        for index in range(len(contours)):
            contour = contours[index]
            points, min_side = self.get_min_boxes(contour)
            if min_side < self.min_size:
                continue
            points = np.array(points)
            score = self.box_score(output, contour)
            if self.box_thresh > score:
                continue
            box, min_side = self.get_min_boxes(points)
            if min_side < self.min_size + 2:
                continue
            box = np.array(box)
            box[:, 0] = np.clip(np.round(box[:, 0] / width * dest_width), 0, dest_width)
            box[:, 1] = np.clip(np.round(box[:, 1] / height * dest_height), 0, dest_height)
            boxes.append(box.astype("int32"))
            scores.append(score)
        return np.array(boxes, dtype="int32"), scores

    @staticmethod
    def get_min_boxes(contour):
        bounding_box = cv2.minAreaRect(contour)
        points = sorted(list(cv2.boxPoints(bounding_box)), key=lambda x: x[0])
        if points[1][1] > points[0][1]:
            index_1 = 0
            index_4 = 1
        else:
            index_1 = 1
            index_4 = 0
        if points[3][1] > points[2][1]:
            index_2 = 2
            index_3 = 3
        else:
            index_2 = 3
            index_3 = 2
        box = [points[index_1], points[index_2], points[index_3], points[index_4]]
        return box, min(bounding_box[1])

    @staticmethod
    def box_score(bitmap, contour):
        h, w = bitmap.shape[:2]
        contour = contour.copy()
        contour = np.reshape(contour, (-1, 2))
        x1 = np.clip(np.min(contour[:, 0]), 0, w - 1)
        y1 = np.clip(np.min(contour[:, 1]), 0, h - 1)
        x2 = np.clip(np.max(contour[:, 0]), 0, w - 1)
        y2 = np.clip(np.max(contour[:, 1]), 0, h - 1)
        mask = np.zeros((y2 - y1 + 1, x2 - x1 + 1), dtype=np.uint8)
        contour[:, 0] = contour[:, 0] - x1
        contour[:, 1] = contour[:, 1] - y1
        contour = contour.reshape((1, -1, 2)).astype("int32")
        cv2.fillPoly(mask, contour, color=(1, 1))
        return cv2.mean(bitmap[y1:y2 + 1, x1:x2 + 1], mask)[0]

    @staticmethod
    def clockwise_order(point):
        poly = np.zeros((4, 2), dtype="float32")
        s = point.sum(axis=1)
        poly[0] = point[np.argmin(s)]
        poly[2] = point[np.argmax(s)]
        tmp = np.delete(point, (np.argmin(s), np.argmax(s)), axis=0)
        diff = np.diff(np.array(tmp), axis=1)
        poly[1] = tmp[np.argmin(diff)]
        poly[3] = tmp[np.argmax(diff)]
        return poly

    @staticmethod
    def clip(points, h, w):
        for i in range(points.shape[0]):
            points[i, 0] = int(min(max(points[i, 0], 0), w - 1))
            points[i, 1] = int(min(max(points[i, 1], 0), h - 1))
        return points

    def resize(self, image):
        h, w = image.shape[:2]
        # limit the max side
        if max(h, w) > self.max_size:
            if h > w:
                ratio = float(self.max_size) / h
            else:
                ratio = float(self.max_size) / w
        else:
            ratio = 1.
        resize_h = max(int(round(int(h * ratio) / 32) * 32), 32)
        resize_w = max(int(round(int(w * ratio) / 32) * 32), 32)
        return cv2.resize(image, (resize_w, resize_h))

    @staticmethod
    def zero_pad(image):
        h, w, c = image.shape
        pad = np.zeros((max(32, h), max(32, w), c), np.uint8)
        pad[:h, :w, :] = image
        return pad

    def __call__(self, img_ocv):
        h, w = img_ocv.shape[:2]
        if sum([h, w]) < 64:
            img_ocv = self.zero_pad(img_ocv)
        img_ocv = self.resize(img_ocv)
        img_ocv = img_ocv.astype('float32')
        cv2.subtract(img_ocv, self.mean, img_ocv)  # inplace
        cv2.multiply(img_ocv, self.std, img_ocv)   # inplace
        img_ocv = img_ocv.transpose((2, 0, 1))
        img_ocv = np.expand_dims(img_ocv, axis=0)
        outputs = self.session.run(None, {self.inputs.name: img_ocv})[0]
        outputs = outputs[0, 0, :, :]
        boxes, scores = self.util_boxes_from_bitmap(outputs, outputs > self.mask_thresh, w, h)
        return self.util_filter_polygon(boxes, (h, w))

# ====================================================================================================

def x1y1wh_2_x1y1x2y2_add_padding(bbox, padding_ratio, ogimg_width, ogimg_height):
    x, y, w, h = bbox
    padding_y = math.ceil(h * padding_ratio)           # padding_y = height x ratio
    padding_x = math.ceil(h * padding_ratio * 2)       # padding_x = height x ratio * 2
    x_min, y_min = max(x-padding_x, 0), max(y-padding_y, 0)
    x_max, y_max = min(x+w+padding_x, ogimg_width), min(y+h+padding_y, ogimg_height)
    return (x_min, y_min, x_max, y_max)

# ====================================================================================================

POCR_DET = POCR_Detection(onnx_path='pkg/VDOCR/POCR/model/det_infer.onnx')
# POCR_DET = POCR_Detection(onnx_path='pkg/VDOCR/POCR/model/ch_PP-OCRv3_det_infer.onnx')
# POCR_DET = POCR_Detection(onnx_path='pkg/VDOCR/POCR/model/ch_PP-OCRv2_det_infer.onnx')
# POCR_DET = POCR_Detection(onnx_path='pkg/VDOCR/POCR/model/en_PP-OCRv3_det_infer.onnx')

def Process_POCR(img_path, padding_ratio=0.2):

    # Convert to OpenCV image
    if isinstance(img_path, str):             img_ocv = cv2.imread(img_path)
    elif isinstance(img_path, Image.Image):   img_ocv = cv2.cvtColor(np.array(img_path), cv2.COLOR_RGB2BGR)
    elif isinstance(img_path, np.ndarray):    img_ocv = img_path
    else:                                     raise ValueError("⚠️ POCR > Not image path, PIL image, or OpenCV image")

    pocr_obboxs = list(POCR_DET(img_ocv))
    pocr_bboxes = [x1y1wh_2_x1y1x2y2_add_padding(bb, padding_ratio=padding_ratio, ogimg_width=img_ocv.shape[1], ogimg_height=img_ocv.shape[0]) for bb in [cv2.boundingRect(obb) for obb in pocr_obboxs]]

    # # # ---------------------------------------------------------------------------------------------------- Just to visualize
    # from pkg.UTILS.UTILS import show_ocv
    # img_tmp = img_ocv.copy()
    # for i, (x1, y1, x2, y2) in enumerate(pocr_bboxes):
    #     cv2.polylines(img_tmp, [pocr_obboxs[i]], True, (0, 0, 255), 1)
    #     cv2.rectangle(img_tmp, (x1, y1), (x2, y2), (255, 0, 0), 1)
    #     cv2.putText(img_tmp, f"{i}", (x1-32, y1+18), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
    # show_ocv(img_tmp)
    # # # ----------------------------------------------------------------------------------------------------

    return pocr_bboxes
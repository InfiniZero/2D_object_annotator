import cv2
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage

def cvimg_to_qtimg(cvimg):
    height, width, depth = cvimg.shape
    cvimg = cv2.cvtColor(cvimg, cv2.COLOR_BGR2RGB)
    cvimg = QImage(cvimg.data, width, height, width *
                   depth, QImage.Format_RGB888)
    return cvimg

class ImageLabel(QLabel):
    imagelabelSig = pyqtSignal(str)
    imagelabelDoubleClickSig = pyqtSignal(str)

    def __init__(self, parent=None):
        super(ImageLabel, self).__init__(parent)
        self.bbox_list = list()
        self.p_1 = (0, 0)
        self.p_2 = (0, 0)
        self.img_name = ''
        self.image_original = None
        self.image = None
        self.move_flag = False
        self.class_id = 1
        self.x_max = 0
        self.y_max = 0

    def update_img(self, img, img_name):
        self.img_name = img_name
        self.bbox_list = list()
        self.image_original = img.copy()
        self.image = img.copy()
        self.x_max = self.image.shape[1]
        self.y_max = self.image.shape[0]
    
    def update_class(self, class_id):
        self.class_id = class_id

    def clean_img(self):
        self.bbox_list = list()
        self.image = self.image_original.copy()

    def mousePressEvent(self, event):    # 单击
        if event.buttons() == Qt.LeftButton:
            coor_x = max(min(event.x(), self.x_max), 0)
            coor_y = max(min(event.y(), self.y_max), 0)
            self.p_1 = (coor_x, coor_y)
        else:
            pass

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move_flag = True
            move_xx = max(min(event.x(), self.x_max), 0)
            move_yy = max(min(event.y(), self.y_max), 0)
            self.p_2 = (move_xx, move_yy)
            image_rect = self.image.copy()
            cv2.rectangle(image_rect, self.p_1, self.p_2, (255, 0, 0), 2)
            self.setPixmap(QPixmap(cvimg_to_qtimg(image_rect)))
            sig_content = self.objectName()
            self.imagelabelSig.emit(sig_content)
        else:
            pass

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.move_flag:
            self.move_flag = False
            cv2.rectangle(self.image, self.p_1, self.p_2, (255, 0, 0), 2)
            bbox = [self.p_1[0], self.p_1[1], (self.p_2[0]-self.p_1[0]), (self.p_2[1]-self.p_1[1])]
            bbox_dict = {'bbox': bbox, 'class': self.class_id}
            self.bbox_list.append(bbox_dict)
        else:
            pass
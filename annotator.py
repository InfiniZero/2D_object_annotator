import os
import cv2
import sys
import json
import argparse
from image_label import ImageLabel, cvimg_to_qtimg
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QLineEdit
from PyQt5.QtCore import Qt, QRect, QEvent
from PyQt5.QtGui import QPixmap, QImage


class Window(QWidget):
    def __init__(self, args):
        super().__init__()
        self.annotation_path = args.label_file
        self.scale_factor = args.scale
        self.annotaion_dict = dict()
        self.img_list = list()
        self.img_name = list()
        img_list = os.listdir(args.img_dir)
        for i in range(len(img_list)):
            if img_list[i].endswith('jpg') or img_list[i].endswith('png'):
                img_path = os.path.join(args.img_dir, img_list[i])
                self.img_list.append(img_path)
                self.img_name.append(img_list[i])
        self.img_num = len(self.img_list)
        self.img_id = 0
        self.class_id = 1
        if self.img_num == 0:
            return
        self._read_img()
        self.region_img_view = ImageLabel(self)
        self.region_img_view.setPixmap(
            QPixmap(cvimg_to_qtimg(self.current_img_resize)))
        self.region_img_view.setMouseTracking(True)
        self.region_img_view.update_img(
            self.current_img_resize, self.img_name[self.img_id])

        self.button_width = 400*self.scale_factor
        self.button_height = 60*self.scale_factor
        self.pushButton1 = QPushButton(self)
        self.pushButton1.setText("Next Img")
        self.pushButton1.clicked.connect(self._down_func)
        self.pushButton2 = QPushButton(self)
        self.pushButton2.setText("Last Img")
        self.pushButton2.clicked.connect(self._up_func)
        self.pushButton3 = QPushButton(self)
        self.pushButton3.setText("Apply")
        self.pushButton3.clicked.connect(self._apply_func)
        self.pushButton4 = QPushButton(self)
        self.pushButton4.setText("Clean")
        self.pushButton4.clicked.connect(self._clean_func)
        self.pushButton5 = QPushButton(self)
        self.pushButton5.setText("Output")
        self.pushButton5.clicked.connect(self._output_func)

        if args.mode == "multi":
            self.class_text_height = 30*self.scale_factor
            self.class_text_width = 100*self.scale_factor
            self.class_text_label = QLabel(self)
            self.class_text_label.setAlignment(Qt.AlignCenter)
            self.class_text_label.setText('Class ID:')
            self.setup_class_id = QLineEdit(self)
            self.setup_class_id.setFocus()
            self.setup_class_id.setFocusPolicy(Qt.ClickFocus)
            self.setup_class_id.installEventFilter(self)
            self.setup_class_id.editingFinished.connect(
                self._setup_class_id_func)
        else:
            self.setup_class_id = QLabel(self)
            self.setup_class_id.setFocus()
            self.setup_class_id.setFocusPolicy(Qt.ClickFocus)
            self.setup_class_id.installEventFilter(self)
        self.setWindowTitle('Simple 2D Object Annotator')
        self._init_window()

    def eventFilter(self, source, event):
        if (event.type() == QEvent.KeyPress and source is self.setup_class_id):
            if event.key() == Qt.Key_Up:
                self.pushButton2.click()
            if event.key() == Qt.Key_Down:
                self.pushButton1.click()
        return super(Window, self).eventFilter(source, event)

    def _setup_class_id_func(self):
        setup_class_id_str = self.setup_class_id.text()
        if setup_class_id_str != '':
            try:
                self.class_id = int(setup_class_id_str)
                self.region_img_view.update_class(self.class_id)
            except Exception as e:
                print(e)

    def _init_window(self):
        window_width = self.img_width + self.button_width + 20
        if args.mode == "multi":
            other_height = 5 * (self.button_height + 10) + \
                self.class_text_height + 10
            self.setup_class_id.setGeometry(
                QRect(self.img_width+20+self.class_text_width, 10 + (10+self.button_height)*5,
                      self.class_text_width, self.class_text_height))
            self.class_text_label.setGeometry(
                QRect(self.img_width+10, 10 + (10+self.button_height)*5,
                      self.class_text_width, self.class_text_height))
        else:
            other_height = 5 * (self.button_height + 10)
        window_height = max(self.img_height, other_height + 10)
        self.setGeometry(100, 100, window_width, window_height)
        self.region_img_view.setGeometry(
            QRect(0, 0, self.img_width, self.img_height))
        self.pushButton1.setGeometry(
            QRect(self.img_width+10, 10, self.button_width, self.button_height))
        self.pushButton2.setGeometry(
            QRect(self.img_width+10, 10 + (10+self.button_height), self.button_width, self.button_height))
        self.pushButton3.setGeometry(
            QRect(self.img_width+10, 10 + (10+self.button_height)*2, self.button_width, self.button_height))
        self.pushButton4.setGeometry(
            QRect(self.img_width+10, 10 + (10+self.button_height)*3, self.button_width, self.button_height))
        self.pushButton5.setGeometry(
            QRect(self.img_width+10, 10 + (10+self.button_height)*4, self.button_width, self.button_height))

    def _read_img(self):
        img_original = cv2.imread(self.img_list[self.img_id])
        image_resize = cv2.resize(
            img_original, None, fx=self.scale_factor, fy=self.scale_factor)
        height, width, _ = image_resize.shape
        self.current_img_resize = image_resize
        self.current_img = img_original
        self.img_height = height
        self.img_width = width

    def _reshape_bbox(self, bbox_list):
        bbox_resize_list = list()
        for item in bbox_list:
            x = int(item['bbox'][0]/self.scale_factor)
            y = int(item['bbox'][1]/self.scale_factor)
            w = int(item['bbox'][2]/self.scale_factor)
            h = int(item['bbox'][3]/self.scale_factor)
            bbox_dict = {'bbox': [x, y, w, h], 'class': item['class']}
            bbox_resize_list.append(bbox_dict)
        return bbox_resize_list

    def _down_func(self):
        self.img_id += 1
        if self.img_id == self.img_num:
            self.img_id = self.img_num - 1
        self._read_img()
        self._init_window()
        self.region_img_view.update_img(
            self.current_img_resize, self.img_name[self.img_id])
        self.region_img_view.setPixmap(
            QPixmap(cvimg_to_qtimg(self.current_img_resize)))
        self.region_img_view.update_class(self.class_id)
        self.setup_class_id.setFocus()

    def _up_func(self):
        self.img_id -= 1
        if self.img_id == -1:
            self.img_id = 0
        self._read_img()
        self._init_window()
        self.region_img_view.update_img(
            self.current_img_resize, self.img_name[self.img_id])
        self.region_img_view.setPixmap(
            QPixmap(cvimg_to_qtimg(self.current_img_resize)))
        self.region_img_view.update_class(self.class_id)
        self.setup_class_id.setFocus()

    def _apply_func(self):
        image_local = self.current_img_resize.copy()
        for item in self.region_img_view.bbox_list:
            bbox = item['bbox']
            class_id = item['class']
            class_id_str = "class: " + str(class_id)
            cv2.rectangle(
                image_local, (bbox[0], bbox[1]), (bbox[0]+bbox[2], bbox[1]+bbox[3]), (0, 255, 0), 2)
            cv2.putText(image_local, class_id_str,
                        (bbox[0], bbox[1]+15), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 1)
        self.region_img_view.setPixmap(QPixmap(cvimg_to_qtimg(image_local)))
        bbox_resize_list = self._reshape_bbox(self.region_img_view.bbox_list)
        self.annotaion_dict[self.img_name[self.img_id]] = bbox_resize_list
        self.setup_class_id.setFocus()

    def _clean_func(self):
        self.region_img_view.clean_img()
        self.region_img_view.setPixmap(
            QPixmap(cvimg_to_qtimg(self.current_img_resize)))
        self.annotaion_dict[self.img_name[self.img_id]] = []
        self.setup_class_id.setFocus()

    def _output_func(self):
        json_str = json.dumps(self.annotaion_dict, indent=1)
        with open(self.annotation_path, 'w') as file:
            file.write(json_str)
        self.setup_class_id.setFocus()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simple 2D Object Annotator')
    parser.add_argument('--mode', type=str, default='single',
                        help='single_class or multi_class')
    parser.add_argument('--scale', type=float, default=1.0,
                        help='annotator scale factor')
    parser.add_argument('--img_dir', type=str, default='dataset/image/',
                        help='image dir path')
    parser.add_argument('--label_file', type=str, default='dataset/label/annotation.json',
                        help='label file path')
    args = parser.parse_args()
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    window = Window(args)
    window.show()
    sys.exit(app.exec_())

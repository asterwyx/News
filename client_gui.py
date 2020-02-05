import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QCoreApplication


class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):

        btn = QPushButton("Quit", self)
        btn.resize(btn.sizeHint())
        btn.move(50, 50)
        btn.clicked.connect(QCoreApplication.instance().quit)

        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle("Hello")
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MyWidget()
    # w.resize(250, 150)
    w.move(300, 300)
    w.setWindowTitle("Test Window")
    # 显示在屏幕上
    w.show()

    # 实现一个按钮的退出功能

    sys.exit(app.exec_())

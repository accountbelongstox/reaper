from kernel.base.base import *
import sys
from PySide6 import QtCore, QtWidgets, QtGui,QtWidgets

class QtMode(BaseClass):
    __app_width = 1200
    __app_widget = 800


    def __init__(self,args):
        pass


    def main(self,args):
        # app = QtWidgets.QApplication(args)
        # widget = MyWidget()
        # widget.resize(self.__app_width, self.__app_widget)
        # widget.show()
        # print(f"app {app}")
        # # ...
        # sys.exit(app.exec())
        pass

class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.button = QtWidgets.QPushButton("点这里")

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.button)
        self.button.clicked.connect(self.showMessage)

    @QtCore.Slot()
    def showMessage(self):
        msgBox = QtWidgets.QMessageBox()
        msgBox.setText("Hello world")
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        ret = msgBox.exec()
import sys
from PyQt5.QtWidgets import  *


class GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.iniUI()
        self.buttonClicked()

    def iniUI(self):
        self.setWindowTitle("seo优化界面")
        self.resize(400, 200)
        #设置文本框
        self.text_browser = QTextBrowser(self)
        self.text_browser.move(30, 30)
        self.text_browser.resize(340, 100)
        #设置滚动条
        # self.text_browser.setLineWrapMode(0)
        # self.text_browser.setObjectName("text_browser")
        self.text_browser.setLineWrapMode(QTextEdit.FixedPixelWidth)
        #设置输入框
        self.qle = QLineEdit(self)
        self.qle.setPlaceholderText("请输入网址...")
        self.qle.move(30, 150)
        self.qle.resize(220,30)
        #设置确定按钮
        btn1 = QPushButton("确定", self)
        btn1.move(270, 150)
        # 绑定信号和槽
        btn1.clicked.connect(self.buttonClicked)

    #定义槽函数
    def buttonClicked(self):
        self.text_browser.setText(self.qle.text())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = GUI()
    gui.show()
    sys.exit(app.exec_())
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QMainWindow

class MainWindow(QMainWindow):
    def __init__(self, parent=None, title='PyQt5 Application', windowSize=(800,600)):
        super(MainWindow, self).__init__(parent=parent)
        self.setWindowTitle(title)
        self.resize(windowSize[0], windowSize[1])
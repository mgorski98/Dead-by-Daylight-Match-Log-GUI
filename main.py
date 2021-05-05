import sys
from PyQt5.QtWidgets import QApplication
from MainWindow import MainWindow

def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow(title='Dead by Daylight match log', windowSize=(1200, 800))
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
import sys
from PyQt6.QtWidgets import QApplication
from controller.controller import ReportCreator

def main():

    app = QApplication(sys.argv)
    app.demo = ReportCreator()
    app.demo.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

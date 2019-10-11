from sys import argv,exit
from dataShow import Ui_MainWindow
from os import path, system, popen
from plot import readDataFrom, plot_dynamic, plot_static
from PyQt5.QtCore import pyqtSignal, QObject, QEvent
from PyQt5.QtWidgets import QApplication, QMainWindow, QDesktopWidget, QLCDNumber

# MainWindow.resize(1280, 800)        # Zum Aendern

def clickable(widget, i):
    # Implement a customized signal that will be emitted when the mouse is pressed and released,
    # used to bind the corresponding slot function to implement a custom mouse-down callback function.
    class Filter(QObject):
        # Variable id marks which lcdNumber was pressed.
        id = i
        # Initialize a pyqt signal for customization.
        clicked = pyqtSignal()

        def eventFilter(self, obj, event):
            # Overwrite the method "eventFilter" of the inherited official class QObject of pyqt.
            if obj == widget:
                if event.type() == QEvent.MouseButtonRelease:
                    # Determine whether the mouse is pressed in the range of the pyqt component
                    # corresponding to the parameter passed by the function, i.e. lcdNumber.
                    if obj.rect().contains(event.pos()):
                        # The custom pyqt signal is emitted, and the slot function bound to it is automatically triggered.
                        self.clicked.emit()
                        return True
            return False

    filter = Filter(widget)
    widget.installEventFilter(filter)
    # Return a custom pyqt signal to bind a slot function。
    return filter.clicked


class mainWindow(QMainWindow):
    # can also directly inherit the Ui_MainWindow class, this eliminates the need to initialize the main_window object,
    # and replace it with self in all places where self.main_window is used.

    def __init__(self):
        super(mainWindow, self).__init__()
        # Initialize the class Ui_MainWindow, call the object method setupUi to generate a graphical interface for displaying sensor data.
        self.main_window = Ui_MainWindow()
        self.main_window.setupUi(self)

        self.main_window.actionReStart.triggered.connect(lambda: system("sudo reboot"))
        self.main_window.actionShutdown.triggered.connect(lambda: system("sudo shutdown -h now"))
        self.main_window.actionRefresh.triggered.connect(self.refresh)
        self.main_window.actionEnd_Programm.triggered.connect(self.endProgramm)
        self.main_window.actionMinwindow.triggered.connect(self.minWindow)

        self.initLcdNumber()    # Initialize all 104 lcdNumber components

    def refresh(self):
        # The effect of refreshing the interface can be achieved by maximizing and minimizing the graphical interface,
        # and is suitable for use when the display of the interface has a long delay.
        self.showMinimized()
        self.showFullScreen()

    def minWindow(self):
        self.showMinimized()

    def endProgramm(self):
        # End the program by ending the process in which the program is located
        with popen('ps -ef | grep python') as f:
            for line in f.readlines():
                if "/home/pi/Luftdrucksensor_RPi/main.py" in line:
                    pid = line.split()[1]
                    break
        system('kill -1 ' + str(pid))

    def center(self):
        qr = self.frameGeometry()  # Get the virtual frame of the graphics window
        cp = QDesktopWidget().availableGeometry().center()  # Get the center point of the screen of the display
        qr.moveCenter(cp)  # Move the center point of the virtual frame to the center of the screen
        self.move(qr.topLeft())  # Move the real graphics window to the center of the screen

    def initLcdNumber(self):
        for i in range(1, 105):     # A total of 13 * 8 = 104 LcdNumber
            lcdNumber_name = eval("self.main_window.lcdNumber_" + str(i))   # Dynamically named variable
            lcdNumber_name.setDigitCount(4)  # Set the maximum number of characters displayed by the lcdNumber
            lcdNumber_name.setMode(QLCDNumber.Dec)  # Set the display mode of the lcdNumber to decimal
            lcdNumber_name.setStyleSheet("background: gray;")  # The initial background color of all lcdNumber is gray

            #clickable(lcdNumber_name, i).connect(lambda: showText(self))
            # Pass lcdNumber and i as arguments to the method clickable to generate a custom signal corresponding to it.
            # Each signal is bound to a slot function.
            clickable(lcdNumber_name, i).connect(lambda : showData(self))



def showData(source):
    sender_id = source.sender().id
    data_from_file, data_from_col = readDataFrom(sender_id)
    local_path = path.split(path.realpath(__file__))[0]
    if path.exists(path.join(local_path,data_from_file)):
        plot_dynamic(data_from_file, data_from_col)

def showText(source):

    print(source.sender().id)


if __name__ == "__main__":
    app = QApplication(argv)
    win = mainWindow()
    win.show()
    exit(app.exec_())

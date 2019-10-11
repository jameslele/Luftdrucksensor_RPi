from re import search
from shutil import copyfile
from os import path, system
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtCore import QThread, pyqtSignal
from configurationsShow import Ui_Configuration
from getUSBpath import get_U_path, get_USB_path
from configuration import doAPconfig, doStaConfig
from setmark import setMark_inMaster, setMark_inUSB
from PyQt5.QtWidgets import QWidget, QMessageBox, QDesktopWidget

class configurationsWindow(QWidget):
    def __init__(self):
        # create a main window
        super(configurationsWindow, self).__init__()
        # The interface and the logic are separated, and the newly generated graphics window is introduced into
        # the initialization method setupUi of the class Ui_Configuration for setting the interface layout, etc.,
        # and all the layout settings of the interface are bound to the main window for the network configuration.
        self.configuration_window = Ui_Configuration()
        self.configuration_window.setupUi(self)

        # Position the graphics window to the middle of the screen
        self.center()
        # Create a message box
        self.msgBox = QMessageBox()

        # Create a child thread that detects the insertion or removal of the USB flash drive continuously
        self.sub_thread = SubThread()
        # Start running the child thread to detect the insertion or removal of the USB disk
        self.sub_thread.start()

        # Get the local path of the program. For example "/home/pi/Luftdrucksensor_RPi"
        self.local_path = path.split(path.realpath(__file__))[0]
        # Initialize network configuration information in the object attributes
        self.initConfigData()
        # Connect some signals and slot functions
        self.setSignalSlot()

        # Execute the function to check the U disk connection to pop up the prompt message box.
        # Executed before the main window for the network configuration pops up.
        self.do_config = True
        self.checkUSBatBegin()

    def initConfigData(self):
        # Initialize network configuration information
        self.ssid = ['0', '0', '0', '0', '0', '0', '0', '0', '0']
        self.password = ['12345678', '12345678', '12345678', '12345678', '12345678', '12345678', '12345678', '12345678',
                         '12345678']

    def center(self):
        # Position the graphics window to the middle of the screen

        # Get the window frame
        qr = self.frameGeometry()
        # Get the screen center point of the display
        cp = QDesktopWidget().availableGeometry().center()
        # Move the center point of the virtual frame to the center of the screen
        qr.moveCenter(cp)
        # Move the real window to the center of the screen
        self.move(qr.topLeft())

    def checkUSBatBegin(self):
        # Check if usb is connected. When the USB flash drive is not connected, a warning message box will pop up.
        # It is called at the beginning to prompt the user to insert a USB flash drive.
        if get_U_path() == None:  # No U disk is connected.
            # The warning message box has an "Ok" button by default, which is selected by default.
            self.msgBox.setText(
                'Opening GUI for the network configration......\nU-Disk not found, please insert a readable U-Disk first.\nYou can also cancel the network configuration by clicking the cancel button or closing this message box.')
            self.msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            self.msgBox.setDefaultButton(QMessageBox.Ok)
            self.msgBox.setIcon(QMessageBox.Warning)
            self.msgBox.setWindowTitle('Warning')
            clicked = self.msgBox.exec_()

            # The message box will close automatically when the "Cancel" button is pressed.
            # The graphical interface for network configuration no longer appears. A graphical interface for presenting data will appear.
            if clicked == QMessageBox.Cancel:
                self.do_config = False
            else:
                # The message box will also close automatically when the "Ok" button is pressed.
                # After the message box is closed, it will detect whether the USB disk is inserted again.
                # If not, the warning message box still pops up.
                if get_U_path() == None:
                    self.checkUSBatBegin()

    def setSignalSlot(self):
        # Create a connection between the two signals emitted by the child process and the two slot functions that generate the message box
        # Bind the signal "inserted" to the slot function "usbInserted"
        self.sub_thread.inserted.connect(self.usbInserted)
        # Bind the signal "pulled_out" to the slot function "usbPulledOut"
        self.sub_thread.pulled_out.connect(self.usbPulledOut)

        # Set the signal slots of the nine spinboxes
        self.configuration_window.spinBox_0.valueChanged.connect(self.changeSSIDOfmyshow)
        self.configuration_window.spinBox_1.valueChanged.connect(self.changeSSIDOfmyshow)
        self.configuration_window.spinBox_2.valueChanged.connect(self.changeSSIDOfmyshow)
        self.configuration_window.spinBox_3.valueChanged.connect(self.changeSSIDOfmyshow)
        self.configuration_window.spinBox_4.valueChanged.connect(self.changeSSIDOfmyshow)
        self.configuration_window.spinBox_5.valueChanged.connect(self.changeSSIDOfmyshow)
        self.configuration_window.spinBox_6.valueChanged.connect(self.changeSSIDOfmyshow)
        self.configuration_window.spinBox_7.valueChanged.connect(self.changeSSIDOfmyshow)
        self.configuration_window.spinBox_8.valueChanged.connect(self.changeSSIDOfmyshow)

        # Set up nine qlineedit signal slots
        self.configuration_window.Password_0.textEdited.connect(self.changePasswordOfmyshow)
        self.configuration_window.Password_1.textEdited.connect(self.changePasswordOfmyshow)
        self.configuration_window.Password_2.textEdited.connect(self.changePasswordOfmyshow)
        self.configuration_window.Password_3.textEdited.connect(self.changePasswordOfmyshow)
        self.configuration_window.Password_4.textEdited.connect(self.changePasswordOfmyshow)
        self.configuration_window.Password_5.textEdited.connect(self.changePasswordOfmyshow)
        self.configuration_window.Password_6.textEdited.connect(self.changePasswordOfmyshow)
        self.configuration_window.Password_7.textEdited.connect(self.changePasswordOfmyshow)
        self.configuration_window.Password_8.textEdited.connect(self.changePasswordOfmyshow)

        # Set the signal slot of the two buttons
        self.configuration_window.Cancel.clicked.connect(self.slotOfCancel)
        self.configuration_window.Ok.clicked.connect(self.slotOfOk)

    def changeSSIDOfmyshow(self):
        # Slot function that will be triggered when the spinbox value that stores ssid of network configuration is modified

        # First judge the sender, then get the value in the corresponding box of the sender,
        # and then synchronize all the values in all spinbox and the attributes of the object attribute "ssid".
        sender = self.sender()
        ssidList = [self.configuration_window.spinBox_0, self.configuration_window.spinBox_1, self.configuration_window.spinBox_2,
                    self.configuration_window.spinBox_3, self.configuration_window.spinBox_4, self.configuration_window.spinBox_5,
                    self.configuration_window.spinBox_6, self.configuration_window.spinBox_7, self.configuration_window.spinBox_8]
        for i in range(9):
            # Synchronize the values in all spinboxes
            if ssidList[i] != sender:
                ssidList[i].setValue(sender.value())
            # Unify the values of all elements in the object attribute "ssid"
            self.ssid[i] = str(sender.value())

    def changePasswordOfmyshow(self):
        # Slot function that will be triggered when the QLineEdit value that stores password of network configuration is modified

        # First judge the sender, then get the value in the corresponding box of the sender,
        # and then synchronize all the values in all QLineEdit and the attributes of the object attribute "password".
        sender = self.sender()
        passwordList = [self.configuration_window.Password_0, self.configuration_window.Password_1, self.configuration_window.Password_2,
                        self.configuration_window.Password_3, self.configuration_window.Password_4, self.configuration_window.Password_5,
                        self.configuration_window.Password_6, self.configuration_window.Password_7, self.configuration_window.Password_8]
        for i in range(9):
            # Synchronize the values in all qlineedit
            if passwordList[i] != sender:
                passwordList[i].setText(sender.text())
            # Unify the values of all elements in the object attribute "password"
            self.password[i] = sender.text()

    def changeSSIDinConfig(self):
        # Modify the contents of ssid in the local config.txt file
        lineList = []
        with open(path.join(self.local_path, 'standardConfig.txt'), 'r') as f:
            for each_line, i in zip(f, range(9)):
                start_index = search('SSID:', each_line).end()
                end_index = search('Password:', each_line).start()
                # The content of the ssid to be changed has been stored in the object attribute ssid
                each_line = each_line[:start_index] + self.ssid[i] + '    ' + each_line[end_index:]
                lineList.append(each_line)

        with open(path.join(self.local_path, 'config.txt'), 'w+') as f:
            f.writelines(lineList)

    def changePasswordInConifg(self):
        # Modify the contents of password in the local config.txt file
        lineList = []
        with open(path.join(self.local_path, 'config.txt'), 'r') as f:
            for each_line, i in zip(f, range(9)):
                start_index = search('Password:', each_line).end()
                # The content of the password to be changed has been stored in the object attribute password
                each_line = each_line[:start_index] + self.password[i] + '\n'
                lineList.append(each_line)

        with open(path.join(self.local_path, 'config.txt'), 'w+') as f:
            f.writelines(lineList)

    def slotOfCancel(self):
        # Slot function that will be triggered when the cancel button is pressed

        # Pop-up question box
        reply = QMessageBox.question(self, 'Question',
                                     "Are you sure to configure the network according to the default situation?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # First copy the local standardConfig.txt file into the USB flash drive, then exit the main window and restart the system.

            # Get the sender of the signal, here is the cancel button
            sender = self.sender()
            # Save the local standardConfig.txt file to the USB flash drive.
            self.saveConfig(sender)
            # do configuration and set mark "configured"
            self.configAndMark4masterRPi()
            # Set the flag that ends the child thread that continuously determines whether the USB disk is inserted or unplugged to True
            self.sub_thread.subThread.exitSubThread = True
            # Pop-up message box
            QMessageBox.information(self, 'Message',
                                    'The default configuration file has been successfully saved into the U-Disk, please take out your U-Disk now.\nThe system will restart immediately.')
            QCoreApplication.instance().quit()  # Exit the main window for the network configuration
            system('sudo reboot')  # reboot RPi

    def slotOfOk(self):
        # Slot function that will be triggered when the ok button is pressed

        # Pop-up question box
        reply = QMessageBox.question(self, 'Question',
                                     "Are you sure to configure the network according to the current changes?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # First change the contents of ssid and password in the local config.txt file,
            # then copy the local config.txt file into the USB flash drive,
            # finally exit the main window and restart the system.
            self.changeSSIDinConfig()
            self.changePasswordInConifg()

            sender = self.sender()
            self.saveConfig(sender)
            self.configAndMark4masterRPi()
            self.sub_thread.subThread.exitSubThread = True
            QMessageBox.information(self, 'Message',
                                    'The modified configuration file has been successfully saved into the U-Disk, please take out your U-Disk now.\nThe system will restart immediately.')
            QCoreApplication.instance().quit()
            system('sudo reboot')

    def closeEvent(self, event):
        # the function that is triggered when When the user presses the red cross button, i.e. the close button
        # of the graphical interface for network configuration.

        # Pop-up question box
        reply = QMessageBox.question(self, 'Question',
                                     "Are you sure to quit the network configuration and display the sensor data now?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Set the flag that ends the child thread that continuously determines whether the USB disk is inserted or unplugged to True
            self.sub_thread.subThread.exitSubThread = True
            # Close the graphical interface for the network configuration
            event.accept()

        else:
            # Ignore the request of closing the graphical interface for the network configuration
            event.ignore()

    def usbPulledOut(self):
        # Function that will be triggered when a USB disk is pulled out
        self.msgBox.setText('U-Disk was pulled out, please insert your U-Disk.')
        self.msgBox.setStandardButtons(QMessageBox.Ok)
        self.msgBox.setDefaultButton(QMessageBox.Ok)
        self.msgBox.setIcon(QMessageBox.Warning)
        self.msgBox.setWindowTitle('Warning')
        # Pop up message dialog, return button being pressed. This is a blocking function.
        clicked = self.msgBox.exec_()

        if clicked == QMessageBox.Ok:
            # The message dialog only has the ok button. After being pressed, it is judged whether the USB disk is inserted.
            # If the u disk is not inserted, the message dialog box will pop up.
            if get_U_path() == None:
                self.usbPulledOut()

    def usbInserted(self):
        # Function that will be triggered when a USB disk is inserted

        # QMessageBox.information(self, 'Message', 'U-Disk found and you can save the configuration file to the U-Disk.')

        # if self.msgBox.text() == 'U-Disk not found, please insert your U-Disk or change a readable U-Disk.':
        #     # The U disk is not inserted at the beginning
        #     self.msgBox.setText('U-Disk found and you can save the configuration file to the U-Disk.')
        # elif self.msgBox.text() == 'U-Disk was pulled out, please insert your U-Disk.':
        #     # # U disk was pulled out halfway
        #     self.msgBox.setText('U-Disk found and you can save the configuration file to the U-Disk.')
        # else:
        self.msgBox.setText('U-Disk found and you can save the configuration file to the U-Disk.')
        self.msgBox.setStandardButtons(QMessageBox.Ok)
        self.msgBox.setDefaultButton(QMessageBox.Ok)
        self.msgBox.setIcon(QMessageBox.Information)
        self.msgBox.setWindowTitle('Information')
        self.msgBox.exec_()

    def saveConfig(self, sender):
        # get the path of U-disk. For example: /media/pi/KINSTON
        usbPath = get_U_path()
        # Save the local config.txt file to the U disk
        configFilePath = path.join(usbPath,
                                      'config.txt')  # the path plus filename. For example: /media/pi/KINSTON/config.txt
        assert isinstance(configFilePath, object)
        if sender == self.configuration_window.Ok:
            # The sender of the signal is the ok button, i.e. the ok button is pressed.
            # Copy the local config.txt file into the USB flash drive
            copyfile(path.join(self.local_path, 'config.txt'), configFilePath)
        else:  # sender == self.configuration_window.Cancel
            # The sender of the signal is the cancel button, i.e. the cancel button is pressed.
            # Save the local standardConfig.txt file to the USB flash drive.
            copyfile(path.join(self.local_path, 'standardConfig.txt'), configFilePath)

    def configAndMark4masterRPi(self):
        # firstly do configuration in master_RPi for set access point
        doAPconfig()
        doStaConfig()       # master_RPi connect own hotspot
        # set mark in configuredOfPi.txt in master_RPi and configured.txt in u-disk to know if the raspberry pi is to be configured.
        setMark_inUSB()
        setMark_inMaster()


class SubThread(QThread):

    # Create two signals, which are triggered by the insertion and removal of the USB flash drive
    inserted = pyqtSignal()     # Class attribute
    pulled_out = pyqtSignal()   # Class attribute

    def __init__(self):
        super(SubThread, self).__init__()

    def run(self):
        self.subThread = get_USB_path()
        self.subThread.checkUSBinWhile(self.inserted, self.pulled_out)

from sys import argv, exit
from shutil import copyfile
from threading import Thread
from getUSBpath import get_U_path
from slavemain import slaveMain
from detectdisplay import detectDisplay
from time import sleep, strftime, localtime
from os import path, system, remove, makedirs
from logging import getLogger, basicConfig, INFO
from setmark import isConfigured, setMark_inSlave
from PyQt5.QtWidgets import QMessageBox, QApplication
from configurationsWindow import configurationsWindow
from configuration import doAPconfig, doStaConfig, changeLine

logger = getLogger(__name__)
basicConfig(level=INFO,filename='error.log',format="%(levelname)s:%(asctime)s:%(message)s")

# Importing a class directly performs the initialization of the class property.
# In the masterServer class, the class mainWindow is instantiated to a class attribute of the class masterServer,
# and the mainWindow class is responsible for initializing the graphical interface.
# Before initializing the graphical interface, you must first execute app = QApplication(argv )
app = QApplication(argv)

# The masterServer class is imported. The class mainWindow is instantiated to the class attribute minWin in the class masterServer
from masterserver import masterServerThread, masterServer

def displayMain(app, local_path):
    # Create a new folder to store the data recorded since this boot time, generate a data file every hour,
    # or when the user presses the save button.
    time_boot = strftime("%Y-%m-%d-%H%M%S", localtime())
    path_name = 'Daten/Daten ab Booten um ' + time_boot[:-2]
    if not path.exists(path.join('/home/pi/Desktop/', path_name)):
        makedirs(path.join('/home/pi/Desktop/', path_name))

    # Delete the last data cache file left
    for i in range(1, 9):
        if path.exists(path.join(local_path, str(i) + ".slave_RPi.csv")):
            remove(path.join(local_path, str(i) + ".slave_RPi.csv"))

    masterServer.mainWin.show()  # The main interface initialized in the masterServer appears.
    masterServer.mainWin.showFullScreen()  # Graphical interface is displayed in full screen.
    masterServer_thread = Thread(target=masterServerThread, args=(), daemon=True)
    masterServer_thread.start()  # The child thread that gets the sensor data is started.

    exit(app.exec_())

def recurseDisplayMain(error):
    global logger
    logger.exception(error)
    try:
        app = QApplication(argv)
        from masterserver import masterServerThread, masterServer
        local_path = path.split(path.realpath(__file__))[0]

        displayMain(app, local_path)
    except Exception as error:
        recurseDisplayMain(error)

def recurseSlaveMain(error):
    global logger
    logger.exception(error)
    try:
        slaveMain()
    except Exception as error:
        recurseSlaveMain(error)

def configAndMark4slaveRPi():
    # do configuration in slave_RPi
    doStaConfig()  # Do configuration to connect other Raspberry Pi hotspots
    changeLine()  # Change the information in the configuration file in the U disk
    doAPconfig()  # Do the network configuration used to create your own hotspots
    # set mark in configuredOfPi.txt in master_RPi and configured.txt in u-disk to know if the raspberry pi is to be configured.
    setMark_inSlave()  # In the "configured.txt" file, mark that the Raspberry Pi has been configured.

if __name__ == "__main__":
    # Get the path to the program. for example /home/pi/Luftdrucksensor_RPi
    local_path = path.split(path.realpath(__file__))[0]
    
    # Delete the CSV files that were last cached in the local directory.
    for i in range(1, 9):
        if path.exists(path.join(local_path, str(i) + ".slave_RPi.csv")):
            remove(path.join(local_path, str(i) + ".slave_RPi.csv"))

    # detect display
    if detectDisplay() == 'Display detected': # If the display is connected
        # excute the programm for master RPi
        
        # First the question window is popped up, asking if you want to configure the network.
        msgBox = QMessageBox()
        msgBox.setText('Do you want to do a new configuration of wlan for the RPis?')
        msgBox.addButton(QMessageBox.Yes)
        msgBox.addButton(QMessageBox.No)
        msgBox.setDefaultButton(QMessageBox.No)
        msgBox.setIcon(QMessageBox.Question)
        msgBox.setWindowTitle('Question')
        clicked = msgBox.exec_()  # The choice of yes or no is returned to the clicked variable

        # If the YES button is pressed, the graphical interface for generating the configuration file pops up.
        if clicked == QMessageBox.Yes:
            # The class used to generate the graphical interface for configuring the network is instantiated
            configWindow = configurationsWindow()
            
            if configWindow.do_config:
                configWindow.show()  # Pop-up graphics window

                # After the graphical interface pops up, the graphical interface becomes the main thread through app.exec(),
                # otherwise the graphical interface flashes past.
                app.exec_()
                print (11)
                # The graphical interface for the network configuration is closed, 
                # and the graphical interface that displays the data appears directly.
                # If the graphical interface for the network configuration is not closed,
                # The system will automatically restart after the configuration is completed.
                try:
                    displayMain(app, local_path)
                except Exception as error:
                    recurseDisplayMain(error)
            else:
                # Network configuration was canceled before inserting the USB flash drive
                try:
                    displayMain(app, local_path)
                except Exception as error:
                    recurseDisplayMain(error)
                    
        # If the NO button is pressed, a graphic window pops up showing the pressure sensor and temperature sensor data from slave_RPi.
        else:
            try:
                displayMain(app, local_path)
            except Exception as error:
                recurseDisplayMain(error)

    else:  # detectDisplay() == 'No Display'
        # execute the program for slave RPi
        # check if this slave RPi was already configured.
        # If not, change the internal configuration file to make the slave RPi connect with the access point of the specific RPi
        # and create a access point of itself.
        # !!!important: if man want to do configuration, he must put the U-disk into RPi before he boot the RPi.

        sleep(3)	# wait for mounting the u-disk
        if get_U_path() != None:	# judge if a USB-Stick for network configuration is connected
            print (111)

            # judge if the Raspberry Pi network has been configured
            if isConfigured() == False:		# If the Raspberry Pi network has not been configured yet
                configAndMark4slaveRPi()
                # After the configuration is complete,
                # the system automatically restarts to make the new network configuration take effect.
                system('sudo reboot')
                
        # If no U disk is connected or RPi is already configured,
        # execute the program for getting sensor data from itself and the slave_RPi connected with its access point
        # and sending all collected sensor data to the RPi it connect with.
        try:    # Prevent the Raspberry Pi from causing program errors because the network has never been configured
            with open(path.join(local_path, 'wpa_supplicant-wlan0.conf'), 'r') as f:
                pass
            with open(path.join(local_path, 'wpa_supplicant-wlan1.conf'), 'r') as f:
                pass
            try:
                slaveMain()
            except Exception as error:
                recurseSlaveMain(error)
        except FileNotFoundError:
            pass

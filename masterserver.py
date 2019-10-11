from time import sleep
from pickle import loads
from plot import saveData
from socket import timeout
from os import path, remove
from threading import Thread
from connectinfo import getOwnSSID
from mainwindow import mainWindow
from socketserver import ThreadingTCPServer, BaseRequestHandler

# Marks the network connection of each Raspberry Pi and the connection status of each Raspberry Pi with the corresponding sensor.
# Initially all gray
lcd_backCol = [[],[],[],[],[],[],[],[]]
for i in range(8):
    for j in range(13):
        lcd_backCol[i].append('gray')

class masterServer:
    # mainWin is a class attribute. This line of code is executed when the class masterServer is imported.
    mainWin = mainWindow()

    @classmethod
    def updateLcd_ColVal(cls, data):
        # Class method, change the value of main_window.lcdNumber in the class attribute mainWin, that is,
        # change the display value and background color of lcdNumber in the graphical interface.

        # The first element of the data list is the source of the data.
        dataFrom = data[0]  # for example "1.slave_RPi_2"
        index = int(dataFrom[0])  # for example "1" from string "1.slave_RPi_2"

        global lcd_backCol

        for i in range(1, 14):
            # Dynamically named graphical interface lcdNumber attributes, each slave_RPi corresponds to 13 lcdNumber attributes,
            # a total of 104, greatly optimized code aesthetics through string dynamic naming.
            lcdNumber_name = eval("cls.mainWin.main_window.lcdNumber_" + str(i + 13 * (index - 1)))
            # Starting from data[2] is sensor data
            # The availability of data means that the Raspberry Pi is already in the network connection,
            # as long as it is determined whether the sensor is connected or the data acquisition is normal.
            # That is to judge whether the background color of the original lcdNumber is brown or green.

            # If the obtained data value is -1, it means that The corresponding sensor is disconnected or the value is not acquired properly..
            if data[i+1] == -1:
                # If the background color of the original lcdNumber is not green, It means to reset the corresponding lcdNumber,
                # set the background color to brown, and set the displayed value to 0.
                if lcd_backCol[index-1][i-1] != 'brown':
                    lcdNumber_name.setStyleSheet("background: brown;")  # Change the color of a single lcdNumber to brown.
                    sleep(0.0075)      # Leave time required for operation
                    lcdNumber_name.display(0)   # set the displayed value to 0.
                    sleep(0.0075)
                    lcd_backCol[index - 1][i - 1] = 'brown'
            # If the obtained data value is -1, Then it is necessary to determine whether the original lcdNumber displays a value,
            # that is, whether the original background color is green.
            else:
                # If the original display is not green, you will not only need to update the display value but also update the background color.
                if lcd_backCol[index-1][i-1] != 'green':
                    lcdNumber_name.setStyleSheet("background: green;")  # Change the color of a single lcdNumber to green.
                    sleep(0.0075)
                    lcdNumber_name.display(data[i+1])
                    sleep(0.0075)
                    lcd_backCol[index - 1][i - 1] = 'green'
                else:   # Otherwise just update the value.
                    lcdNumber_name.display(data[i+1])
                    sleep(0.03)

    @classmethod
    def resetLCD_ColVal(cls, slaveNum):
        # Change the background color and displayed value of the lcdNumber corresponding to the Raspberry Pi
        # and all its clients that are suddenly disconnected.

        global lcd_backCol

        for index in range(slaveNum, 9):
            for i in range(1, 14):
                lcdNumber_name = eval("cls.mainWin.main_window.lcdNumber_" + str(i + 13 * (index - 1)))
                if lcd_backCol[index-1][i-1] != 'gray':
                    lcd_backCol[index-1][i-1] = 'gray'
                    lcdNumber_name.setStyleSheet("background: gray;")    # Change the color of a single lcdNumber to gray
                    sleep(0.0075)
                    lcdNumber_name.display(0)       # set the displayed value to 0.
                    sleep(0.0075)

        # Delete legacy data cache files
        # local_path = path.split(path.realpath(__file__))[0]
        # for i in range(slaveNum, 9):
        #     if path.exists(path.join(local_path, str(i) + ".slave_RPi.csv")):
        #         remove(path.join(local_path, str(i) + ".slave_RPi.csv"))

def masterServerThread():
    # Responsible for generating threads that receive data from 1.slave RPi and update the display of data in the main interface
    HOST, PORT = "192.168.1" + ('0' if getOwnSSID()=='m' else getOwnSSID()) + ".1", 9999
    #HOST, PORT = "192.168.137.1", 9999
    # Achieve multiple concurrent response clients to achieve multi-threaded multi-thread operation,
    # because the threads corresponding to "getandsend" and "recandsend" are connected to the server as clients.
    # In addition, the reconnection after disconnection can be realized.
    server = ThreadingTCPServer((HOST, PORT), MyTCPHandler)
    server.serve_forever()  # Start server thread

class MyTCPHandler(BaseRequestHandler):
    def handle(self):
        # This function is the real part of the server thread, is the trigger function after the client connection.

        # Set the timeout to 2s. If 2s does not receive the incoming data from 1.slave_RPi, it is considered disconnected.
        self.request.settimeout(2)
        while True:
            try:
                self.data = self.request.recv(8760)  # a blocking function that receives data from the client
                self.data = loads(self.data)     # Convert binary data back to the original format, i.e. list format.
                # Received information about the disconnection of the Raspberry Pi, a Raspberry Pi after 1.slave_RPi
                if self.data[1] == 'My client is disconnected.':
                    #masterServer.resetLCD_ColVal(int(self.data[0]) + 1)
                    resetLCD_ColVal_thread = Thread(target=masterServer.resetLCD_ColVal, args=(int(self.data[0][0]) + 1,))
                    resetLCD_ColVal_thread.start()
                    if self.data[0][:11] == '2.slave_RPi':
                        resetLCD_ColVal_thread.join()
                        # The Raspberry Pi behind 1.salve_RPi has been disconnected, so you can close the socket connection
                        # between the "recandsend" thread and the master server, because there is no new data to pass,
                        # but 1.slave_RPi will still send a null byte b'' to the master server.
                        break
                # Update the incoming value
                else:
                    # Initialize two threads, one to update the numerical display and background color LcdNumber,
                    # one to store the received data in a temporary csv format cache file.
                    updateLcd_ColVal_thread = Thread(target=masterServer.updateLcd_ColVal, args=(self.data,))
                    saveData_thread = Thread(target=saveData, args=(self.data,))

                    # Start two threads
                    updateLcd_ColVal_thread.start()
                    saveData_thread.start()
            # 1.slave_RPi itself is disconnected. EOFError is triggered by pickle.loads when self.request.recv(1024) = b''.
            except (ConnectionResetError, EOFError, timeout):
                masterServer.resetLCD_ColVal(1)
                break










from os import system
from math import isnan
from pickle import dumps
from socket import socket
from time import time, sleep,localtime,strftime
from logging import getLogger, basicConfig, INFO

logger = getLogger(__name__)
basicConfig(level=INFO,filename='error.log',format="%(levelname)s:%(asctime)s:%(message)s")

from queue import Queue
from threading import Thread
from connectinfo import getOwnSSID, serverInConnect, getOwnName
from getsensordata import getPressure, getTemperature, beschleunigungssensor

class ThreadPoolManger():
    """Thread-Pool-Manager"""
    def __init__(self, thread_num):
        # Parameter initialisieren
        self.work_queue = Queue()
        self.thread_num = thread_num
        self.__init_threading_pool(self.thread_num)

    def __init_threading_pool(self, thread_num):
        # Den Thread-Pool initialisieren und eine bestimmte Anzahl von Thread-Pools erstellen
        for i in range(thread_num):
            thread = ThreadManger(self.work_queue)
            thread.start()

    def add_job(self, func, *args):
        # Die Task in die Warteschlange stellen. Die Parameter sind die Parameter der ausgeführten Funktion und Funktion.
        self.work_queue.put((func, args))

class ThreadManger(Thread):
    """Thread-Manager."""
    def __init__(self, work_queue):
        Thread.__init__(self)
        self.work_queue = work_queue
        self.daemon = True

    def run(self):
        # Thread starten
        try:
            while True:
                # Die platzierte Aufgabe aus der Warteschlange nehmen
                target, args = self.work_queue.get()
                # Die entfernte Aufgabe ausführen
                target(*args)
                # Markiert, dass die Aufgabe ausgeführt wurde.
                self.work_queue.task_done()
        except:
            self.work_queue.task_done()

class getAndSend():
    
    def __init__(self):
        # Initialize a list of sensor data, the first element is the name of the Raspberry Pi as the data source,
        # and the second to sixth elements are the data of the five pressure sensors.
        # The seventh to eleventh store the data of five temperature sensors.
        # The twelfth to the fourteenth are the data of the acceleration sensor. The last one is the moment when the data is sent.
        self.data = [getOwnName(), -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
        # Connect own server
        self.serverADDR = '192.168.1' + str(int(getOwnSSID()) - 1) + '.1'
        #self.serverADDR = '192.168.137.1'
        self.connectServer()
        self.connected = True
        
        # Einen Threadpool mit 4 Threads erstellen
        self.thread_pool = ThreadPoolManger(4)

        self.bs = beschleunigungssensor()
        
    def get_send(self):
        try:
            # get own data and send
            time_1 = time()
            while True:
                if self.connected: 
                    time_2 = time()
                    if time_2 - time_1 >= 0.25:  # Die neuesten Daten alle 0,5 Sekunden abrufen und senden

                        time_1 = time_2
                        self.getOwnData()       # get own data
                        self.thread_pool.add_job(self.sendDataToServer, *())    # send data to own server
  
        except Exception as error:
            from traceback import print_exc
            print_exc()
            global logger
            logger.exception(error)
            self.asClient.close()
            raise error

    def sendDataToServer(self):
        # Send all the data acquired by the sensor to his own server
        msg = dumps(self.data)       # Convert the list object to a bytes format to be sent by the socket
        
        try:
            if serverInConnect():
                self.asClient.send(msg)  # send data from own client to own server
            else:
                system('sudo reboot')
                
        except Exception as error:     # (BrokenPipeError, ConnectionResetError):  # Disconnected from the server
            from traceback import print_exc
            print_exc()
            global logger
            logger.exception(error)
            
            self.connected = False
            self.reconnectServer()
            self.connected = True
            

    def getallDruck(self):
        #all_druck = getAllPressure()
        for drucksensor_num in range(1, 6):
            #self.data[drucksensor_num+1] = all_druck[drucksensor_num-1]
            self.getDruck(drucksensor_num)
            sleep(.001)

    def getallTemp(self):
        for i in range(1,6):
            self.getTemp(i)
            sleep(.001)

    def getOwnData(self):
        #self.thread_pool.add_job(self.getallDruck, *())
        self.thread_pool.add_job(self.getallTemp, *())
        self.thread_pool.add_job(self.getAccel, *())

        time_now = strftime("%Y-%m-%d-%H%M%S", localtime())
        self.data[1] = time_now

        self.getallDruck()

    def getDruck(self, drucksensor_num):
        # 0-25mA entspricht 0-3V or 0-20mA entspricht 0-3.3V
        try:
            # Get data from pressure sensors
            druck = getPressure(drucksensor_num)

            if druck >= 0:
                self.data[drucksensor_num+1] = format(druck, '.2f')
            else:   # Data acquisition is not normal or pressure sensor not connected
                self.data[drucksensor_num+1] = -1

        except:  # Internal circuit failure, ADC failure
            self.data[drucksensor_num+1] = -1

    def getTemp(self, temperatursensor_num):
        try:
            temp = getTemperature(temperatursensor_num)

            # Data acquisition is not normal or temperature sensor is not connected
            if isnan(temp) or temp == 0:
                self.data[6+temperatursensor_num] = -1
            else:
                self.data[6+temperatursensor_num] = int(temp)

        except:   # Internal circuit failure, ADC failure
            self.data[6+temperatursensor_num] = -1

    def getAccel(self):
        try:
            # Get the data of the acceleration sensor
            accel_data = self.bs.getLinearAcc()
            (accel_X, accel_Y, accel_Z) = accel_data - self.bs.static_acc_error
            # accel_X = accel_data[0]
            # accel_Y = accel_data[1]
            # accel_Z = accel_data[2]

            self.data[12] = format(accel_X, '.1f')
            self.data[13] = format(accel_Y, '.1f')
            self.data[14] = format(accel_Z, '.1f')

        except:     # OSError [Errno 121]Remote I/O error. Acceleration sensor is not connected or damaged
            self.data[12] = -1
            self.data[13] = -1
            self.data[14] = -1

    def connectServer(self):
        # connect own server

        self.asClient = socket()

        while True:  # connect the own server
            try:
                self.asClient.connect((self.serverADDR, 9999))
                break
            except:
                sleep(.001)
                continue

    def reconnectServer(self):
        # First close the failed socket connection
        self.asClient.close()
        # Then reconnect own server
        self.asClient = socket()
        while True:
            try:  
                self.asClient.connect((self.serverADDR, 9999))
                break
            except:
                sleep(.001)
                continue



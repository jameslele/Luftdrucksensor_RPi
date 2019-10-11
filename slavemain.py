from threading import Thread
from recandsend import recAndSend
from getandsend import getAndSend

def slaveMain():
	# start the thread for receiving data from client and send to server
	recSend_thread = Thread(target=recAndSend, args=())
	recSend_thread.start()

	# start the thread for getting own data and send to server
	# Bei der Initialisierung wird zunächst die Verbindung zum Server hergestellt
	# und nach erfolgreicher Verbindung wird die folgende Anweisung weiter ausgeführt.
	get_and_send = getAndSend()
	get_and_send.get_send()

if __name__ == "__main__":
    slaveMain()



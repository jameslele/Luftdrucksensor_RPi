from time import sleep
from pickle import dumps
from os import system
from socket import socket, timeout
from connectinfo import getOwnSSID, serverInConnect
from socketserver import BaseRequestHandler, ThreadingTCPServer

class MyTCPHandler(BaseRequestHandler):
    # After receiving the socket connection request from the client and reaching a connection,
    # the content of the automatically opened server-side thread, that is, the message is delivered.
    def handle(self):
        # The next Raspberry Pi is its own client, which automatically triggers the handle function
        # when the client connects to its own open socket. In this trigger function,
        # the Raspberry Pi will connect to the previous Raspberry Pi, its own server,
        # and then receive the message sent from its own client, and then send it to its own server,
        # that is, it plays a a role in delivering messages.

        # Set the timeout for receiving messages to 2s. If 2s does not receive the incoming data
        # from the next Raspberry Pi, it is considered that the client is disconnected from itself.
        self.request.settimeout(2)

        # Connect to own server. connectServer is a blocking function. After connecting to own server,
        # it will continue to execute the code afterwards.
        # Self.sc_connected will be True only if both server and client are connected to itself.
        # In the process of connecting to the server, if the client disconnects from itself, self.sc_connected is set to Fasle.
        self.serverADDR = '192.168.1' + str(int(getOwnSSID()) - 1) + '.1'
        #self.serverADDR = '192.168.137.1'
        self.sc_connected = self.connectServer()

        # Passing data
        while self.sc_connected:
            try:
                # receive data from own client. This is also a blocking function.
                self.data_from_client = self.request.recv(1024)

                # For example, 3.slave_RPi has been disconnected from 2.salve_RPi,
                # 2.slave_RPi will automatically close its socket connection with 1.salve_RPi,(self.asClient.close())
                # but 1.salve_RPi can still receive the null byte b'',
                # which means the server-side thread opened by 1.salve_RPi for 2.slave_RPi is not finished yet,
                # and this is meaningless, so this means that 1.slave_RPi should end the service thread for 2.slave_RPi.
                if self.data_from_client == b'':
                    break

                try:
                    # After judging that your server is still connected to itself,
                    # send a message sent by your client to yourself to your server.
                    # For example, 1.slave_RPi forwards the message sent to it by 2.slave_RPi to master_RPi.
                    if serverInConnect():
                        self.asClient.send(self.data_from_client)
                    else:
                        # Otherwise, it means that your server is likely to have been shut down.
                        # Restarting is more conducive to reconnecting the previous Raspberry Pi that was restarted again.
                        system('sudo reboot')
                # If only the server side program is abnormal or exits, and the network connection with the server still exists,
                # an error BrokenPipeError or error ConnectionResetError will be generated.
                except (BrokenPipeError, ConnectionResetError):
                    # Resend the socket connection request to the server
                    self.sc_connected = self.reconnectServer()

            # If the client disconnects from itself or his program is abnormal,
            # the error ConnectionResetError is triggered at the previous code "self.data_from_client = self.request.recv(1024)",
            # or the message is not received in two seconds, the error socket.timeout is triggered.
            except (ConnectionResetError, timeout):
                try:
                    # Send a message to the previous Raspberry Pi to let master_RPi know that
                    # a Raspberry Pi is disconnected from the network.
                    info = [getOwnSSID(), 'My client is disconnected.']
                    if serverInConnect():
                        self.asClient.send(dumps(info))
                        self.asClient.close()  # End the socket connection to own server
                        # The client has been disconnected. End the server thread opened for the client
                        self.sc_connected = False
                    else:
                        system('sudo reboot')
                except (BrokenPipeError, ConnectionResetError):
                    self.asClient.close()
                    self.sc_connected = False

    def connectServer(self):
        # Connect own server
        self.asClient = socket()

        while True:
            try:
                self.asClient.connect((self.serverADDR, 9999))
                return True

            except:
                # Before reaching the connection with the server, keep receiving the data of the client Raspberry Pi,
                # avoiding the data accumulated together being sent to the server when the connection with the server is successful.
                sleep(.1)
                try:
                    self.request.recv(1024)
                # Before the connection with the server is successful, the connection with the client has been disconnected,
                # then the thread that passes the data is directly ended.
                except (ConnectionResetError, timeout):
                    return False

    def reconnectServer(self):
        # Apply for a socket connection again
        self.asClient.close()
        self.asClient = socket()
        while True:
            try:
                self.asClient.connect((self.serverADDR, 9999))
                return True

            except:
                sleep(.1)
                try:
                    self.request.recv(1024)
                except (ConnectionResetError, timeout):
                    return False

def recAndSend():
    # recieve data from own client and send the data to own server
    HOST, PORT = "192.168.1" + getOwnSSID() + ".1", 9999      # for example '192.168.11.1'
    # Generate a server-side thread queue that will automatically start a thread to join the queue
    # whenever it receives a socket connection request from the client and a connection is reached.

    # Set the ip and port number, and fill in the custom class, the class inherits the parent class "socketserver.BaseRequestHandler",
    # the rewritten "handle" function is the trigger function after the client connects with itself.
    server = ThreadingTCPServer((HOST, PORT), MyTCPHandler)
    # This is a blocking function that always waits for a new connection request and then opens a new server-side thread to join the thread queue.
    server.serve_forever()


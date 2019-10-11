from re import search
from os import popen, path

def serverInConnect():
    # Determine if the network connection is disconnected from the previous Raspberry Pi,
    # that is, whether it is connected to the hotspot opened by the previous Raspberry Pi.
    with popen('ifconfig') as f:
        lines = f.readlines()
        next_line = False
        for line in lines:
            if next_line:
                break
            if line[:5] == 'wlan0':
                next_line = True

        return line.split()[1][:8] == '192.168.'

def getOwnSSID():
    # get own ssid
    local_path = path.split(path.realpath(__file__))[0]  # /home/pi/Luftdrucksensor_RPi
    with open(path.join(local_path, 'wpa_supplicant-wlan1.conf'), 'r') as f:
        text = f.read()

        startIndex = search('ssid="', text).end()
        endIndex = search('mode=', text).start()
        ssid = text[startIndex:endIndex].rstrip()  # for example "1.slave_RPi_1"" "master_RPi_1"
        ssid = ssid[0]  # for example "1" "m"
        return ssid

def getOwnName():
    # Get the name of the Raspberry Pi that sent the data
    local_path = path.split(path.realpath(__file__))[0]  # /home/pi/Luftdrucksensor_RPi
    with open(path.join(local_path, 'wpa_supplicant-wlan1.conf'), 'r') as f:
        text = f.read()
        startIndex = search('ssid="', text).end()
        endIndex = search('mode=', text).start()
        name = text[startIndex:endIndex].rstrip()  # for example "1.slave_RPi_1""
        name = name[:-1]  # for example "1.slave_RPi_1"
        return name

if __name__ == "__main__":
    print ("ok")


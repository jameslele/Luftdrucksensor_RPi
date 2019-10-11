from re import search
from os import path, system
from getUSBpath import get_U_path

# Waln0 is used to do sta, wlan1 is used to do ap, sta connects other hotspots of Raspberry Pi,
# and ap opens its own hotspot for other Raspberry Pi to connect.

def getSSIDandPASS():
    # patch infos from the first line of config.txt in u-disk
    with open(path.join(get_U_path(),'config.txt')) as f:
        for each_line in f:
            firstLine = each_line
            break
        
    endIndex = search(':', firstLine).start()
    RPi = firstLine[:endIndex]
    
    startIndex = search('SSID:', firstLine).end()
    endIndex = search('Password', firstLine).start()
    SSID = firstLine[startIndex:endIndex].rstrip()

    startIndex = search('Password:', firstLine).end()
    Password = firstLine[startIndex:].rstrip()
    
    return [RPi, SSID, Password]
        
def doStaConfig():
    # do configuration for connecting with specific wifi
    # create a "wpa_supplicant-wlan0.conf" file in local directionary
    # and copy it to override the same named file in path "/etc/wpa_supplicant/"
    local_path = path.split(path.realpath(__file__))[0] # /home/pi/Luftdrucksensor_RPi
    with open(path.join(local_path,'wpa_supplicant-wlan0.conf'), 'w+') as f:
        text = 'country=GB\n\
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n\
update_config=1\n\
network={\n\
    ssid=""\n\
    psk=""\n\
    priority=100\n\
}'
        # Obtain the relevant network configuration information from the config.txt file of the USB flash drive.
        [RPi, SSID, Password] = getSSIDandPASS()
        bridgeIndex = search('ssid="', text).end()
        text = text[:bridgeIndex] + RPi+'_'+SSID + text[bridgeIndex:]
        bridgeIndex = search('psk="', text).end()
        text = text[:bridgeIndex] + Password + text[bridgeIndex:]
        f.writelines(text)

    # copy and override the created file to "/etc/wpa_supplicant/wpa_supplicant-wlan0.conf"
    command = 'sudo cp ' + local_path + '/wpa_supplicant-wlan0.conf /etc/wpa_supplicant/wpa_supplicant-wlan0.conf'
    system(command)

def changeLine():
    # place the first line to the last line in config.txt in u-disk
    # Call this method after calling method doStaConfig and before calling method doApConfig
    text = []
    with open(path.join(get_U_path(), 'config.txt')) as f:
        for i, each_line in zip(range(9), f):
            if i == 0:
                first_line = each_line
            else:
                text.append(each_line)
        text.append(first_line)

    with open(path.join(get_U_path(), 'config.txt'), 'w') as f:
        f.writelines(text)

def doAPconfig():
    # do configuration for opening specific access point(AP)
    local_path = path.split(path.realpath(__file__))[0] # /home/pi/Luftdrucksensor_RPi
    with open(path.join(local_path,'wpa_supplicant-wlan1.conf'), 'w+') as f:
        text = 'country=GB\n\
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n\
update_config=1\n\
ap_scan=2\n\
network={\n\
    ssid=""\n\
    mode=2\n\
    key_mgmt=WPA-PSK\n\
    psk=""\n\
    frequency=2412\n\
}'
        
        [RPi, SSID, Password] = getSSIDandPASS()
        bridgeIndex = search('ssid="', text).end()
        text = text[:bridgeIndex] + RPi+'_'+SSID + text[bridgeIndex:]
        bridgeIndex = search('psk="', text).end()
        text = text[:bridgeIndex] + Password + text[bridgeIndex:]
        f.writelines(text)

    # copy and override the created file to "/etc/wpa_supplicant/wpa_supplicant-wlan1.conf"
    command = 'sudo cp ' + local_path + '/wpa_supplicant-wlan1.conf /etc/wpa_supplicant/wpa_supplicant-wlan1.conf'
    system(command)

    # change address of AP in /etc/systemd/network/12-wlan1.network
    with open('/etc/systemd/network/12-wlan1.network', 'r') as f:
        text = f.read()
        startIndex = search('Address=', text).end()
        endIndex = search('/24', text).start()

        # set address
        ssid = getOwnSSID()
        if ssid == 'm':     # is master_RPi
            address = '192.168.10.1'
        else:               # is slave_RPi. The range is '1' - '8'
            address = '192.168.1' + ssid + '.1'
        text = text[:startIndex] + address + text[endIndex:]

    with open(path.join(local_path,'12-wlan1.network'), 'w+') as f:
        f.write(text)

    # copy and override the created file to "/etc/systemd/network/12-wlan1.network"
    command = 'sudo cp ' + local_path + '/12-wlan1.network /etc/systemd/network/12-wlan1.network'
    system(command)


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



from re import search
from os import path, system
from getUSBpath import get_U_path


def isConfigured():
    # Used to determine if the network of slave_RPi has been configured.
    # The configuredOfPi.txt file in the local path stores how many times the Raspberry Pi has been configured,
    # and the configured.txt file in the U disk stores the information about which round Raspberry Pi needs to be configured.
    # The difference between the two information will trigger the new network configuration of slave_RPi,
    # and after being configured, the configuration information in the configuredOfPi.txt file of the Raspberry Pi
    # will be synchronized with the configuration information in the configured.txt file of the U disk.

    local_path = path.split(path.realpath(__file__))[0]
    try:
        with open(path.join(local_path, 'configuredOfPi.txt'), 'r') as f:
            # get text of configuredOfPi.txt in Pi and get number of round
            firstLine = f.readline()  # type: str
            startIndex = search('At ', firstLine).end()
            endIndex = firstLine.index('.')
            roundOfPi = int(firstLine[startIndex:endIndex])
    except FileNotFoundError:
        # Raspberry Pi has not been configured yet.
        with open(path.join(local_path, 'configuredOfPi.txt'), 'w+') as s:
            s.write('At 0.round configured')
            roundOfPi = 0

    try:
        with open(path.join(get_U_path(), 'configured.txt'), 'r') as s:
            # get text of configured.txt in  U-disk and get number of round
            firstLine = s.readline()  # type: str
            endIndex = firstLine.index('.')
            roundOfUSB = int(firstLine[:endIndex])
    except FileNotFoundError:  # new U-disk without any configuration-file
        return True  # nothing happen and run main program of slave
    except PermissionError:
        system('sudo rmdir ' + get_U_path())
        system('sudo reboot')

    # Determine whether the configuration information of the Raspberry Pi is synchronized with the configuration information in the u disk.
    if roundOfPi == roundOfUSB:
        return True
    else:
        return False

def setMark_inUSB():
    # get text of configured.txt in U-disk and get number of round
    try:    # judge if the file "configured.txt" already exists in U-disk
        with open(path.join(get_U_path(), 'configured.txt'), 'r') as f:
            # file exist
            firstLine = f.readline()  # type: str
            endIndex = firstLine.index('.')
            roundOfUSB = int(firstLine[:endIndex])
    except FileNotFoundError:
        # File is not found.
        with open(path.join(get_U_path(), 'configured.txt'), 'w+') as s:
            s.write('0.round configuration')
            roundOfUSB = 0

    # increase the number of round
    with open(path.join(get_U_path(), 'configured.txt'), 'w+') as f:
        firstLine = str(roundOfUSB+1) + '.round configuration'
        f.write(firstLine)

def setMark_inMaster():     # is same with setMark_inSlave()
    # change the first line "At x.round configured" to "At x+1.round configured" in configuredOfPi.txt in master_RPi
    with open(path.join(get_U_path(), 'configured.txt'), 'r') as s:
        # get text of configured.txt in  U-disk and get number of round
        firstLine = s.readline()  # type: str
        endIndex = firstLine.index('.')
        roundOfUSB = firstLine[:endIndex]

    local_path = path.split(path.realpath(__file__))[0]     # Get the local path where the program is located
    with open(path.join(local_path, 'configuredOfPi.txt'), 'w+') as f:
        # change the first line "At x.round configured" to "At x+1.round configured" in configuredOfPi.txt
        firstLine = 'At ' + roundOfUSB + '.round configured'
        f.write(firstLine)

def setMark_inSlave():
    # change the first line "At x.round configured" to "At x+1.round configured" in configuredOfPi.txt in slave_RPi
    with open(path.join(get_U_path(), 'configured.txt'), 'r') as s:
        # get text of configured.txt in  U-disk and get number of round
        firstLine = s.readline()    # type: str
        endIndex = firstLine.index('.')
        roundOfUSB = firstLine[:endIndex]

    local_path = path.split(path.realpath(__file__))[0]
    with open(path.join(local_path, 'configuredOfPi.txt'), 'w+') as f:
        # change the first line "At x.round configured" to "At x+1.round configured" in configuredOfPi.txt
        firstLine = 'At ' + roundOfUSB + '.round configured'
        f.write(firstLine)

if __name__ == "__main__":
    # setMark_inUSB()
    # setMark_inMaster()
    #
    # if isConfigured() == False:
    #     setMark_inSlave()
    # else:
    #     print('configured')
    print (isConfigured())



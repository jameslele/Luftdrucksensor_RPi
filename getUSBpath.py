from time import sleep
from os import popen, path, system, listdir


def get_U_path():
    # Returns None when no USB flash drive is connected, and returns the full path of the USB flash drive when connected
    # Can be executed once to get the path of U-Disk. Used "os.popen".
    u_path = None
    with popen('cd /media ; ls') as s:
        # first time to boot after install system, there are no folder "pi" in "media".
        # After the u-disk is mounted at least one time, there are a folder "pi".
        # So when there is no folder called "pi", it means that there is never a U disk connected.
        if s.readline().rstrip() != 'pi':
            return None
    with popen('cd /media/pi ; ls') as f:
        # When no U disk is inserted, f is empty, the program will not enter the for loop, and the path is also None.
        # the first directionary in path "/media/pi/" is the path of U-Disk.
        for each_line in f:
            # Get the full path of the u disk
            u_path = path.join('/media/pi/', each_line.rstrip())
            # rstrip() can delete all space(' ') at the end of the string, including line break('\n'), tabs('\t'), etc.
            # Prevent the previous file directory from not successfully ending the mount
            if system('cd ' + u_path) != 0:
                system('sudo rmdir ' + u_path)
                return None
    return u_path

class get_USB_path():
    # A method of identifying whether a U disk is inserted or removed in a loop is provided.

    def __init__(self):
        # This is a flag used to determine whether to end the thread that recognizes whether the U disk is inserted or unplugged in the loop.
        self.exitSubThread = False

    def checkUSBinWhile(self, inserted, pulled_out):
        # When the user detects the pullout or insertion of the USB flash drive during the process of modifying the configuration file in the user interface,
        # a message dialog box pops up to make a reminder. This function will run in a child thread because of the loop.
        # In the loop, iteratively traverses whether there is a new folder under the "/media/pi" path. If a new folder appears,
        # it means that there is a USB disk inserted, otherwise it means there is no USB disk inserted, the newly added folder is the inserted USB flash drive.
        # In a branch thread (see configurationwindows.py file), this function will be executed. The thread first identifies whether there is a U disk path.
        # If it is recognized, a message dialog box pops up to remind the user, "The U disk is inserted and the configuration file will be saved into the U disk",
        # if the U disk path is not recognized, the user is prompted, "U disk is not found, please insert the U disk".

        # Obtain the path that the u disk will load, as the initial state, used to determine
        # whether there is more folder name added after the U disk is loaded in the path.
        with popen('cd /media ; ls') as s:
            if s.readline().rstrip() != 'pi':
                # first time to boot, there are no folder "pi" in "media".
                # After the u-disk is mounted at least one time, there are a folder "pi".
                # In this case, create a folder called pi directly
                system('sudo mkdir /media/pi')
        usb_path = "/media/pi/"  # "/media/pi/" is the path where the USB flash drive is mounted.
        content = listdir(usb_path)  # Get all folder names under the "/media/pi/" path

        # After entering the function loop, identify the disappearance and appearance of the U disk path.
        # If it disappears or appears, there will be a corresponding message dialog box to prompt.
        while True:
            if self.exitSubThread == True:
                break
            # Get all folders names under the "/media/pi/" path again
            new_content = listdir(usb_path)
            # If the folder name under the "/media/pi/" path changes, it means U disk is pulled out or inserted.
            if new_content != content:
                # After the U disk is inserted or unplugged, the folder name corresponding to the U disk is added or decreased in the "/media/pi/" path.
                # When the file is inserted, the folder name is stored in the item list. When it is pulled out, the item becomes An empty list
                item = [item for item in new_content if item not in content]

                # U disk is pulled out
                if len(item) == 0:
                    # The pyqt signal "pulsed_out" passed to the function "checkUSBinWhile" is emitted
                    pulled_out.emit()
                # U disk is inserted
                else:
                    # The pyqt signal "inserted" passed to the function "checkUSBinWhile" is emitted
                    inserted.emit()

                # Update the old folder name stored in the variable "content"
                content = new_content
            sleep(.1)


if __name__ == "__main__":
    print(get_U_path())


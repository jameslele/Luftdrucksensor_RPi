import os


def detectDisplay():
    # Implement command line operations in code form
    command = 'tvservice -s'  # The command to be executed on the command line
    r = os.popen(command)  # Execute the command
    info = r.readline()  # Read the output of the command line into a string
    # When the first 14 characters of the command line output are 'state 0x120006', it means a small display is connected.
    if info[:14] == 'state 0x120006':
        return 'Display detected'
    # Otherwise, when you continue to execute 'tvservice -n' and have output, it means a big monitor is connected.
    else:
        command = 'tvservice -n'  # The command to be executed on the command line
        r = os.popen(command)
        info = r.readline()
        # In this case, it means that there is no display connection.
        if info == '':
            return 'No display'
        # In this case, it means that a big display is connected.
        else:
            return 'Display detected'


if __name__ == "__main__":
    print(detectDisplay())

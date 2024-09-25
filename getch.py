
import msvcrt, time

def getch_or_timeout(timeout):
    '''
    Waits for `timeout` seconds to check for a user input
    '''
    time.sleep(timeout)

    if msvcrt.kbhit():
        return msvcrt.getch()

    return

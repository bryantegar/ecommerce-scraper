import signal
import time

from libs.logger import printinfo


class GracefulKiller:
    kill_now = False
    _signal = 0

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        printinfo(f"Received signal {signum}, stopping process...")
        self.kill_now = True
        if signum == 2:
            self._signal = 'INTERRUPTED'
        elif signum == 15:
            self._signal = 'TERMINATED'
        else:
            self._signal = 'STOPPED'

# if __name__ == '__main__':
#   killer = GracefulKiller()
#   while not killer.kill_now:
#     time.sleep(1)
#     print("doing something in a loop ...")

#   print("End of the program. I was killed gracefully :)")

import msvcrt
import time
import threading


class A(object):
    def __init__(self):
        self.c = ""

    def work(self):
        while self.c != "q":
            print("... waiting for user input, press 'q' to quit")
            time.sleep(1)

    def get_user(self):
        while True:
            if msvcrt.kbhit() and ord(msvcrt.getch()) == ord('q'):
                self.c = "q"
                break

    def main(self):
        t0 = threading.Thread(target=self.work)
        t0.start()
        t1 = threading.Thread(target=self.get_user)
        t1.start()
        t0.join()
        t1.join()
        return 0


if __name__ == "__main__":
    a = A()
    a.main()

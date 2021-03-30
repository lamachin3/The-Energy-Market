from multiprocessing import Value
import sysv_ipc, threading, time, random
 

class Weather:

    temperature = Value('i', 0)
    barrier = None
    stop = None

    def __init__(self, barrier, stop):
        self.temperature.value = 20
        self.barrier = barrier
        self.stop = stop

    def getSharedMem(self):
        return self.temperature

    def genTemperature(self):
        self.barrier.wait()
        while not self.stop.value:
            self.temperature.value = int(random.gauss(self.temperature.value, 7))
            print("Generated temperature : {}".format(self.temperature.value))
            self.barrier.wait()

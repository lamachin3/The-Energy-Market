from multiprocessing import Value
import sysv_ipc, threading, time, random
 

class Weather:

    temperature = Value('i', 0)

    def getSharedMem(self):
        return self.temperature

    def genTemperature(self):
        t0 = time.time() 
        while True:
            t1 = time.time()
            if t1-t0 > 10:
                self.temperature.value = random.randint(-20, 40)
                print("Generated temperature : {}".format(self.temperature.value))
                t0 = t1

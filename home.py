from multiprocessing import Process
import random
import math
import sysv_ipc
import time, os
 

class Home(Process):

    cons, prod, policy, temperature = int, int, int, None

    def __init__(self, policy, shrdMem):
        super().__init__()
        self.policy = policy
        self.temperature = shrdMem

    def run(self):
        t0 = time.time() 
        while True:
            t1 = time.time()
            if t1-t0 > 10:
                self.getCons()
                self.getProd()
                t0 = t1

    def getCons(self): 
        self.cons = round(100 + ((self.temperature.value - 20)/2)**2 + random.randint(-20, 20))

    def getProd(self):
        self.prod = round(8*self.temperature.value + random.randint(-20, 20))
        if self.prod < 0:
            self.prod = 0

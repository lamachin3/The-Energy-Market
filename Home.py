from multiprocessing import Process
import random
import math

class Home(Process):

    cons, prod, policy, temperature = int, int, int, 40

    def __init__(self, policy):
        super().__init__()
        self.policy = policy

    def run(self):
        #print("Conso", self.getCons())
        #print("Prod", self.getProd())
        print("Ecart", self.getProd()-self.getCons())

    def getCons(self): 
        self.cons = round(100 + ((self.temperature - 20)/2)**2 + random.randint(-20, 20))
        return self.cons

    def getProd(self):
        self.prod = round(8*self.temperature + random.randint(-20, 20))
        if self.prod < 0:
            self.prod = 0
        return self.prod

if __name__ == "__main__":
    for i in range(10):
        p = Home(i)
        p.start()
    for i in range(10):
        p.join()
from multiprocessing import Process
import random
import math
import sysv_ipc
import time, os
 
key_market = 123
key_share = 321

class Home(Process):

    cons, prod, policy, temperature = int, int, int, None
    #accounting = {"sold": [], "bought": []}

    def __init__(self, policy, shrdMem):
        super().__init__()
        self.policy = policy
        self.temperature = shrdMem

    def run(self):
        try:
            mq_market = sysv_ipc.MessageQueue(key_market)
        except:
            print("Cannot connect to message queue", key_market, ", terminating.")
            exit(1)
        
        mq_share = sysv_ipc.MessageQueue(key_share)  

        t0 = time.time()
        while True:
            t1 = time.time()
            if t1-t0 > 10:
                self.getCons()
                self.getProd()
                self.buy_or_sell(mq_market, self.share(mq_share))
                t0 = t1       

    def getCons(self): 
        #self.cons = round(100 + ((self.temperature.value - 20)/2)**2 + random.randint(-20, 20))
        self.cons = random.randint(0, 200)
        #print("Conso : {} - {}".format(self.cons, os.getpid()))

    def getProd(self):
        #self.prod = round(8*self.temperature.value + random.randint(-50, 50))
        self.prod = random.randint(0, 100)
        if self.prod < 0:
            self.prod = 0
        #print("Prod : {} - {}".format(self.prod, os.getpid()))

    def buy_or_sell(self, mq_market, gap):
        encd_gap = str(abs(gap)).encode()
        if gap > 0:
            mq_market.send(encd_gap, type = 1)    
        elif gap < 0:
            mq_market.send(encd_gap, type=2)

    def share(self, mq_share):
        gap = self.prod - self.cons
        print("gap", gap, "\tpid", os.getpid())
        if self.policy == 2 and gap > 0:
            msg = "0_" + str(os.getpid())
        else:
            msg = str(gap) + "_" + str(os.getpid())
        msg = msg.encode()
        
        mq_share.send(msg, type=self.policy)   
        msg_rcvd = mq_share.receive(type=os.getpid())[0].decode()
        if self.policy == 2 and gap > 0:
            msg_rcvd = gap
        return int(msg_rcvd)

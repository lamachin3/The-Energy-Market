from multiprocessing import Process
from external import External
import concurrent.futures
import sysv_ipc
import sys

key = 123

class Market(Process):
    temperature = None
    external = External()
    accounting = float
    internal_factors = {"energy_balance": 0, "temperature": 0}
    external_factors = {"tension": 0, "fuel_shortage": 0}
    price = int
    mq = None

    def __init__(self, shrdMem):
        super().__init__()
        self.temperature = shrdMem
        self.price = 0.145
        self.accounting = 0

    def run(self):
        try:
            self.mq = sysv_ipc.MessageQueue(key, sysv_ipc.IPC_CREX)
        except:
            print("Message queue", key, "already exsits, terminating.")
            sys.exit(1)

        with concurrent.futures.ThreadPoolExecutor(max_workers = 4) as executor:
            while True:
                msg, t = self.mq.receive()
                self.set_price()
                if t == 1:
                    executor.submit(self.sell_energy, int(msg.decode()))
                elif t == 2:
                    executor.submit(self.buy_energy, int(msg.decode()))
    
    def buy_energy(self, qty):
        self.internal_factors["energy_balance"] -= qty
        self.accounting -= self.price * qty
        print("buying {} from house".format(qty))

    def sell_energy(self, qty):
        self.internal_factors["energy_balance"] += qty
        self.accounting += self.price * qty
        print("selling {} to house".format(qty))

    def set_price(self):
        self.internal_factors["temperature"]  = self.temperature.value
        gamma = 0.99
        alpha = [0.001, 0.002]
        beta = [0.02, 0.01]
        self.price = self.price * gamma

        for key in self.internal_factors:
            index = list(self.internal_factors).index(key)
            self.price += alpha[index] * self.internal_factors[key]

        for key in self.external_factors:
            index = list(self.external_factors).index(key)
            self.price += beta[index] * self.external_factors[key]
        

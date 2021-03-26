from multiprocessing import Process
import concurrent.futures
import sysv_ipc, signal
import sys, os, time

key = 123

class Market(Process):
    temperature = None
    external_proc = None
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
        signal.signal(signal.SIGUSR1, self.handler)
        self.external_proc = Process(target=self.external_worker, args=())
        self.external_proc.start()
    
    def handler(self, sig, frame):
        if sig == signal.SIGUSR1:
            self.external_factors["tension"] = 1
        elif sig == signal.SIGUSR2:
            self.external_factors["fuel_shortage"] = 1

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
                    executor.submit(self.buy_energy, int(msg.decode()))
                elif t == 2:
                    executor.submit(self.sell_energy, int(msg.decode()))
                for i in self.external_factors:
                    self.external_factors[i] = 0
        self.external_proc.join()
    
    def sell_energy(self, qty):
        self.internal_factors["energy_balance"] -= qty
        self.accounting -= self.price * qty
        #print("selling {} to house".format(qty))

    def buy_energy(self, qty):
        self.internal_factors["energy_balance"] += qty
        self.accounting += self.price * qty
        #print("buying {} from house".format(qty))

    def set_price(self):
        self.internal_factors["temperature"]  = self.temperature.value
        gamma = 0.99
        alpha = [-0.001, 0.002]
        beta = [0.02, 0.01]
        self.price = self.price * gamma

        for key in self.internal_factors:
            index = list(self.internal_factors).index(key)
            self.price += alpha[index] * self.internal_factors[key]

        for key in self.external_factors:
            index = list(self.external_factors).index(key)
            self.price += beta[index] * self.external_factors[key]
        
    def external_worker(self):  # A FINIR
        t0 = time.time()
        while True:
            t1 = time.time()
            if t1-t0 > 10:
                os.kill(os.getppid(), signal.SIGUSR1)
                t0 = t1
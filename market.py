from multiprocessing import Process
import concurrent.futures
import sysv_ipc, signal
import sys, os, time, random

key = 123

class Market(Process):
    temperature = None
    external_proc = None
    barrier = None
    stop = None
    accounting = float
    internal_factors = {"energy_balance": 0, "temperature": 0}
    external_factors = {"storm": 0, "fuel_shortage": 0}
    price = int
    mq = None

    def __init__(self, shrdMem, barrier, stop):
        super().__init__()
        self.temperature = shrdMem
        self.barrier = barrier
        self.stop = stop
        self.price = 0.145
        self.accounting = 0
        signal.signal(signal.SIGUSR1, self.handler)
        signal.signal(signal.SIGUSR2, self.handler)
        self.external_proc = Process(target=self.external_worker, args=())
        self.external_proc.start()

        try:
            self.mq = sysv_ipc.MessageQueue(key, sysv_ipc.IPC_CREX)
        except:
            print("Message queue", key, "already exsits, terminating.")
            sys.exit(1)
    
    def handler(self, sig, frame):
        if sig == signal.SIGUSR1:
            self.external_factors["storm"] = 1
            with open('storm.txt','r') as f:
                print(f.read())
        
        if sig == signal.SIGUSR2:
            self.external_factors["fuel_shortage"] = 1
            with open('fuel.txt','r') as f:
                print(f.read())

    def run(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers = 4) as executor:
            while not self.stop.value:
                msg, t = None, None
                while msg == None and not self.stop.value:
                    try:
                        msg, t = self.mq.receive(block=False)
                    except:
                        msg = None
                if self.stop.value:
                    break

                self.set_price()
                if t == 1:
                    executor.submit(self.buy_energy, int(msg.decode()))
                elif t == 2:
                    executor.submit(self.sell_energy, int(msg.decode()))
                
        self.mq.remove()
    
    def sell_energy(self, qty):
        self.internal_factors["energy_balance"] -= qty
        self.accounting -= self.price * qty
        print("selling {} to house".format(qty))

    def buy_energy(self, qty):
        self.internal_factors["energy_balance"] += qty
        self.accounting += self.price * qty
        print("buying {} from house".format(qty))

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
            
        
    def external_worker(self):
        self.barrier.wait()
        p1, p2 =  0.9, 0.95
        while not self.stop.value:
            for i in self.external_factors:
                self.external_factors[i] = 0

            if random.random() > p1:
                os.kill(os.getppid(), signal.SIGUSR1)
                p1 = 0.9
            else:
                p1 = p1**2

            if random.random() > p2:
                os.kill(os.getppid(), signal.SIGUSR2)
                p2 = 0.95
            else:
                p2 = p2**2
            self.barrier.wait()

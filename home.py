from multiprocessing import Process
import random
import math
import sysv_ipc
import time, os
 
key_market = 123 #clé de la message queue du market
key_share = 321 #clé de la messager queue du partage

class Home(Process):

    cons, prod, policy = int, int, int
    stop = None
    temperature = None
    barrier = None
    mq_market, mq_share = None, None
    recap = dict() #"day_n : [gap_debut, gap_share]" 

    def __init__(self, policy, shrdMem, barrier, stop):
        super().__init__()
        self.policy = policy
        self.temperature = shrdMem
        self.barrier = barrier
        self.stop = stop
        try:
            self.mq_market = sysv_ipc.MessageQueue(key_market) #Connexion à une message queue pour communiquer avec le market
            self.mq_share = sysv_ipc.MessageQueue(key_share) #Connexio à une message queue pour communiquer avec les autres maisons
        except:
            print("Cannot connect to message queue, terminating.")
            exit(1)
        

    def run(self):
        self.barrier.wait()
        while not self.stop.value:
            self.getCons()
            self.getProd()
            self.buy_or_sell(self.mq_market, self.share(self.mq_share))
            self.barrier.wait()
        for i in self.recap:
            print("Day_" + str(repr(i)), repr(self.recap[i][0]).rjust(4), repr(self.recap[i][1]).rjust(4), end='\t\t')
        print("\n")

    #calcul de la consommation de la maison
    def getCons(self): 
        #self.cons = round(100 + ((self.temperature.value - 20)/2)**2 + random.randint(-20, 20))
        self.cons = random.randint(0, 200) 
        #print("Conso : {} - {}".format(self.cons, os.getpid()))

    #calcul de la production de la maison 
    def getProd(self):
        #self.prod = round(8*self.temperature.value + random.randint(-50, 50))
        self.prod = random.randint(0, 100)
        if self.prod < 0:
            self.prod = 0
        #print("Prod : {} - {}".format(self.prod, os.getpid()))

    #achat et vente sur le marché
    def buy_or_sell(self, mq_market, gap):
        encd_gap = str(abs(gap)).encode()
        if gap > 0:
            mq_market.send(encd_gap, type = 1) #demande de vente d'energie sur le marché
        elif gap < 0:
            mq_market.send(encd_gap, type=2) #demande d'achat d'energie sur le marché

    #partage des ressources avec les autres maisons
    def share(self, mq_share):
        gap = self.prod - self.cons #calcul du reste de l'energie après consommation
        if self.policy == 2 and gap > 0:
            msg = "0_" + str(os.getpid()) # pas de partage
        else:
            msg = str(gap) + "_" + str(os.getpid()) #création du message pour la message queue avec l'écart et le PID sous la forme (GAP_PID)
        msg = msg.encode()
        
        mq_share.send(msg, type=self.policy) #envoi du message de type = policy
        msg_rcvd = mq_share.receive(type=os.getpid())[0].decode() #réception du message de type = PID
        if self.policy == 2 and gap > 0:
            msg_rcvd = gap #réatribution de l'écart non mis sur le partage
        self.recap[len(self.recap) + 1]=(gap, int(msg_rcvd))
        return int(msg_rcvd)

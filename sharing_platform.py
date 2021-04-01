from multiprocessing import Process
import sysv_ipc, sys

key = 321

class SharingPlatform(Process):
    mq = None
    barrier = None
    nb_houses = int
    stop = None

    def __init__(self, nb_houses, barrier, stop):
        super().__init__()
        self.nb_houses = nb_houses
        self.barrier = barrier
        self.stop = stop
        try:
            self.mq = sysv_ipc.MessageQueue(key, sysv_ipc.IPC_CREX) #crée une message queue 
        except:
            print("Message queue", key, "already exists, terminating.")
            sys.exit(1)

    def run(self):
        self.barrier.wait()
        while not self.stop.value:
            if self.mq.current_messages == self.nb_houses: #attend que toutes les maisons aient envoyé un message
                data_rcvd = dict()
                while self.mq.current_messages != 0:
                    msg = self.mq.receive(type=-3)[0].decode() #traite tous les messages de type <= 3 en commençant par le type le plus petit (priorisation des échanges pour les policy 1 (energie perdu sinon))
                    msg_split = msg.split("_")  
                    data_rcvd[msg_split[1]] = int(msg_split[0]) #"PID_GAP"

                data_send = self.processing(data_rcvd) #effectue les transactions
                for i in data_send:
                    self.mq.send(str(data_send[i]).encode(), type=int(i)) #envoie la nouvelle valeur après échange à leur propriétaire à l'aide du PID
                self.barrier.wait()
        self.mq.remove()
                
    def processing(self, rcvd_dict):
        needed_dict = dict()
        available_dict = dict()
        for i in rcvd_dict:
            if rcvd_dict[i] < 0: #besoin d'energie
                needed_dict[i] = abs(rcvd_dict[i])
            elif rcvd_dict[i] > 0: #surplus d'energie
                available_dict[i] = rcvd_dict[i]

        while needed_dict and available_dict:       #tant qu'il y a des besoins ET des surplus d'energie
            key1, key2 = list(needed_dict.keys())[0], list(available_dict.keys())[0]        
            val_need, val_avlb = needed_dict[key1], available_dict[key2]       
            if val_need == val_avlb:
                needed_dict.pop(key1)       
                available_dict.pop(key2)        
            elif val_need < val_avlb:       
                needed_dict.pop(key1)      
                available_dict[key2] = val_avlb - val_need 
            else:  # val_need > val_avlb        
                available_dict.pop(key2)            
                needed_dict[key1] = val_need - val_avlb        
        
        for i in rcvd_dict:
            rcvd_dict[i] = 0 #considérons que toutes les transactions ont conduit à un parfait échange
        
        if needed_dict: #il reste des besoins d'energie après échange
            for i in needed_dict:
                rcvd_dict[i] = -needed_dict[i] #rajoute les besoins restants après la transaction dans rcvd
        elif available_dict: #il reste des surplus d'energie après échange
            for i in available_dict:
                rcvd_dict[i] = available_dict[i] #rajoute les surplus d'energie restants après la transaction dans rcvd
        #else : echange parfait donc aucune action puisqu'il confirme l'hypothèse ligne 62
        print("Sharing balance : ", rcvd_dict)
        return rcvd_dict

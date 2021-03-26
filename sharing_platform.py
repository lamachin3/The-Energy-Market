from multiprocessing import Process
import sysv_ipc, sys

key = 321

class SharingPlatform(Process):
    mq = None
    nb_houses = int

    def __init__(self, nb_houses):
        super().__init__()
        self.nb_houses = nb_houses
        try:
            self.mq = sysv_ipc.MessageQueue(key, sysv_ipc.IPC_CREX)
        except:
            print("Message queue", key, "already exsits, terminating.")
            sys.exit(1)

    def run(self):
        while True:
            if self.mq.current_messages == self.nb_houses:
                data_rcvd = dict()
                while self.mq.current_messages != 0:
                    msg = self.mq.receive(type=-3)[0].decode()
                    msg_split = msg.split("_")
                    data_rcvd[msg_split[1]] = int(msg_split[0])

                data_send = self.processing(data_rcvd)
                for i in data_send:
                    self.mq.send(str(data_send[i]).encode(), type=int(i))

    def processing(self, rcvd_dict):
        needed_dict = dict()
        available_dict = dict()
        for i in rcvd_dict:
            if rcvd_dict[i] < 0:
                needed_dict[i] = abs(rcvd_dict[i])
            elif rcvd_dict[i] > 0:
                available_dict[i] = rcvd_dict[i]

        while needed_dict and available_dict:
            key1, key2 = list(needed_dict.keys())[0], list(available_dict.keys())[0]
            val_need, val_avlb = needed_dict[key1], available_dict[key2]
            if val_need == val_avlb:
                needed_dict.pop(key1)
                available_dict.pop(key2)
            elif val_need < val_avlb:
                needed_dict.pop(key1)
                available_dict[key2] = val_avlb - val_need
            else:
                available_dict.pop(key2)
                needed_dict[key1] = val_need - val_avlb
        
        for i in rcvd_dict:
            rcvd_dict[i] = 0
        
        if needed_dict:
            for i in needed_dict:
                rcvd_dict[i] = -needed_dict[i]
        elif available_dict:
            for i in available_dict:
                rcvd_dict[i] = available_dict[i]

        return rcvd_dict

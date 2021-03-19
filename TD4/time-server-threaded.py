
import sys 
import time
import sysv_ipc
import threading

key = 666

def worker(mq, m):
    print("Starting thread:", threading.current_thread().name)
    dt = time.asctime()      
    message = str(dt).encode()
    pid = int(m.decode())
    t = pid + 3
    time.sleep(10)
    mq.send(message, type=t)
    print("Ending thread:", threading.current_thread().name)    

if __name__ == "__main__":
    print("Starting thread:", threading.current_thread().name)
    
    try:
        mq = sysv_ipc.MessageQueue(key, sysv_ipc.IPC_CREX)
    except ExistentialError:
        print("Message queue", key, "already exsits, terminating.")
        sys.exit(1)

    print("Starting time server.")

    threads = []
    while True:
        m, t = mq.receive()
        if t == 1:
            p = threading.Thread(target=worker, args=(mq, m))
            p.start()
            threads.append(p)
        if t == 2:
            for thread in threads:
                thread.join()
            mq.remove()                
            break
    
    print("Terminating time server.")
    print("Ending thread:", threading.current_thread().name)    

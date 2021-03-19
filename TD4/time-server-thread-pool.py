
import sys 
import time
import sysv_ipc
import concurrent.futures

key = 666

def worker(mq, m):
    dt = time.asctime()      
    message = str(dt).encode()
    pid = int(m.decode())
    t = pid + 3
    mq.send(message, type=t)


if __name__ == "__main__":
    try:
        mq = sysv_ipc.MessageQueue(key, sysv_ipc.IPC_CREX)
    except ExistentialError:
        print("Message queue", key, "already exsits, terminating.")
        sys.exit(1)

    print("Starting time server.")

    with concurrent.futures.ThreadPoolExecutor(max_workers = 4) as executor:
        while True:
            m, t = mq.receive(type = -2)
            if t == 1:
                executor.submit(worker, mq, m)
            if t == 2:
                mq.remove()                
                break
    
    print("Terminating time server.")

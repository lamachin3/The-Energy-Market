
import time
import random 
import multiprocessing
import math
import os

def is_prime(n):
    if n < 2:
        return (n, False)
    if n == 2:
        return (n, True)
    if n % 2 == 0:
        return (n, False)

    sqrt_n = int(math.floor(math.sqrt(n)))
    for i in range(3, sqrt_n + 1, 2):
        if n % i == 0:
            return (n, False)
    return (n, True)
    
if __name__ == "__main__":
    numbers = [random.randint(1000, 1000000) for i in range(100)]   # experiment with different lengths 10^2 to 10^6
    print(os.cpu_count()) #Print the number of CPU on this machine
    
    with multiprocessing.Pool() as pool:    # experiment with processes keyword argument
        start = time.time()
        results = pool.map(is_prime, numbers)
        # for r in results:
        #     print(r)
        end = time.time()
        print("Synchronous map:\t", end - start)
        
        start = time.time()
        results = pool.map_async(is_prime, numbers).get()
        # for r in results:
        #     print()
        end = time.time()
        print("Asynchronous map:\t", end - start)
        
        start = time.time()
        results = [pool.apply_async(is_prime, (n,)) for n in numbers]
        print(results[99].get())
        end = time.time()
        print("Asynchronous apply:\t", end - start)
        

import argparse
from queue import PriorityQueue
import numpy as np
from random import sample

class Peer:
    def __init__(self, num, slow, low_cpu):
        self.num = num
        self.slow = slow
        self.low_cpu = low_cpu
        self.balance = 0
        self.connected_peers = {}
        self.txn_pool = {}

class Transaction:
    def __init__(self, txn_id, payer_id, rec_id, amount):
        self.txn_id = txn_id
        self.payer_id = payer_id
        self.rec_id = rec_id
        self.amount = amount


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('n')
    parser.add_argument('z0')
    parser.add_argument('z1')
    args = parser.parse_args()
    peers = []
    slow_peers = set(sample(range(n),int(n*z0/100)))
    low_cpu_peers = set(sample(range(n),int(n*z1/100)))
    for i in range(n):
        slow = i in slow_peers
        low_cpu = i in low_cpu_peers
        peers.append(Peer(i,slow,low_cpu)
    event_queue = PriorityQueue()

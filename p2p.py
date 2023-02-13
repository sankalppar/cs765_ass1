import argparse
from queue import PriorityQueue
import numpy as np
from random import sample
import copy

T_tx = 0
event_queue = PriorityQueue()
links = None

class Peer:
    def __init__(self, num, slow, low_cpu, balances, id):
        self.num = num
        self.slow = slow
        self.low_cpu = low_cpu
        # self.balance = 0
        self.balances = balances
        self.connected_peers = set([])
        self.txn_pool = set([])
        self.id = id
        self.index = int(id)
        self.transactions_generated = 0
        
    def add_neighbor(self, neighbor):
        self.connected_peers.add(neighbor)
        
    def generate_transaction(self):
        time = np.random.exponential(scale = T_tx)
        receiver = None
        
        while(True):
            receiver = np.random.randint(low = 0, high = self.num, size = 1)
            if(receiver != self.index):
                break
            

        receiver_id = format(receiver.item(), '04d')
        
        amount = np.random.rand() # Uniform in 0 to 1
        txn_id = self.id + format(self.transactions_generated, '06d')
        txn = Transaction(txn_id, self.id, receiver_id, amount)
        self.transactions_generated += 1
        
        return time, txn
    
        

class Transaction:
    def __init__(self, txn_id, payer_id, rec_id, amount):
        self.txn_id = txn_id
        self.payer_id = payer_id
        self.rec_id = rec_id
        self.amount = amount
        
def init_Peers(n, z0, z1, balance_scale):
    peers = []

    # Initialize balances
    balances = np.random.rand(n)*balance_scale
    print("Initialized balances:", balances)

    slow_peers = set(sample(range(n),int(n*z0)))
    low_cpu_peers = set(sample(range(n),int(n*z1)))

    for i in range(n):
        slow = i in slow_peers
        low_cpu = i in low_cpu_peers
        peers.append(Peer(n, slow, low_cpu, balances, format(i, '04d')))

    
    return peers

def generate_graph(peers) :
    n = len(peers)
    graph = []
    for i in range(n):
        graph.append([])
    degrees_final = None
    
    while(True):
        
        degrees = np.random.randint(low = 4, high = 9, size = n)
        if(degrees.sum()%2==1):
            ids = np.where(degrees < 8)
            degrees[ids[0]] += 1
            
        for i in range(degrees.shape[0]):
            graph[i] = []
        
        degrees_final = copy.deepcopy(degrees)
            
        # remaining_degrees = degrees
        generated = True
        for i in range(n):
            if(degrees[i]==0):
                continue
            
            valid_indices = []
            for j in range(i+1, n):
                if(degrees[j] > 0):
                    valid_indices.append(j)
                    
            if(len(valid_indices) < degrees[i]):
                generated = False
                break
                
            indices = np.random.choice(valid_indices, size = degrees[i], replace = False)
            
            if(indices.shape[0] < degrees[i]):
                generated = False
                break
            
            for index in indices:
                degrees[i] -= 1
                degrees[index] -= 1
                graph[i].append(index)
                # graph[index].append(i)
                
        if(generated):
            break

    print("Generated graph")
    for i in range(len(graph)):
        # print(f"Degree of {peers[i].id} is {degrees_final[i]}")
        for j in range(len(graph[i])):
            peers[i].add_neighbor(peers[graph[i][j]])
            peers[graph[i][j]].add_neighbor(peers[i])
    
def generate_links(peers):
    global links
    links = {}
    n = len(peers)
            
    for i in range(n):
        peer = peers[i]
        for adj_peer in peer.connected_peers:
            adj_peer_index = int(adj_peer.id)

            if((i, adj_peer_index) in links):
                continue
            
            ro = 0.01 + 0.49*np.random.rand() # in seconds
            c = None
            if(peer.slow or adj_peer.slow):
                c = 5 # in MBps
            else:
                c = 100 # in Mbps
            
            links[(i, adj_peer_index)] = (ro, c)
            links[(adj_peer_index, i)] = (ro, c)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--n', type = int, required=True)
    parser.add_argument('--z0', type = float, required = True)
    parser.add_argument('--z1', type = float, required = True)
    parser.add_argument('--T_tx', type = float, required = True)
    args = parser.parse_args()
    n = args.n
    z0 = args.z0/100
    z1 = args.z1/100
    T_tx = args.T_tx
    balance_scale = 100

    # Initialize peers: 
    peers = init_Peers(n, z0, z1, balance_scale)
    
    # Generate network
    generate_graph(peers)
    
    # Generate links
    generate_links(peers)
    
    for i in range(n):
        time, txn = peers[i].generate_transaction()
        data = {"txn": txn}
        print(f"Transaction generated by {i} for time {time}, receiver is {txn.rec_id}")
        event_queue.put((time, "TxnGenerated" , data))
        
    # In event queue for each event, first value is time
    # second value is type of event
    # third value is the object (txn or block)
    
    # When transaction is generated, the payer puts it in its own txn set
    # and broadcasts to all neighbors
    # When a transaction is received, the receiver checks whether it is in his own txn set
    # if yes, it was already received, do nothing
    # else, broadast it to every neighbor except the one from whom you received it
        
    while(not event_queue.empty()):
        item = event_queue.get()
        curr_time = item[0]
        type = item[1]
        
        if(type=="TxnGenerated"):

            txn = item[2]['txn']
            payer_index = int(txn.payer_id)
            print(f"Transaction generated by {payer_index} for time {time}, receiver is {txn.rec_id}")
            
            # Put transaction to own txnset
            peers[payer_index].txn_pool.add(txn)
            
            # Broadcast generated transaction to all neighbors
            for neighbor in peers[payer_index].connected_peers:
                neighbor_index = neighbor.index
                ro, c = links[(payer_index, neighbor_index)] # link attr is (ro, c), ro in s, c in Mbps
                d = np.random.exponential(scale = 96*1e3/(c*1e6))
                prop_time = ro + 8*1e3/(c*1e6) + d
                
                data = {'sender': payer_index, 'txn': txn, 'receiver': neighbor_index}
                
                event_queue.put((curr_time + prop_time, "TxnReceived", data))
            
            time, new_txn = peers[payer_index].generate_transaction()
            event_queue.put((curr_time + time, "TxnGenerated", new_txn))

        if(type=="TxnReceived"):
            sender = item[2]['sender']
            receiver = item[2]['receiver']
            txn = item[2]['txn']
            
            # If transaction already received, do nothing
            # else, broadcast to all neighbors except from the one you received
            
            if(txn in peers['receiver']):
                continue
    
            for neighbor in peers[receiver].connected_peers:
                neighbor_index = neighbor.index
                if(neighbor_index == sender):
                    continue
            
                ro, c = links[(receiver, neighbor_index)] # link attr is (ro, c), ro in s, c in Mbps
                d = np.random.exponential(scale = 96*1e3/(c*1e6))
                prop_time = ro + 8*1e3/(c*1e6) + d
                
                data = {'sender': receiver, 'txn': txn, 'receiver': neighbor_index}
                
                event_queue.put((curr_time + prop_time, "TxnReceived", data))
                
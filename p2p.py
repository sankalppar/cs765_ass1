import argparse
from queue import PriorityQueue
import numpy as np
from random import sample
import copy

T_tx = 0
event_queue = PriorityQueue()
links = None
I = 600

class Peer:
    def __init__(self, num, slow, low_cpu, balances, id, hashing_power, gen_block):
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
        self.hashing_power = hashing_power
        self.gen_block = copy.deepcopy(gen_block)
        self.last_block = self.gen_block
        self.coinbase_generated = 1
        self.block_generated = 1
        self.block_set = {self.gen_block.blk_id : self.gen_block}

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

    def generate_coinbase(self):
        txn_id = self.id + format(self.coinbase_generated, '06d')
        txn = Transaction(txn_id, None, self.id, 50)
        self.coinbase_generated += 1
        return txn

    def generate_block(self, parent):
        time = np.random.exponential(scale = I/self.hashing_power)
        blk_id = self.id + format(self.block_generated, '06d')
        coinbase = self.generate_coinbase()
        blk_txns = set([])
        size = 0
        curr_balances = copy.deepcopy(parent.final_balance)
        for txn in self.txn_pool:
            if len(blk_txns) == 998:
                break
            if txn.amount <= curr_balances[int(txn.payer_id)]:
                blk_txns.add(txn)
                curr_balances[int(txn.payer_id)] -= txn.amount
        size = len(blk_txns) + 2
        blk_txns.add(coinbase)
        blk = Block(blk_id, parent, blk_txns, size, self.id, curr_balances)
        self.block_generated += 1
        return time, blk


class Transaction:
    def __init__(self, txn_id, payer_id, rec_id, amount):
        self.txn_id = txn_id
        self.payer_id = payer_id
        self.rec_id = rec_id
        self.amount = amount

class Block:
    def __init__(self, blk_id, parent, txns, size, creator_id, final_balance):
        self.blk_id = blk_id
        self.parent = parent
        self.txns = txns
        self.size = size
        self.creator_id = creator_id
        self.final_balance = final_balance
        self.children = []
        self.time = 0
        if parent:
            self.level = self.parent.level + 1
        else:
            self.level = 0

    def add_child(self, child_blk):
        new_blk = copy.deepcopy(child_blk)
        new_blk.parent = self
        self.children.append(new_blk)
        return new_blk


def init_Peers(n, z0, z1, balance_scale):
    peers = []

    # Initialize balances
    balances = np.random.rand(n)*balance_scale
    print("Initialized balances:", balances)

    slow_peers = set(sample(range(n),int(n*z0)))
    low_cpu_peers = set(sample(range(n),int(n*z1)))
    gen_txns = []
    for i in range(n):
        txn_id = format(i, '04d') + '000000'
        gen_txns.append(Transaction(txn_id, None, format(i, '04d'), balances[i]))
    gen_block_id = format(0, '10d')
    gen_block = Block(gen_block_id, None, gen_txns, len(gen_txns) + 1, None, balances)

    for i in range(n):
        slow = i in slow_peers
        low_cpu = i in low_cpu_peers
        if low_cpu:
            hashing_power = 1/(10*(1-z1) + z1)
        else:
            hashing_power = 10/(10*(1-z1) + z1)
        peers.append(Peer(n, slow, low_cpu, balances, format(i, '04d'), hashing_power, gen_block))

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
        print("Time:", time)
        # print(f"Transaction generated by {i} for time {time}, receiver is {txn.rec_id}")
        event_queue.put((time, "TxnGenerated" , data))
    for i in range(n):
        time, blk = peers[i].generate_block(peers[i].gen_block)
        data = {"blk": blk}
        print("Time:", time)
        event_queue.put((time, "BlkGenerated", data))
    input()
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
        
        if(curr_time > 1):
            break
        
        if(type=="TxnGenerated"):

            txn = item[2]['txn']
            payer_index = int(txn.payer_id)
            print(f"Transaction generated by {payer_index} at time {curr_time}, receiver is {txn.rec_id}")
            
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
                print(f"Sending transaction from {payer_index} to {neighbor_index} at {curr_time}")
            
            time, new_txn = peers[payer_index].generate_transaction()
            data = {'txn': new_txn}
            event_queue.put((curr_time + time, "TxnGenerated", data))

        if(type=="TxnReceived"):
            sender = item[2]['sender']
            receiver = item[2]['receiver']
            txn = item[2]['txn']
            
            # If transaction already received, do nothing
            # else, broadcast to all neighbors except from the one you received
            print(f"Transaction received from {sender} to {receiver} at {curr_time}")
            
            if(txn in peers[receiver].txn_pool):
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
                print(f"Sending transaction from {receiver} to {neighbor_index} at {curr_time}")

        if(type=="BlkGenerated"):
            blk = item[2]['blk']
            creator_index = int(blk.creator_id)

            #Check if block still valid
            if peers[creator_index].last_block != blk.parent:
                time, new_blk = peers[creator_index].generate_block(peers[creator_index].last_block)
                data = {'blk': new_blk}
                event_queue.put((curr_time + time, "BlkGenerated", data))
                continue

            peers[creator_index].balances = blk.final_balance

            #Broadcast block to neighbor nodes
            for neighbor in peers[creator_index].connected_peers:
                neighbor_index = neighbor.index
                ro, c = links[(payer_index, neighbor_index)] # link attr is (ro, c), ro in s, c in Mbps
                d = np.random.exponential(scale = 96*1e3/(c*1e6))
                prop_time = ro + 8*1e3*blk.size/(c*1e6) + d
                data = {'sender': creator_index, 'blk': blk, 'receiver': neighbor_index}
                event_queue.put((curr_time + prop_time, "BlkReceived", data))

            added_blk = peers[creator_index].last_block.add_child(blk)
            added_blk.time = curr_time
            peers[creator_index].last_block = added_blk
            time, new_blk = peers[creator_index].generate_block(blk)
            data = {'blk': new_blk}
            event_queue.put((curr_time + time, "BlkGenerated", data))

            print(f"Block generated by {creator_index} at time {curr_time}")

        if(type=="BlkReceived"):
            blk = item[2]['blk']
            sender_index = item[2]['sender']
            receiver_index = item[2]['receiver']

            if(peers['receiver_index'].block_set[blk.blk_id]):
                continue

            #Check if block is valid
            current_bal = copy.deepcopy(blk.parent.final_balance)
            valid_blk = True
            for txn in blk.txns:
                current_bal[int(txn.payer_id)] -= txn.amount
                if current_bal[int(txn.payer_id)] < 0:
                    valid_blk = False
                    break
            if not valid_blk:
                continue

            #Add to parent block
            parent_blk = peers['receiver_index'].block_set[blk.parent.blk_id]
            added_blk = parent_blk.add_child(blk)
            added_blk.time = curr_time
            peers['receiver_index'].block_set[added_blk.blk_id] = added_blk

            #Remove txns from txn pool
            peers['receiver_index'].txn_pool = peers['receiver_index'].txn_pool.difference(added_blk.txns)

            #Determine if this blockchain becomes longest
            if added_blk.level > peers['receiver_index'].last_block.level:
                peers['receiver_index'].last_block = added_blk

            #Send block to neighbors
            for neighbor in peers[receiver_index].connected_peers:
                neighbor_index = neighbor.index
                if(neighbor_index == sender):
                    continue
            
                ro, c = links[(receiver, neighbor_index)] # link attr is (ro, c), ro in s, c in Mbps
                d = np.random.exponential(scale = 96*1e3/(c*1e6))
                prop_time = ro + 8*1e3/(c*1e6) + d
                
                data = {'sender': receiver, 'blk': blk, 'receiver': neighbor_index}
                
                event_queue.put((curr_time + prop_time, "BlkReceived", data))






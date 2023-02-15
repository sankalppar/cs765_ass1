import argparse
from queue import PriorityQueue
import numpy as np
from random import sample, seed
import copy
import os

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
        self.block_cache = set([])

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
        curr_balances_new = copy.deepcopy(parent.final_balance)
        for txn in self.txn_pool:
            if len(blk_txns) == 998:
                break
            if txn.amount <= curr_balances[int(txn.payer_id)]:
                blk_txns.add(txn)
                curr_balances[int(txn.payer_id)] -= txn.amount
                curr_balances_new[int(txn.rec_id)] += txn.amount
                curr_balances_new[int(txn.payer_id)] -= txn.amount
        curr_balances_new[self.index] += 50
        size = len(blk_txns) + 2
        blk_txns.add(coinbase)
        blk = Block(blk_id, parent, blk_txns, size, self.id, curr_balances_new)
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

    slow_peers = set(sample(range(n),int(n*z0)))
    low_cpu_peers = set(sample(range(n),int(n*z1)))
    gen_txns = []
    for i in range(n):
        txn_id = format(i, '04d') + '000000'
        gen_txns.append(Transaction(txn_id, None, format(i, '04d'), balances[i]))
    gen_block_id = '0000000000'
    gen_block = Block(gen_block_id, None, gen_txns, len(gen_txns) + 1, None, balances)

    for i in range(n):
        slow = i in slow_peers
        low_cpu = i in low_cpu_peers
        if low_cpu:
            hashing_power = 1/((10*(1-z1) + z1)*n)
        else:
            hashing_power = 10/((10*(1-z1) + z1)*n)
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
    parser.add_argument('--seed', type = int, default=0)
    
    args = parser.parse_args()
    n = args.n
    z0 = args.z0/100
    z1 = args.z1/100
    T_tx = args.T_tx
    balance_scale = 100
    np.random.seed(args.seed)
    seed(args.seed)

    # Initialize peers: 
    peers = init_Peers(n, z0, z1, balance_scale)
    
    # Generate network
    generate_graph(peers)
    
    # Generate links
    generate_links(peers)
    
    for i in range(n):
        time, txn = peers[i].generate_transaction()
        data = {"txn": txn}
        #print("Time:", time)
        # print(f"Transaction generated by {i} for time {time}, receiver is {txn.rec_id}")
        event_queue.put((time, "TxnGenerated" , data))
    for i in range(n):
        time, blk = peers[i].generate_block(peers[i].gen_block)
        data = {"blk": blk}
        #print("Time:", time)
        event_queue.put((time, "BlkGenerated", data))
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
        
        if(curr_time > 10000):
            break
        
        if(type=="TxnGenerated"):

            txn = item[2]['txn']
            payer_index = int(txn.payer_id)
            
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
            data = {'txn': new_txn}
            event_queue.put((curr_time + time, "TxnGenerated", data))

        if(type=="TxnReceived"):
            sender = item[2]['sender']
            receiver = item[2]['receiver']
            txn = item[2]['txn']
            
            # If transaction already received, do nothing
            # else, broadcast to all neighbors except from the one you received
            
            if(txn in peers[receiver].txn_pool):
                continue

            peers[receiver].txn_pool.add(txn)
    
            for neighbor in peers[receiver].connected_peers:
                neighbor_index = neighbor.index
                if(neighbor_index == sender):
                    continue
            
                ro, c = links[(receiver, neighbor_index)] # link attr is (ro, c), ro in s, c in Mbps
                d = np.random.exponential(scale = 96*1e3/(c*1e6))
                prop_time = ro + 8*1e3/(c*1e6) + d
                
                data = {'sender': receiver, 'txn': txn, 'receiver': neighbor_index}
                
                event_queue.put((curr_time + prop_time, "TxnReceived", data))

        if(type=="BlkGenerated"):
            blk = item[2]['blk']
            creator_index = int(blk.creator_id)

            #Check if block still valid
            if peers[creator_index].last_block != blk.parent:
                #time, new_blk = peers[creator_index].generate_block(peers[creator_index].last_block)
                #data = {'blk': new_blk}
                #event_queue.put((curr_time + time, "BlkGenerated", data))
                #print(f"Block {blk.blk_id} failed")
                continue

            peers[creator_index].balances = blk.final_balance
            peers[creator_index].txn_pool = peers[creator_index].txn_pool.difference(blk.txns)

            #Broadcast block to neighbor nodes
            for neighbor in peers[creator_index].connected_peers:
                neighbor_index = neighbor.index
                ro, c = links[(creator_index, neighbor_index)] # link attr is (ro, c), ro in s, c in Mbps
                d = np.random.exponential(scale = 96*1e3/(c*1e6))
                prop_time = ro + 8*1e3*blk.size/(c*1e6) + d
                data = {'sender': creator_index, 'blk': blk, 'receiver': neighbor_index}
                event_queue.put((curr_time + prop_time, "BlkReceived", data))

            added_blk = peers[creator_index].last_block.add_child(blk)
            added_blk.time = curr_time
            peers[creator_index].last_block = added_blk
            peers[creator_index].block_set[added_blk.blk_id] = added_blk
            time, new_blk = peers[creator_index].generate_block(blk)
            data = {'blk': new_blk}
            event_queue.put((curr_time + time, "BlkGenerated", data))

            #print(f"Block generated by {creator_index} at time {curr_time}")

        if(type=="BlkReceived"):
            blk = item[2]['blk']
            sender_index = item[2]['sender']
            receiver_index = item[2]['receiver']

            if(blk.blk_id in peers[receiver_index].block_set.keys()):
                continue

            #Check if block is valid
            current_bal = copy.deepcopy(blk.parent.final_balance)
            valid_blk = True
            for txn in blk.txns:
                if(txn.payer_id != None):
                    current_bal[int(txn.payer_id)] -= txn.amount
                #current_bal[int(txn.rec_id)] += txn.amount
            for i in range(len(current_bal)):
                if current_bal[i] < 0:
                    valid_blk = False
            if not valid_blk or blk.size > 1000:
                continue

            #Add to cache if no parent
            if not(blk.parent.blk_id in peers[receiver_index].block_set.keys()):
                peers[receiver_index].block_cache.add(item[2])
                continue
            #Otherwise add child to parent
            parent_blk = peers[receiver_index].block_set[blk.parent.blk_id]
            added_blk = parent_blk.add_child(blk)
            added_blk.time = curr_time
            peers[receiver_index].block_set[added_blk.blk_id] = added_blk

            #Check if child already present in cache
            for block_data in peers[receiver_index].block_cache:
                if block_data['blk'].parent.blk_id == added_blk.blk_id:
                    peers[receiver_index].block_cache.remove(block_data)
                    event_queue.put((curr_time, "BlkReceived", block_data))

            #Remove txns from txn pool
            peers[receiver_index].txn_pool = peers[receiver_index].txn_pool.difference(added_blk.txns)

            #Determine if this blockchain becomes longest
            if added_blk.level > peers[receiver_index].last_block.level:
                peers[receiver_index].last_block = added_blk
                peers[receiver_index].balances = added_blk.final_balance
                time, new_blk = peers[receiver_index].generate_block(peers[receiver_index].last_block)
                data = {'blk': new_blk}
                event_queue.put((curr_time + time, "BlkGenerated", data))

            #Send block to neighbors
            for neighbor in peers[receiver_index].connected_peers:
                neighbor_index = neighbor.index
                if(neighbor_index == sender_index):
                    continue
            
                ro, c = links[(receiver_index, neighbor_index)] # link attr is (ro, c), ro in s, c in Mbps
                d = np.random.exponential(scale = 96*1e3/(c*1e6))
                prop_time = ro + 8*1e3*blk.size/(c*1e6) + d
                
                data = {'sender': receiver_index, 'blk': blk, 'receiver': neighbor_index}
                
                event_queue.put((curr_time + prop_time, "BlkReceived", data))
            #print(f"Block received by {receiver_index} at time {curr_time}")

    #Save blockchain tree along with time for each peer using level tree traversal
    if not os.path.exists(f'./trees/trees_{args.n}_{args.z0}_{args.z1}_{args.T_tx}_{args.seed}'):
        os.mkdir(f'./trees/trees_{args.n}_{args.z0}_{args.z1}_{args.T_tx}_{args.seed}')
    for i in range(n):
        treeFileStr = f'./trees/trees_{args.n}_{args.z0}_{args.z1}_{args.T_tx}_{args.seed}/tree' + str(i) + '.txt'
        treeFile = open(treeFileStr, 'w')
        gen_blk = peers[i].gen_block
        q = [gen_blk]
        while len(q) > 0:
            q_len = len(q)
            while q_len > 0:
                p = q[0]
                q.pop(0)
                if(p.parent != None):
                    print(f"{p.blk_id} ({p.parent.blk_id}) : {p.time} ", file=treeFile)
                else:
                    print(f"{p.blk_id} (genesis block) : {p.time} ", file=treeFile)
                for child in p.children:
                    q.append(child)
                q_len -= 1
            # print("",file=treeFile)
    treeFile.close()

    #Saving block related info into a file for debugging
    '''blockFile = open('block.txt', 'w')
    for i in range(n):
        print(f"Peer {i}", file=blockFile)
        for blk in peers[i].block_set.values():
            print(f"{blk.blk_id} {blk.size} {len(blk.txns)} {blk.final_balance}", file=blockFile)
    blockFile.close()'''

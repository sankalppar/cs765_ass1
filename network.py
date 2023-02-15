import networkx as nx
import matplotlib.pyplot as plt
import os
import graphviz, argparse
# G = nx.petersen_graph()

# subax1 = plt.subplot(121)
# nx.draw(G, with_labels = True, font_weight = 'bold')

# subax2 = plt.subplot(122)
# nx.draw_shell(G, nlist=[range(5, 10), range(5)], with_labels=True, font_weight='bold')

# plt.show()

import networkx as nx
import random

# dir_path = "./trees"
# num_trees = 20

parser = argparse.ArgumentParser()
parser.add_argument('--n', type = int, required=True)
parser.add_argument('--z0', type = float, required = True)
parser.add_argument('--z1', type = float, required = True)
parser.add_argument('--T_tx', type = float, required = True)
parser.add_argument('--seed', type = int, default=0)

args = parser.parse_args()

num_trees = args.n
dir_path  = f'./trees/trees_{args.n}_{args.z0}_{args.z1}_{args.T_tx}_{args.seed}'

    
def hierarchy_pos(G, root=None, width=1., vert_gap = 0.2, vert_loc = 0, xcenter = 0.5):


    if not nx.is_tree(G):
        raise TypeError('cannot use hierarchy_pos on a graph that is not a tree')

    if root is None:
        if isinstance(G, nx.DiGraph):
            root = next(iter(nx.topological_sort(G)))  #allows back compatibility with nx version 1.11
        else:
            root = random.choice(list(G.nodes))

    def _hierarchy_pos(G, root, width=1., vert_gap = 0.2, vert_loc = 0, xcenter = 0.5, pos = None, parent = None):

    
        if pos is None:
            pos = {root:(xcenter,vert_loc)}
        else:
            pos[root] = (xcenter, vert_loc)
        children = list(G.neighbors(root))
        if not isinstance(G, nx.DiGraph) and parent is not None:
            children.remove(parent)  
        if len(children)!=0:
            dx = width/len(children) 
            nextx = xcenter - width/2 - dx/2
            for child in children:
                nextx += dx
                pos = _hierarchy_pos(G,child, width = dx, vert_gap = vert_gap, 
                                    vert_loc = vert_loc-vert_gap, xcenter=nextx,
                                    pos=pos, parent = root)
        return pos
    
    return _hierarchy_pos(G, root, width, vert_gap, vert_loc, xcenter)


for peer_index in range(num_trees):
    file_path = os.path.join(dir_path, f"tree{peer_index}.txt")

    if(not os.path.exists(file_path)):
        print("File does not exist")
        
    file = open(file_path)

    lines = file.readlines()
    root = lines[1].split(' ')[0]

    nodes = []
    parents = []
    times = []
    
    num_blocks = len(lines) - 1

    for i in range(2,len(lines)):
        line = lines[i].strip()
        words = line.split(' ')
        node = words[0]
        parent = words[1]
        parent = parent[1:-1]
        time = float(words[-1])
        
        nodes.append(node)
        parents.append(parent)
        times.append(round(time, 3))
        
        # print(f"node {node}, parent {parent}, time {time}")
        

    G = nx.Graph()
    # G.add_node(root, {"Color": "Red"})
    G.add_nodes_from([(root, {"color": "red"})])
    color_map = ['red']

    labels = {}
    labels[root] = "Time: 0"
    # labels[root] = root + ", Time: 0"

    for i in range(len(nodes)):
        G.add_node(nodes[i])
        G.add_edge(nodes[i], parents[i])
        color_map.append('green')
        # labels[nodes[i]] = (nodes[i] + f", Time: {times[i]}")
        labels[nodes[i]] = (f"Time: {times[i]}")
        
    pos = hierarchy_pos(G, root)
    

    fig = plt.figure()
    fig.set_figheight(1*num_blocks)
    fig.set_figwidth(6)
    # subax1 = plt.subplot(121)
    nx.draw(G,  labels = labels, node_color = color_map,pos = pos, with_labels = True, font_weight = 'bold')
    
    if(not os.path.exists(dir_path + "/visual/")):
        os.mkdir(dir_path + "/visual/")
    # plt.show()
    plt.savefig(dir_path + "/visual/" + f"tree{peer_index}.png")
    del G
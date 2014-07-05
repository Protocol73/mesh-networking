# -*- coding: utf-8 -*-
# MIT Liscence : Nick Sweeting
version = "0.2" 
import traceback  
import time
import random

from node import VirtualLink, HardLink, Node

def adj(node1, node2):
    """returns # of hops it takes to get from node1 to node2, 1 means they're on the same link"""
    if node1 != node2 and set(node1.interfaces).intersection(set(node2.interfaces)):
        return 1
    else:
        return 0

def linkmembers(nodes, link):
    # members = []
    # for node in nodes:
    #     if link in node.interfaces:
    #         members += [node]
    # return members
    return [ node for node in nodes if link in node.interfaces ]

def eigenvalue(nodes, node=None):
    """
    calculate the eigenvalue (number of connections) for a given node in an array of nodes connected by an array of links
    if no node is given, return the minimum eigenvalue in the whole network
    """
    if node is None:
        min_eigen = 100
        for node in nodes:
            eigen = eigenvalue(nodes, node)
            if eigen < min_eigen:
                min_eigen = eigen
        return min_eigen
    else:
        eigen = 0
        for node2 in nodes:
            if adj(node, node2):
                eigen += 1
        return eigen

def commandloop():
    dont_exit = True
    try:
        while dont_exit:
            command = str(raw_input("[$]:"))

            if command[:1] == "l":
                # LINK COMMANDS
                idx = int(command[1:])
                if -1 < idx < len(links):
                    link = links[idx]
                    link_members = linkmembers(nodes, link)
                    message = str(raw_input("%s(%s) %s:" % (link, len(link_members), link_members)))
                    if message == "stop":
                        link.stop()
                    else:
                        link.send(message)
                else:
                    print "Not a link."
                
            elif command[:1] == "n":
                # NODE COMMANDS
                idx = int(command[1:])
                if -1 < idx < len(nodes):
                    node = nodes[idx]
                    message = str(raw_input("%s<%s> ∂%s:" % (node, node.interfaces, eigenvalue(nodes, node))))
                    if message == "stop":
                        node.stop()
                    else:
                        node.broadcast(message)
                else:
                    print "Not a node."
                
            elif command[:1] == "":
                # NODE COMMANDS
                print "duh"

            time.sleep(0.5)
    except KeyboardInterrupt:
        for node in nodes:
            node.stop()
        links[0].stop()
        print("EXITING CLEANLY")
        exit(0)
    except Exception as e:
        for node in nodes:
            node.stop()
        links[0].stop()
        traceback.print_exc()
        raise SystemExit(1)

def fmt(type, value, fallback=None):
    try:
        return type(value)
    except ValueError:
        return fallback

if __name__ == "__main__":
    num_nodes = fmt(int, raw_input("How many nodes do you want? (26):"), 26)
    num_links = fmt(int, raw_input("How many links do you want? (40):"), 40)
    bridge    = fmt(int, raw_input("Link to wifi too, if so, on what port? (0 for no/#):"), False)
    randomize = False if str(raw_input("Randomize links, or play God? (r/g)"))[:1].lower() == "g" else True                 # chose entropy or order

    links = [ HardLink("en1", bridge) ] if bridge else [ VirtualLink("l0") ]
    links += [ VirtualLink("l%s" % (x+1)) for x in range(num_links-1) ]
    for link in links:
        link.start()
        print link

    nodes = [ Node([], "n%s" % x) for x in range(num_nodes) ]

    desired_min_eigenvalue = 2

    if randomize:
        for link in links:
            node1 = random.choice(nodes)
            node1.add_interface(link)
            node2 = random.choice(nodes)
            while node2 == node1 and len(nodes) > 1:
                node2 = random.choice(nodes)
            node2.add_interface(link)
        #and another sweep to catch all the unlinked nodes
        underconnected_nodes = filter(lambda x: True if len(x.interfaces) < desired_min_eigenvalue else False, nodes)
        while underconnected_nodes:
            print "Second pass."
            for node in underconnected_nodes:
                node.add_interface(random.choice(links))
            underconnected_nodes = filter(lambda x: True if len(x.interfaces) < desired_min_eigenvalue else False, nodes)
            
            
    print "Let there be life."
    for node in nodes:
        print "%s:(%s)\n" % (node, node.interfaces),
        node.start()
    
    commandloop()



"""

   ^      \/
   |      |
   |      |
   \      /
    \    /
     \  /
      |
       |
      |
       |
      |
       |
      |
       |        < 4 bits can be sent in one clock tick
      |                 - 2b up
       |                - 2b down
      |
       |          or
      |
       |                - 1b up and 1b down in one tick


two cables, each cable can transmit one packet per tick
in order to switch transmission directions there is a 
small latency between ticks.

this is a graph of the cable's state over time (time increases going down)
^ means the traffic is going up; , means it's going down

|^||^| time = 2 ticks; up, down = 2,2
------       1 tick delay for each direction switch
|,||,|
------
|^||^|
------
|,||,|
------       wasted tick is the time it takes the line to empty the buffer holding the packet
|^||^|
------
|,||,|
------
|^||^|
------
|,||,|
------
|^||^|

|,||^| time = 2 ticks; up, down = 2,2
|,||^|       no delay
|,||^|
|,||^|
|,||^|
|,||^|
|,||^|
|,||^|       meanwhile, there are no ---- because packets can be streames one after another, crammed in tight
|,||^|
|,||^|
|,||^|
|,||^|
|,||^|
|,||^|
|,||^|
|,||^|
|,||^|

thus, in the same amount of time, a full-duplex setup where up and down are split
on seperate wires will always beat two single time-sharing duplex cables

of course, the wasted time will be much lower on a short line (probably in the <1ms range), but on longer cables
it can probably grow to >1ms, which really slows down an ethernet cable trying to run at 100mbps.


 """

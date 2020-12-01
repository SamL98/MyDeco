class Node(object):
    NUM_NODES = 0

    def __init__(self, predecessor=None, predecessors=None, successors=None, idx=-1, name=None):
        self.predecessors = predecessors
        if predecessors is None:
            self.predecessors = []

        self.successors = successors
        if successors is None:
            self.successors = []

        self.idx = idx
        self.name = name

        if name is None:
            self.name = 'node_%d' % Node.NUM_NODES

        Node.NUM_NODES += 1

        if predecessor is not None:
            self.add_predecessor(predecessor)

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def set_idx(self, idx):
        self.idx = idx

    def add_predecessor(self, predecessor):
        self.predecessors.append(predecessor)
        predecessor.add_successor(self)

    def add_successor(self, successor):
        self.successors.append(successor)

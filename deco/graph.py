import pdb
from collections import defaultdict

from node import Node


class Graph(object):
    def __init__(self, nodes):
        start_nodes = []
        other_nodes = []

        for node in nodes:
            if len(node.predecessors) == 0:
                start_nodes.append(node)
            else:
                other_nodes.append(node)

        self.nodes = start_nodes + other_nodes

    def idom(self, node):
        return self.doms[node.idx]

    def set_idom(self, node, idom):
        self.doms[node.idx] = idom

    def shared_idom(self, node1, node2):
        while node1.idx != node2.idx:
            if node1.idx < node2.idx: node1 = self.idom(node1)
            else:                     node2 = self.idom(node2)
        return node1

    def generate_dom_tree(self):
        self.doms = {node.idx: None for node in self.nodes}
        self.set_idom(self.start, self.start)

        changed = True

        while changed:
            changed = False

            for node in self.nodes[:-1][::-1]: # reverse postorder
                # DEBUG
                for p in node.predecessors:
                    if p not in self.nodes:
                        pdb.set_trace()
                # END

                processed_preds = [p for p in node.predecessors if self.idom(p) is not None]

                if len(processed_preds) == 0:
                    continue

                new_idom = processed_preds[0]

                for pred in processed_preds:
                    pred_idom = self.idom(pred)
                    new_idom = self.shared_idom(pred, new_idom) 

                prev_idom = self.idom(node)

                if prev_idom is None or prev_idom.idx != new_idom.idx:
                    self.set_idom(node, new_idom)
                    changed = True

        # Reverse the idom `doms` linked list to get the dom tree adjacency list.
        dt_nodes = []

        def get_dt_node(node):
            if node in dt_nodes:
                return dt_nodes[dt_nodes.index(node)]
            else:
                dt_node = Node(name=node.name)
                dt_nodes.append(dt_node)
                return dt_node

        for node in self.nodes[:-1]:
            dt_node = get_dt_node(node)

            prev_idom = node
            idom = self.idom(prev_idom)
            if idom is None:
                pdb.set_trace()

            while idom != prev_idom:
                dt_idom = get_dt_node(idom)
                dt_node.add_predecessor(dt_idom)

                prev_idom = idom
                idom = self.idom(prev_idom)

        self.dom_tree = Graph(dt_nodes)

    def generate_dom_frontiers(self):
        self.frontiers = defaultdict(set)

        for node in self.nodes:
            if len(node.predecessors) < 2:
                continue

            idom = self.idom(node)

            for pred in node.predecessors:
                runner = pred
                while runner.idx != idom.idx:
                    self.frontiers[runner.idx].add(node)
                    runner = self.idom(runner)

    def frontier(self, node):
        return self.frontiers[node.idx]

    def dfs_(self, node, visited, pre_fn=None, post_fn=None):
        if pre_fn is not None:
            pre_fn(node)

        visited.add(node)

        for succ in node.successors:
            if succ not in visited:
                self.dfs_(succ, visited, pre_fn=pre_fn, post_fn=post_fn)

        if post_fn is not None:
            post_fn(node)

    def dfs(self, pre_fn=None, post_fn=None):
        visited = set()

        for node in self.nodes:
            if node not in visited:
                self.dfs_(node, visited, pre_fn=pre_fn, post_fn=post_fn)

    def sort_by_postorder(self):
        idx_ctr = 0

        def set_idx(node):
            nonlocal idx_ctr
            node.set_idx(idx_ctr)
            print(hex(int(node.start)), node.idx)
            idx_ctr += 1

        self.dfs(post_fn=set_idx)
        self.nodes = sorted(self.nodes, key=lambda n: n.idx)
        print([node.idx for node in self.nodes])
        self.start = self.nodes[-1]

    def copy(self, copy_fn):
        new_nodes = {}

        def copy_and_track(node):
            new_node = copy_fn(node)
            new_nodes[node.name] = new_node

        def reconstruct_edges(node):
            new_node = new_nodes[node.name]

            for succ in node.successors:
                new_succ = new_nodes[succ.name]
                new_succ.add_predecessor(new_node)

        self.dfs(pre_fn=copy_and_track, post_fn=reconstruct_edges)
        return type(self)(list(new_nodes.values()))

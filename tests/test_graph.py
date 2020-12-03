import sys
sys.path.insert(0, '..')

import pdb
import unittest

from collections import defaultdict

from graph import Graph
from node import Node

# Super simple test graph
ss_node4 = Node(name='ss_node_4')
ss_node2 = Node(ss_node4, name='ss_node_2')
ss_node3 = Node(ss_node4, name='ss_node_3')
ss_node1 = Node(ss_node2, name='ss_node_1')
super_simple_graph_nodes = [ss_node3, ss_node2, ss_node1, ss_node4]

# Simple test graph
s_node5 = Node(name='s_node_5')
s_node3 = Node(s_node5, name='s_node_3')
s_node4 = Node(s_node5, name='s_node_4')
s_node2 = Node(s_node3, name='s_node_2')
s_node1 = Node(s_node4, name='s_node_1')
s_node1.add_predecessor(s_node2)
s_node2.add_predecessor(s_node1)
simple_graph_nodes = [s_node5, s_node2, s_node3, s_node4, s_node1]

# Complex test graph
c_node6 = Node(name='c_node_6')
c_node4 = Node(c_node6, name='c_node_4')
c_node5 = Node(c_node6, name='c_node_5')
c_node3 = Node(c_node4, name='c_node_3')
c_node2 = Node(c_node4, name='c_node_2')
c_node1 = Node(c_node5, name='c_node_1')
c_node1.add_predecessor(c_node2)
c_node2.add_predecessor(c_node1)
c_node2.add_predecessor(c_node3)
c_node3.add_predecessor(c_node2)
complex_graph_nodes = [c_node6, c_node5, c_node2, c_node3, c_node4, c_node1]


class TestGraph(unittest.TestCase):
    def test_super_simple_graph_creation(self):
        self.assertEqual(len(ss_node4.predecessors), 0)
        self.assertEqual(len(ss_node4.successors), 2)
        self.assertEqual(ss_node4.successors, [ss_node2, ss_node3])

        self.assertEqual(len(ss_node3.predecessors), 1)
        self.assertEqual(len(ss_node3.successors), 0)
        self.assertEqual(ss_node3.predecessors, [ss_node4])

        self.assertEqual(len(ss_node2.predecessors), 1)
        self.assertEqual(len(ss_node2.successors), 1)
        self.assertEqual(ss_node2.predecessors, [ss_node4])
        self.assertEqual(ss_node2.successors, [ss_node1])

        self.assertEqual(len(ss_node1.predecessors), 1)
        self.assertEqual(len(ss_node1.successors), 0)
        self.assertEqual(ss_node1.predecessors, [ss_node2])

    def test_postorder_super_simple(self):
        super_simple_graph = Graph(super_simple_graph_nodes)
        super_simple_graph.sort_by_postorder()

        self.assertEqual(super_simple_graph.nodes, [ss_node1, ss_node2, ss_node3, ss_node4])

    def test_dom_tree_super_simple(self):
        super_simple_graph = Graph(super_simple_graph_nodes)
        super_simple_graph.sort_by_postorder()
        super_simple_graph.generate_dom_tree()

        doms = {
            0: ss_node2,
            1: ss_node4,
            2: ss_node4,
            3: ss_node4
        }

        self.assertEqual(super_simple_graph.doms, doms)

    def test_dom_frontiers_super_simple(self):
        super_simple_graph = Graph(super_simple_graph_nodes)
        super_simple_graph.sort_by_postorder()
        super_simple_graph.generate_dom_tree()
        super_simple_graph.generate_dom_frontiers()

        self.assertEqual(super_simple_graph.frontiers, defaultdict(set))

    def test_simple_graph_creation(self):
        self.assertEqual(len(s_node5.predecessors), 0)
        self.assertEqual(len(s_node5.successors), 2)
        self.assertEqual(s_node5.successors, [s_node3, s_node4])

        self.assertEqual(len(s_node4.predecessors), 1)
        self.assertEqual(len(s_node4.successors), 1)
        self.assertEqual(s_node4.predecessors, [s_node5])
        self.assertEqual(s_node4.successors, [s_node1])

        self.assertEqual(len(s_node3.predecessors), 1)
        self.assertEqual(len(s_node3.successors), 1)
        self.assertEqual(s_node3.predecessors, [s_node5])
        self.assertEqual(s_node3.successors, [s_node2])

        self.assertEqual(len(s_node2.predecessors), 2)
        self.assertEqual(len(s_node2.successors), 1)
        self.assertEqual(s_node2.predecessors, [s_node3, s_node1])
        self.assertEqual(s_node2.successors, [s_node1])

        self.assertEqual(len(s_node1.predecessors), 2)
        self.assertEqual(len(s_node1.successors), 1)
        self.assertEqual(s_node1.predecessors, [s_node4, s_node2])
        self.assertEqual(s_node1.successors, [s_node2])

    def test_postorder_simple(self):
        simple_graph = Graph(simple_graph_nodes)
        simple_graph.sort_by_postorder()

        self.assertEqual(simple_graph.nodes, [s_node1, s_node2, s_node3, s_node4, s_node5])

    def test_dom_tree_simple(self):
        simple_graph = Graph(simple_graph_nodes)
        simple_graph.sort_by_postorder()
        simple_graph.generate_dom_tree()

        self.assertEqual(simple_graph.doms, {i: s_node5 for i in range(5)})

    def test_dom_frontiers_simple(self):
        simple_graph = Graph(simple_graph_nodes)
        simple_graph.sort_by_postorder()
        simple_graph.generate_dom_tree()
        simple_graph.generate_dom_frontiers()

        frontiers = {
            0: {s_node2},
            1: {s_node1},
            2: {s_node2},
            3: {s_node1}
        }

        self.assertEqual(simple_graph.frontiers, frontiers)

    def test_postorder_complex(self):
        complex_graph = Graph(complex_graph_nodes)
        complex_graph.sort_by_postorder()

        self.assertEqual(complex_graph.nodes, [c_node1, c_node2, c_node3, c_node4, c_node5, c_node6])

    def test_dom_tree_complex(self):
        complex_graph = Graph(complex_graph_nodes)
        complex_graph.sort_by_postorder()
        complex_graph.generate_dom_tree()

        self.assertEqual(complex_graph.doms, {i: c_node6 for i in range(6)})

    def test_dom_frontiers_complex(self):
        complex_graph = Graph(complex_graph_nodes)
        complex_graph.sort_by_postorder()
        complex_graph.generate_dom_tree()
        complex_graph.generate_dom_frontiers()

        frontiers = {
            0: {c_node2},
            1: {c_node1, c_node3},
            2: {c_node2},
            3: {c_node2, c_node3},
            4: {c_node1}
        }

        self.assertEqual(complex_graph.frontiers, frontiers)


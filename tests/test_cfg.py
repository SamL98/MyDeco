import sys
sys.path.insert(0, '..')

import unittest

from block import Block
from cfg import CFG


# Simple test graph
s_block1 = Block(name='s_block_1')
s_block2 = Block(s_block1, name='s_block_2')
s_block3 = Block(s_block1, name='s_block_3')
s_block4 = Block(s_block3, name='s_block_4')
simple_graph_blocks = [s_block2, s_block3, s_block4, s_block1]

# Complex test graph
c_block6 = Block(name='c_block_6')
c_block4 = Block(c_block6, name='c_block_4')
c_block5 = Block(c_block6, name='c_block_5')
c_block3 = Block(c_block4, name='c_block_3')
c_block2 = Block(c_block4, name='c_block_2')
c_block1 = Block(c_block5, name='c_block_1')
c_block1.add_predecessor(c_block2)
c_block2.add_predecessor(c_block1)
c_block2.add_predecessor(c_block3)
c_block3.add_predecessor(c_block2)
complex_graph_blocks = [c_block6, c_block5, c_block2, c_block3, c_block4, c_block1]

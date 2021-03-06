import sys
sys.path.insert(0, '..')

import unittest

from blocks import Block
from cfg import CFG
from insn import Instruction
from pcode import PcodeOp
from varnode import Varnode

insn_addr = 0
insn_len = 4
reg_size = 4

r1 = Varnode('register', 0, reg_size)
r2 = Varnode('register', reg_size, reg_size)
r3 = Varnode('register', reg_size * 2, reg_size)
u0 = Varnode('unique', 0, reg_size)
insn1 = Instruction(insn_addr, insn_len, [PcodeOp(insn_addr, 'INT_ADD', [r1, r2], u0)])
insn2 = Instruction(insn_addr, insn_len, [PcodeOp(insn_addr, 'COPY', [u0], r3)])
insn3 = Instruction(insn_addr, insn_len, [PcodeOp(insn_addr, 'COPY', [u0], r1)])

# Simple test CFG
s_block1 = Block([insn1], name='s_block_1')
s_block2 = Block([insn1], predecessor=s_block1, name='s_block_2')
s_block3 = Block([insn1], predecessor=s_block1, name='s_block_3')
s_block4 = Block([insn1], predecessor=s_block3, name='s_block_4')
simple_cfg_blocks = [s_block2, s_block3, s_block4, s_block1]

# Complex test CFG 1
c1_block1 = Block([insn1.copy(), insn2], name='c1_block_1')
c1_block2 = Block([insn1.copy()], predecessor=c1_block1, name='c1_block_2')
c1_block3 = Block([insn1.copy()], predecessor=c1_block1, name='c1_block_3')
c1_block4 = Block([insn1.copy()], predecessor=c1_block3, name='c1_block_4')
c1_block4.add_predecessor(c1_block2)
complex1_cfg_blocks = [c1_block2, c1_block3, c1_block4, c1_block1]

# Complex test CFG 2 
c2_block1 = Block([insn1.copy(), insn2], name='c2_block_1')
c2_block2 = Block([insn1.copy(), insn3], predecessor=c2_block1, name='c2_block_2')
c2_block3 = Block([insn1.copy()], predecessor=c2_block1, name='c2_block_3')
c2_block4 = Block([insn1.copy()], predecessor=c2_block3, name='c2_block_4')
c2_block4.add_predecessor(c2_block2)
c2_block5 = Block([insn1.copy()], predecessor=c2_block4, name='c2_block_5')
complex2_cfg_blocks = [c2_block2, c2_block3, c2_block4, c2_block1, c2_block5]


class TestCFG(unittest.TestCase):
    def test_insert_phis_simple(self):
        cfg = CFG(simple_cfg_blocks)
        phis_inserted = cfg.insert_phis()

        self.assertEqual(phis_inserted, 0)

    def test_insert_phis_complex_1(self):
        cfg = CFG(complex1_cfg_blocks)
        phis_inserted = cfg.insert_phis()

        self.assertEqual(phis_inserted, 1)

        for blk in [c1_block1, c1_block2, c1_block3]:
            for insn in blk.insns:
                self.assertEqual(insn.num_phis(), 0)

        insn = c1_block4.insns[0]
        self.assertEqual(insn.num_phis(), 1)
        self.assertEqual(insn.pcode[0].output, r3)

    def test_insert_phis_complex_2(self):
        cfg = CFG(complex2_cfg_blocks)
        phis_inserted = cfg.insert_phis()

        self.assertEqual(phis_inserted, 2)

        for blk in [c2_block1, c2_block2, c2_block3, c2_block5]:
            for insn in blk.insns:
                self.assertEqual(insn.num_phis(), 0)

        insn = c2_block4.insns[0]
        self.assertEqual(insn.num_phis(), 2)

        outputs = set([pcop.output for pcop in insn.pcode if pcop.is_phi()])
        self.assertEqual(outputs, set({r3, r1}))

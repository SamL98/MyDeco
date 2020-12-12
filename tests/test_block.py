import sys
sys.path.insert(0, '..')

import unittest

from blocks import decompose_into_blocks
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

insn_addr += insn_len
insn2 = Instruction(insn_addr, insn_len, [PcodeOp(insn_addr, 'COPY', [u0], r3)])

insn_addr += insn_len
insn3 = Instruction(insn_addr, insn_len, [PcodeOp(insn_addr, 'COPY', [u0], r1)])

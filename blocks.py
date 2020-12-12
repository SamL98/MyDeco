from functools import reduce

from node import Node
from pcode import PhiOp, PcodeList, addr_to_str


class Block(Node):
    def __init__(self, start, **kwargs):
        super().__init__(**kwargs)
        self.start = start


class InstructionBlock(Block):
    def __init__(self, insns, **kwargs):
        start = insns[0].addr
        end = insns[-1].addr
        super().__init__(start, **kwargs)

        self.insns = insns
        self.end = end

    def __len__(self):
        return len(self.insns)

    def __repr__(self):
        addr_str = '%s: ' % addr_to_str(self.start)
        return '\n'.join([addr_str + str(self.insns[0])] + [(' ' * len(addr_str)) + str(insn) for insn in self.insns[1:]])

    def contains(self, addr, inclusive=True):
        is_within = addr <= self.end

        if inclusive:
            return is_within and (addr >= self.start)
        else:
            return is_within and (addr > self.start)

    def split(self, at_addr, predecessor=None):
        e = 1

        while self.insns[e].addr != at_addr:
            e += 1

        return [Block(self.insns[:e], predecessors=self.predecessors, successors=self.successors), 
                Block(self.insns[e:], predecessor=predecessor)]


class PcodeBlock(PcodeList, Block):
    def __init__(self, pcode, **kwargs):
        start = pcode[0].addr
        PcodeList.__init__(self, start, pcode)
        Block.__init__(self, start, **kwargs)

    @staticmethod
    def fromiblock(iblock):
        return PcodeBlock(reduce(lambda x,y: x+y, [insn.pcode for insn in iblock.insns]))

    def insert_phis(self, varnodes):
        phis = [PhiOp.fromblock(self, v) for v in varnodes]
        self.prepend_pcode(phis)
        return len(phis)

    def convert_to_ssa(self):
        super().convert_to_ssa()

        for succ in self.successors:
            for phi in succ.phis():
                phi.replace_input(self)


from functools import reduce
import pdb

from node import Node
from pcode import PhiOp, PcodeList, addr_to_str


class Block(Node):
    def __init__(self, start, elems, **kwargs):
        super().__init__(**kwargs)
        self.start = start
        self.elems = elems

    def fallthrough(self):
        if len(self.successors) == 0:
            return None

        ft = self.successors[0]

        # If you branch but unconditionally (i.e. jmp), the first successor still counts as the fallthrough.
        # It *also* counts as the target. Is this bad? I also don't know how I'm going to deal with indirect
        # branches (i.e. switches) so I'll ignore them for now.
        if self.branches() and self.is_conditional() and not self.is_indirect():
            for succ in self.successors:
                if succ.start != self.elems[-1].target():
                    ft = succ
                    break

        return ft

    def target(self):
        if self.branches():
            for succ in self.successors:
                if succ.start == self.elems[-1].target():
                    return succ

    def draw_vertex(self, g):
        g.node(self.name, addr_to_str(self.start))


class InstructionBlock(Block):
    def __init__(self, insns, **kwargs):
        start = insns[0].addr
        end = insns[-1].addr
        super().__init__(start, insns, **kwargs)

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
        Block.__init__(self, start, pcode, **kwargs)

    @staticmethod
    def fromiblock(iblock):
        return PcodeBlock(reduce(lambda x,y: x+y, [insn.pcode for insn in iblock.insns]))

    def insert_phis(self, varnodes):
        phis = [PhiOp.fromblock(self, v) for v in varnodes]
        self.prepend_pcode(phis)
        return len(phis)

    def target(self):
        return Block.target(self)

    def fallthrough(self):
        return Block.fallthrough(self)

    def convert_to_ssa(self):
        super().convert_to_ssa()

        for succ in self.successors:
            for phi in succ.phis():
                phi.replace_input(self)

    def draw_edges(self, g):
        # Again, I'll deal with switches when they come.
        if len(self.successors) > 2:
            Block.draw_edges(self, g)
        else:
            if self.pcode[-1].branches() and self.pcode[-1].is_conditional():
                g.edge(self.name, self.target().name, label='target')

        if len(self.successors) > 0:
            g.edge(self.name, self.fallthrough().name)

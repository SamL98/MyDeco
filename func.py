from cfg import CFG
from insn import Instruction
from blocks import decompose_into_blocks


class Function(object):
    def __init__(self, blocks):
        self.cfg = CFG(blocks)

    def __repr__(self):
        sep = '-' * 50
        return '\n'.join(reduce(lambda x,y: x+y,
                                [[sep, str(blk), sep] for blk in self.blocks]))

    @staticmethod
    def unserialize(j):
        insns = reduce(lambda x,y: x+y, [Instruction.unserialize(ij) for ij in j])
        return Function(decompose_into_blocks(insns))

    def simplify(self):
        new_blocks = []

        for blk in self.blocks:
            blk.simplify()

            if len(blk.insns) > 0:
                new_blocks.append(blk)

        self.blocks = new_blocks

    def convert_to_ssa(self):
        for blk in self.blocks:
            blk.convert_to_ssa()

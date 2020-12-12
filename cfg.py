from collections import defaultdict
from functools import reduce

from blocks import InstructionBlock, PcodeBlock
from graph import Graph
from insn import Instruction


def get_block_containing(addr, blocks):
    for start, blk in blocks.items():
        if blk.contains(addr, inclusive=False):
            return start
    return None


def decompose_into_blocks(insns):
    blocks = {}

    insn_lookup = {insn.addr: insn for insn in insns}
    addr_buff = [(insns[0].addr, [], None)]

    while len(addr_buff) > 0:
        addr, curr_block, predecessor = addr_buff.pop(-1)

        if addr in blocks:
            blk = InstructionBlock(curr_block, predecessor=predecessor)
            blocks[blk.start] = blk
            curr_block = []
            blocks[addr].add_predecessor(blk)
            continue

        cont_blk_start = get_block_containing(addr, blocks)

        if cont_blk_start is not None:
            cont_blk = blocks[cont_blk_start]
            new_blocks = cont_blk.split(addr, predecessor)

            del blocks[cont_blk_start]
            for blk in new_blocks:
                blocks[blk.start] = blk
            continue

        insn = None

        if addr in insn_lookup:
            insn = insn_lookup[addr]

        if insn is not None:
            curr_block.append(insn)

        if insn is None or insn.terminates():
            blk = InstructionBlock(curr_block, predecessor=predecessor)
            blocks[blk.start] = blk
            curr_block = []
            predecessor = blk

        if insn is not None:
            if insn.fallthrough() is not None:
                addr_buff.append((insn.fallthrough(), curr_block, predecessor))

            if insn.target() is not None:
                addr_buff.append((insn.target(), [], blk))

    if len(curr_block) > 0:
        blk = InstructionBlock(curr_block, predecessor=predecessor)
        blocks[blk.start] = blk

    return sorted(blocks.values(), key=lambda b: b.start)


class CFG(Graph):
    def __init__(self, blocks):
        super().__init__(blocks)

        self.sort_by_postorder()
        self.generate_dom_tree()
        self.generate_dom_frontiers()

        self.blocks = self.nodes
        self.entry = self.start

    def __repr__(self):
        sorted_blocks = sorted(self.blocks, key=lambda b: b.start)

        sep = '-' * 50
        return '\n'.join(reduce(lambda x,y: x+y,
                                [[sep, str(blk), sep] for blk in sorted_blocks]))


    @staticmethod
    def fromjson(j):
        insns = reduce(lambda x,y: x+y, [Instruction.fromjson(ij) for ij in j])
        insn_blocks = decompose_into_blocks(insns)
        insn_CFG = CFG(insn_blocks)
        return insn_CFG.copy(lambda iblock: PcodeBlock.fromiblock(iblock))

    def insert_phis(self):
        phis_inserted = 0
        visited = set()
        all_varnodes = reduce(lambda x,y: x+y,
                              [blk.written_varnodes(ignore_uniq=True) for blk in self.blocks])

        for blk in self.blocks:
            buff = self.frontier(blk)

            while len(buff) > 0:
                df_blk = buff.pop()

                if df_blk in visited:
                    continue

                phis_inserted += df_blk.insert_phis(all_varnodes)

                visited.add(df_blk)
                buff.update(self.frontier(df_blk))

        return phis_inserted

    def convert_to_ssa(self):
        self.insert_phis()

        def convert_block_to_ssa(blk):
            print('Converting %s to SSA' % blk.name)
            blk.convert_to_ssa()

        def unwind_version(blk):
            blk.unwind_version()

        self.dom_tree.dfs_(self.entry, 
                           set(), 
                           pre_fn=convert_block_to_ssa, 
                           post_fn=unwind_version)

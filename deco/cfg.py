import pdb
from collections import defaultdict
from functools import reduce
from graphviz import Digraph

from blocks import InstructionBlock, PcodeBlock
from graph import Graph
from insn import Instruction
from utils import addr_to_str


def get_block_containing(addr, blocks):
    for start, blk in blocks.items():
        if blk.contains(addr, inclusive=False):
            return start
    return None


def decompose_into_blocks(insns):
    """
    Group the instructions into basic blocks.

    Do this by performing DFS on the instruction graph. In this graph,
        there is an edge from an instruction to its fallthrough (if applicable)
        and edges from branches to target.
    """
    blocks = {}

    insn_lookup = {insn.addr: insn for insn in insns}
    addr_buff = [(insns[0].addr, [], None)]

    while len(addr_buff) > 0:
        addr, curr_block, predecessor = addr_buff.pop(-1)

        # In this case, we are falling through into a previous branched-to block.
        # Therefore, we want to convert the current buffer of instructions into a block.
        if addr in blocks:
            if len(curr_block) > 0:
                blk = InstructionBlock(curr_block, predecessor=predecessor)
                blocks[blk.start] = blk

                curr_block = []
                predecessor = blk

            blocks[addr].add_predecessor(predecessor)
            continue

        cont_blk_start = get_block_containing(addr, blocks)

        # In this case, we are branching into the middle of a sequence of instructions we
        # previously thought made up a basic block. Therefore, we want to split said block.
        if cont_blk_start is not None:
            cont_blk = blocks[cont_blk_start]
            new_blk1, new_blk2 = cont_blk.split(addr)

            # In addition to deleting the stale block, we need to unlink it from its predecessors.
            del blocks[cont_blk_start]

            for pred in cont_blk.predecessors:
                pred.remove_successor(cont_blk)
                new_blk1.add_predecessor(pred)

            # Now we also need to transfer the old predecessors to the new first block
            # and the old successors to the new second block. And also add an edge between
            # the two blocks and from the branch predecessor to the second block.
            for succ in cont_blk.successors:
                succ.add_predecessor(new_blk2)

            new_blk2.add_predecessor(predecessor)
            new_blk2.add_predecessor(new_blk1)

            blocks[new_blk1.start] = new_blk1
            blocks[new_blk2.start] = new_blk2

            continue

        insn = None

        if addr in insn_lookup:
            insn = insn_lookup[addr]

        if insn is not None:
            curr_block.append(insn)

        # If the instruction returns or there is some unforseen error, create a block
        # from the current instruction buffer.
        if insn is None or insn.terminates():
            blk = InstructionBlock(curr_block, predecessor=predecessor)
            blocks[blk.start] = blk

            curr_block = []
            predecessor = None

            if insn is not None and not insn.returns():
                predecessor = blk

        # Add the successors to the current instruction to the DFS queue (buffer, whatever).
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
        self.draw()
        exit()

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

    def tojson(self):
        j = {
                'entry': addr_to_str(self.entry.start),
                'blocks': {}
            }

        def convert_block_to_json(blk):
            j['blocks'][addr_to_str(blk.start)] = blk.tojson()

        self.dfs_(self.entry,
                  set(),
                  pre_fn=convert_block_to_json)

        return j

    def insert_phis(self):
        phis_inserted = 0
        visited = set()
        all_varnodes = reduce(lambda x,y: x.union(y),
                              [blk.written_varnodes(ignore_uniq=True) for blk in self.blocks])

        for blk in self.blocks:
            buff = {b for b in self.frontier(blk)} # Don't consume from the frontier!

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
            blk.convert_to_ssa()

        def unwind_version(blk):
            blk.unwind_version()

        self.dom_tree.dfs_(self.entry, 
                           set(), 
                           pre_fn=convert_block_to_ssa, 
                           post_fn=unwind_version)

    def convert_from_ssa(self):
        for block in self.blocks:
            block.convert_from_ssa()

    def simplify(self):
        # TODO: Handle case where blocks may become empty
        self.changed = True

        def simplify_block(blk):
            self.changed |= blk.simplify()

        while self.changed:
            self.changed = False
            self.dfs_(self.entry,
                      set(),
                      post_fn=simplify_block)

    def draw(self):
        g = Digraph(comment='CFG')
        pre_fn = lambda blk: blk.draw_vertex(g) 
        post_fn = lambda blk: blk.draw_edges(g) 
        self.dfs(pre_fn=pre_fn,
                 post_fn=post_fn)
        g.render('cfg', view=True)

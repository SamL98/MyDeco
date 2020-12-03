from functools import reduce

from node import Node
from pcode import PhiOp


class Block(Node):
    def __init__(self, insns, **kwargs):
        super().__init__(**kwargs)
        self.start = insns[0].addr
        self.end = insns[-1].addr
        self.insns = insns

    def __repr__(self):
        return '\n'.join([str(insn) for insn in self.insns])

    def __eq__(self, other):
        if type(other) == Block:
            return self.start == other.start and \
                   self.end == other.end
        elif type(other) == Node:
            return super().__eq__(other)
        else:
            raise NotImplementedError('Block.__eq__ %s' % type(other))

    def __hash__(self):
        return super().__hash__()

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

    def written_varnodes(self, ignore_uniq=False):
        return reduce(lambda x,y: x+y,
                      [insn.written_varnodes(ignore_uniq=ignore_uniq) for insn in self.insns])

    def insert_phis(self, varnodes):
        phis = [PhiOp.fromblock(self, v) for v in varnodes]
        self.insns[0].prepend_pcode(phis)
        return len(phis)

    def simplify(self):
        new_insns = []

        for insn in self.insns:
            insn.simplify()

            if len(insn.pcode) > 0:
                new_insns.append(insn)

        self.insns = new_insns

    def unwind_version(self):
        for insn in self.insns:
            insn.unwind_version()

    def convert_to_ssa(self):
        for insn in self.insns:
            insn.convert_to_ssa()

        for succ in self.successors:
            for phi in succ.insns[0].phis():
                phi.replace_input(self)


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
            blk = Block(curr_block, predecessor=predecessor)
            blocks[blk.start] = blk

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

        if insn is None or insn.ends_block():
            blk = Block(curr_block, predecessor=predecessor)
            blocks[blk.start] = blk

        if insn is not None:
            if insn.fallthrough() is not None:
                if insn.ends_block():
                    addr_buff.append((insn.fallthrough(), [], blk))
                else:
                    addr_buff.append((insn.fallthrough(), curr_block, predecessor))

            if insn.target() is not None:
                addr_buff.append((insn.target(), [], blk))

    if len(curr_block) > 0:
        blk = Block(curr_block, predecessor=predecessor)
        blocks[blk.start] = blk

    return sorted(blocks.values(), key=lambda b: b.start)

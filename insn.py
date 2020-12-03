import math

from functools import reduce


def addr_to_str(addr):
    return '%s.%02d' % (hex(int(math.floor(addr))), (addr - math.floor(addr)) * 100)


class Instruction(object):
    def __init__(self, addr, length, pcode):
        self.addr = addr
        self.length = length
        self.pcode = pcode

    def copy(self):
        return Instruction(self.addr, self.length, self.pcode)

    def __repr__(self):
        addr_str = '%s: ' % addr_to_str(self.addr)
        return '\n'.join([addr_str + str(self.pcode[0])] + [(' ' * len(addr_str)) + str(pcop) for pcop in self.pcode[1:]])

    @staticmethod
    def unserialize(j):
        insn_addr = int(j['addr'], 16)
        insn_len = j['length']

        insns = []
        pcode = []

        for pj in j['pcode']:
            pcop = PcodeOp.unserialize(pj)
            pcode.append(pcop)

            if pcop.branches() or pcop.returns():
                insns.append(Instruction(pcode[0].addr, insn_len * float(len(pcode)) / len(j['pcode']), pcode))
                pcode = []

        if len(pcode) > 0:
            insns.append(Instruction(pcode[0].addr, insn_len * float(len(pcode)) / len(j['pcode']), pcode))

        return insns

    def written_varnodes(self, ignore_uniq=False):
        return reduce(lambda x,y: x+y, 
                      [pcop.written_varnodes(ignore_uniq=ignore_uniq) for pcop in self.pcode])

    def prepend_pcode(self, new_ops):
        self.pcode = new_ops + self.pcode

    def phis(self):
        return [pcop for pcop in self.pcode if pcop.is_phi()]

    def num_phis(self):
        return len(self.phis())

    def fallthrough(self):
        fallthru = None

        if not self.returns():
            fallthru = self.addr + self.length

        return fallthru

    def target(self):
        targ = None

        if self.branches():
            target_vnode = self.pcode[-1].inputs[0]
            if target_vnode.is_ram():
                targ = target_vnode.offset

        return targ

    def returns(self):
        return self.pcode[-1].returns()

    def branches(self):
        return self.pcode[-1].branches()

    def ends_block(self):
        return self.branches() or self.returns()

    def simplify(self, block):
        """
        As a first pass, we go through all of the operations that are equivalent to the identity,
        replace all uses of the rhs with the lhs, and remove said operation.
        """
        new_pcode = []

        for pcop in self.pcode:
            pcop.simplify()

            if not (pcop.has_output() and pcop.is_identity()):
                new_pcode.append(pcop)
                continue

            for use in pcop.output.uses:
                use.pcop.inputs[use.idx] = pcop.inputs[0]

        self.pcode = new_pcode

    def unwind_version(self):
        for pcop in self.pcode:
            pcop.unwind_version()

    def convert_to_ssa(self):
        for pcop in self.pcode:
            pcop.convert_to_ssa()

from pcode import PcodeOp, PcodeList


class Instruction(PcodeList):
    def __init__(self, addr, length, pcode):
        super().__init__(addr, pcode)
        self.length = length

    def copy(self):
        return Instruction(self.addr, self.length, [pcop.copy() for pcop in self.pcode])

    @staticmethod
    def fromjson(j):
        insn_addr = int(j['addr'], 16)
        insn_len = j['length']

        insns = []
        pcode = []

        for pj in j['pcode']:
            pcop = PcodeOp.fromjson(pj)
            pcode.append(pcop)

            if pcop.branches() or pcop.returns():
                insns.append(Instruction(pcode[0].addr, insn_len * float(len(pcode)) / len(j['pcode']), pcode))
                pcode = []

        if len(pcode) > 0:
            insns.append(Instruction(pcode[0].addr, insn_len * float(len(pcode)) / len(j['pcode']), pcode))

        return insns

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

    def is_conditional(self):
        return self.pcode[-1].is_conditional()

    def terminates(self):
        return self.branches() or self.returns()


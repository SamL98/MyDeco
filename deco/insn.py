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

        if not (self.returns() or (self.branches() and not self.is_conditional())):
            fallthru = self.addr + self.length

        return fallthru



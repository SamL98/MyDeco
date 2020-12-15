import math
import pdb
from functools import reduce

from code_elem import CodeElement
from varnode import Varnode, SSAVarnode


class PcodeOp(CodeElement):
    def __init__(self, addr, mnemonic, inputs, output=None):
        self.addr = addr
        self.mnemonic = mnemonic

        if self.is_reorderable() and len(inputs) == 2 and inputs[1].dominates(inputs[0]):
            inputs = [inputs[1], inputs[0]]

        self.inputs = inputs
        self.output = output

    def copy(self):
        return PcodeOp(self.addr, self.mnemonic, self.inputs, output=self.output)

    def __repr__(self):
        op_str = ', '.join([str(v) for v in self.inputs])
        rhs = '%s %s' % (self.mnemonic, op_str)

        if self.output is not None:
            return '%s = %s' % (self.output, rhs)
        else:
            return rhs

    @classmethod
    def fromjson(cls, j):
        inputs = [Varnode.fromjson(ij) for ij in j['inputs']]
        output = None

        if 'output' in j:
            output = Varnode.fromjson(j['output'])

        return cls(j['addr'], j['mnemonic'], inputs, output)

    @classmethod
    def fromstring(cls, s):
        comps = s.split(': ')
        addr = int(comps[0], 16)
        s = comps[1]

        comps = s.split(' = ')
        output = None

        if len(comps) == 2:
            output = Varnode.fromstring(comps[0])
            s = comps[1]

        mnem_idx = s.index(' ')
        mnemonic = s[:mnem_idx]
        inputs = [Varnode.fromstring(comp) for comp in s[mnem_idx+1:].split(', ')]

        return cls(addr, mnemonic, inputs, output)

    def returns(self):
        return 'RETURN' in self.mnemonic

    def branches(self):
        return 'BRANCH' in self.mnemonic

    def terminates(self):
        return self.branches() or self.returns()

    def is_conditional(self):
        return self.mnemonic == 'CBRANCH'

    def is_indirect(self):
        return self.mnemonic.endswith('IND')

    def target(self):
        if self.branches() and self.inputs[0].is_ram():
            return self.inputs[0].offset

    def has_output(self):
        return self.output is not None

    def is_reorderable(self):
        return not (self.mnemonic in ['LOAD', 'STORE', 'MULTIEQUAL'])

    def is_identity(self):
        return self.mnemonic == 'COPY'

    def is_phi(self):
        return False

    def written_varnodes(self, ignore_uniq=False, ignore_pc=True):
        vnodes = []
        if self.output is not None and \
           not (ignore_uniq and self.output.is_unique()) and \
           not (ignore_pc and self.output.is_pc()):
            vnodes.append(self.output)
        return set(vnodes)

    def replace_input(self, idx, new_input):
        self.inputs[idx] = new_input

    def all_inputs_equal(self):
        return all([inpt == self.inputs[0] for inpt in self.inputs])

    def convert_to_identity(self, lhs=None):
        if lhs is None:
            lhs = self.inputs[0]

        self.mnemonic = 'COPY'
        self.inputs = [lhs]

    def convert_to_zero(self, lhs=None):
        if lhs is None:
            lhs = self.inputs[0]

        self.convert_to_identity(Varnode('const', 0, lhs.size))

    def simplify(self):
        if len(self.inputs) < 2:
            return

        if self.inputs[1].is_const():
            if self.inputs[1] == 0:
                if self.mnemonic in ['INT_OR', 'INT_ADD', 'INT_SUB', 'INT_XOR', 'INT_LEFT', 'INT_RIGHT']:
                    self.convert_to_identity()
                elif self.mnemonic in ['INT_AND', 'INT_MULT']:
                    self.convert_to_zero()

            elif self.inputs[1] == 1 and self.mnemonic in ['INT_MULT', 'INT_DIV', 'INT_SDIV']:
                self.convert_to_identity()

        elif self.all_inputs_equal():
            if self.mnemonic in ['INT_AND', 'INT_OR', 'MULTIEQUAL']:
                self.convert_to_identity()
            elif self.mnemonic == 'INT_XOR':
                self.convert_to_zero()

    def unwind_version(self):
        if self.has_output():
            self.output.unwind_version()

    def convert_to_ssa(self):
        inputs = [vnode.convert_to_ssa(self) for vnode in self.inputs]
        output = None

        if self.has_output():
            output = self.output.convert_to_ssa(self, assignment=True)

        self.inputs = inputs
        self.output = output


class PhiOp(PcodeOp):
    def __repr__(self):
        op_strs = []

        for v in self.inputs:
            if isinstance(v, Varnode):
                op_strs.append(str(v))
            else:
                op_strs.append('%s_%s' % (self.output, v.name))

        op_str = ', '.join(op_strs)
        rhs = '%s %s' % (self.mnemonic, op_str)
        return '%s = %s' % (self.output, rhs)

    def is_phi(self):
        return True

    @staticmethod
    def fromblock(blk, v):
        return PhiOp(blk.start, 
                     'MULTIEQUAL', 
                     [p for p in blk.predecessors],
                     v)

    def replace_input(self, predecessor):
        if predecessor in self.inputs:
            idx = self.inputs.index(predecessor)
            vnode = SSAVarnode.get_latest(self.output)

            super().replace_input(idx, vnode)
            vnode.add_use(self, idx=idx)

    def convert_to_ssa(self):
        self.output = self.output.convert_to_ssa(self, assignment=True)


def addr_to_str(addr):
    return '%s.%02d' % (hex(int(math.floor(addr))), (addr - math.floor(addr)) * 100)


class PcodeList(CodeElement):
    def __init__(self, addr, pcode):
        self.addr = addr
        self.pcode = pcode 

    def __repr__(self):
        addr_str = '%s: ' % addr_to_str(self.addr)
        return '\n'.join([addr_str + str(self.pcode[0])] + [(' ' * len(addr_str)) + str(pcop) for pcop in self.pcode[1:]])

    def __len__(self):
        return len(self.pcode)

    def prepend_pcode(self, new_ops):
        self.pcode = new_ops + self.pcode

    def phis(self):
        return [pcop for pcop in self.pcode if pcop.is_phi()]

    def num_phis(self):
        return len(self.phis())

    def written_varnodes(self, ignore_uniq=False, ignore_pc=True):
        return reduce(lambda x,y: x.union(y), 
                      [pcop.written_varnodes(ignore_uniq=ignore_uniq, ignore_pc=ignore_pc) for pcop in self.pcode])

    def returns(self):
        return self.pcode[-1].returns()

    def branches(self):
        return self.pcode[-1].branches()

    def terminates(self):
        return self.pcode[-1].terminates()

    def is_conditional(self):
        return self.pcode[-1].is_conditional()

    def is_indirect(self):
        return self.pcode[-1].is_indirect()

    def target(self):
        return self.pcode[-1].target()

    def simplify(self):
        """
        As a first pass, we go through all of the operations that are equivalent to the identity,
        replace all uses of the rhs with the lhs, and remove said operation.
        """
        changed = True

        # Is this loop needed?
        while changed:
            new_pcode = []

            for pcop in self.pcode:
                pcop.simplify()

                if not (pcop.has_output() and \
                        pcop.is_identity() and \
                        not any([type(use.pcop) == PhiOp for use in pcop.output.uses])):
                    new_pcode.append(pcop)
                    continue

                for use in pcop.output.uses:
                    use.pcop.inputs[use.idx] = pcop.inputs[0]

            changed = len(self.pcode) != len(new_pcode)
            self.pcode = new_pcode

    def unwind_version(self):
        for pcop in self.pcode:
            pcop.unwind_version()

    def convert_to_ssa(self):
        for pcop in self.pcode:
            pcop.convert_to_ssa()

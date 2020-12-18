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

    def __eq__(self, other):
        # TODO: Figure out if this needs to be more "sophisticated".
        return self.addr == other.addr

    @classmethod
    def fromjson(cls, j):
        inputs = [Varnode.fromjson(ij) for ij in j['inputs']]
        output = None

        if 'output' in j:
            output = Varnode.fromjson(j['output'])

        pcop = cls(j['addr'], j['mnemonic'], inputs, output)

        if pcop.is_call():
            pcop = CallOp.frompcop(pcop)

        return pcop

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

        pcop = cls(addr, mnemonic, inputs, output)

        if pcop.is_call():
            pcop = CallOp.frompcop(pcop)

        return pcop

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

    def is_call(self):
        return 'CALL' in self.mnemonic

    def target(self):
        if self.branches() and self.inputs[0].is_ram():
            return self.inputs[0].offset

    def has_output(self):
        return self.output is not None

    def arity(self):
        return len(self.inputs)

    def is_reorderable(self):
        return not (self.mnemonic in ['LOAD', 'STORE', 'MULTIEQUAL'])

    def is_identity(self):
        return self.mnemonic == 'COPY'

    def is_phi(self):
        return False

    def shd_incl_output(self, output, ignore_uniq=False, ignore_pc=True):
        return not (ignore_uniq and output.is_unique()) and \
               not (ignore_pc and output.is_pc())

    def written_varnodes(self, ignore_uniq=False, ignore_pc=True):
        vnodes = set()

        if self.output is not None and \
           self.shd_incl_output(self.output, ignore_uniq, ignore_pc):
            vnodes.add(self.output)

        return vnodes

    def can_be_propagated(self):
        return self.has_output() and self.is_identity() and \
               (self.is_phi() or not any([use.pcop.is_phi() for use in self.output.uses]))

    def is_dead(self):
        return self.has_output() and len(self.output.uses) == 0

    def replace_input(self, idx, new_input):
        self.inputs[idx] = new_input

    def all_inputs_equal(self):
        return all([inpt == self.inputs[0] for inpt in self.inputs])

    def relink_inputs(self, start_idx=1):
        for inpt in self.inputs[start_idx:]:
            inpt.remove_use(self)

    def convert_to_identity(self, lhs=None):
        self.relink_inputs()

        if lhs is None:
            lhs = self.inputs[0]

        self.mnemonic = 'COPY'
        self.inputs = [lhs]

    def convert_to_zero(self, lhs=None):
        self.relink_inputs()

        if lhs is None:
            lhs = self.inputs[0]

        # TODO: Do we need to deal with SSAVarnode's here? Probably
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

    """ Debug Methods """
    def print_with_linkage(self):
        for inpt in self.inputs:
            inpt.print_with_uses()

        print(self)
        print()

        if self.output is not None:
            self.output.print_with_uses()

class CallOp(PcodeOp):
    def __init__(self, addr, mnemonic, inputs, output=None, killed_varnodes=[]):
        super().__init__(addr, mnemonic, inputs, output=output)
        self.killed_varnodes = killed_varnodes

    @staticmethod
    def frompcop(pcop):
        # TODO: Read cspecs to get varnodes killedbycall.
        killed_varnodes = [Varnode('register', off, 8) for off in [0x0, 0x10, 0x1200]]
        return CallOp(pcop.addr, pcop.mnemonic, pcop.inputs, pcop.output, killed_varnodes)

    def written_varnodes(self, ignore_uniq=False, ignore_pc=True):
        vnodes = super().written_varnodes(ignore_uniq, ignore_pc)
        vnodes.update({ v for v in self.killed_varnodes \
                        if self.shd_incl_output(v, ignore_uniq, ignore_pc) })
        return vnodes

    def unwind_version(self):
        super().unwind_version()

        for vnode in self.killed_varnodes:
            vnode.unwind_version()

    def convert_to_ssa(self):
        super().convert_to_ssa()
        ssa_killed_varnodes = []

        for vnode in self.killed_varnodes:
            ssa_killed_varnodes.append(vnode.convert_to_ssa(self, assignment=True))

        self.killed_varnodes = ssa_killed_varnodes


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
        Do some basic arithmetic simplification on the pcop's then
        perform copy propagation on the result.
        """
        changed = True

        #print(addr_to_str(self.start))
        #print(self)
        new_pcode = []

        for pcop in self.pcode:
            pcop.simplify()

            if not (pcop.can_be_propagated() or pcop.is_dead()):
                new_pcode.append(pcop)
                continue

            if pcop.is_dead():
                pcop.relink_inputs(start_idx=0)

            for use in pcop.output.uses:
                prop_vnode = pcop.inputs[0]
                use.pcop.inputs[use.idx] = prop_vnode
                prop_vnode.add_use(use.pcop, idx=use.idx)

        changed = len(self.pcode) != len(new_pcode)
        self.pcode = new_pcode

        return changed

    def unwind_version(self):
        for pcop in self.pcode:
            pcop.unwind_version()

    def convert_to_ssa(self):
        for pcop in self.pcode:
            pcop.convert_to_ssa()

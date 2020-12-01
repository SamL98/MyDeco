from varnode import *


class PcodeOp(object):
    def __init__(self, addr, mnemonic, inputs, output=None):
        self.addr = addr
        self.mnemonic = mnemonic

        if self.is_reorderable() and len(inputs) == 2 and inputs[1].dominates(inputs[0]):
            inputs = [inputs[1], inputs[0]]

        self.inputs = inputs
        self.output = output

    def __repr__(self):
        op_str = ', '.join([str(v) for v in self.inputs])
        rhs = '%s %s' % (self.mnemonic, op_str)

        if self.output is not None:
            return '%s = %s' % (self.output, rhs)
        else:
            return rhs

    @classmethod
    def unserialize(cls, j):
        inputs = [Varnode.unserialize(ij) for ij in j['inputs']]
        output = None

        if 'output' in j:
            output = Varnode.unserialize(j['output'])

        return cls(j['addr'], j['mnemonic'], inputs, output)

    def returns(self):
        return 'RETURN' in self.mnemonic

    def branches(self):
        return 'BRANCH' in self.mnemonic

    def has_output(self):
        return self.output is not None

    def is_reorderable(self):
        return not (self.mnemonic in ['LOAD', 'STORE'])

    def is_identity(self):
        return self.mnemonic == 'COPY'

    def written_varnodes(self, ignore_uniq=False):
        vnodes = []
        if self.output is not None and not (ignore_uniq and self.output.is_unique()):
            vnodes.append(self.output)
        return vnodes

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

    def convert_to_ssa(self):
        inputs = [vnode.convert_to_ssa(self) for vnode in self.inputs]
        
        if pcop.output is not None:
            output = self.output.convert_to_ssa(self, create=True)
        
        self.inputs = inputs
        self.output = output


class PhiOp(PcodeOp):
    def fill_in_input(self, predecessor):
        if predecessor in self.inputs:
            self.replace_input(self.inputs.index(predecessor),
                               predecessor.get_varnode(self.output))

    @staticmethod
    def fromblock(blk, v):
        return PcodeOp(blk.start, 
                       'MULTIEQUAL', 
                       [p for p in blk.predecessors],
                       v)

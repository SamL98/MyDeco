import pdb
from functools import reduce

from code_elem import CodeElement
from exprs import *
from stmts import *
from varnode import Varnode, SSAVarnode
from variable import Variable
from utils import addr_to_str


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
        elif pcop.is_ret():
            pcop = RetOp.frompcop(pcop)

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
        elif pcop.is_ret():
            pcop = RetOp.frompcop(pcop)

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

    def is_ret(self):
        return self.mnemonic == 'RETURN'

    def is_load(self):
        return self.mnemonic == 'LOAD'

    def is_store(self):
        return self.mnemonic == 'STORE'

    def is_phi(self):
        return self.mnemonic == 'MULTIEQUAL'

    def is_identity(self):
        return self.mnemonic == 'COPY'

    def is_assign(self):
        return self.is_store()# or self.is_identity()

    def target(self):
        if self.branches() and self.inputs[0].is_ram():
            return self.inputs[0].offset

    def has_output(self):
        return self.output is not None

    def arity(self):
        return len(self.inputs)

    def is_reorderable(self):
        return not (self.mnemonic in ['LOAD', 'STORE', 'MULTIEQUAL'])

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
        self.convert_to_identity(SSAVarnode('const', 0, lhs.size, None, version=0))

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

    def convert_to_stmts(self):
        stmts = []

        for inpt in self.inputs:
            if inpt.version == 0 and not (inpt.is_const() or inpt.is_ram()):
                # Bad design but the order in which you generate an Expr and a Variable matters because
                # Expr will lookup in the Variable cache as well as its own. Therefore, you most likely want
                # to instantiate an Expr first if creating an AssignStmt.
                expr = Expr.fromvnode(inpt)

                # TODO: Cleanup.
                if isinstance(expr, Expr) and expr not in Variable.CACHE:
                    var = expr.break_out()
                    assign = AssignStmt(self.addr, var, expr)
                    stmts = [assign] + stmts

        if self.is_store():
            space = Expr.fromvnode(self.inputs[0])
            dst = Expr.fromvnode(self.inputs[1])
            data = Expr.fromvnode(self.inputs[2])

            # We need to wrap the operand expressions into an expression
            # representing the STORE because STORE has no output varnode.
            store_expr = NaryExpr('STORE', space, dst, data)
            store_stmt = StoreStmt(self.addr, store_expr)
            stmts.append(store_stmt)

        return stmts


class ABIOp(PcodeOp):
    """
    Pcode operations that require ABI-dependent information (like CALL, RETURN, etc).
    """
    def __init__(self, addr, mnemonic, inputs, output=None, killed_varnodes=[]):
        super().__init__(addr, mnemonic, inputs, output=output)
        self.killed_varnodes = killed_varnodes

    @classmethod
    def frompcop(cls, pcop):
        # TODO: Read cspecs to get varnodes killedbycall.
        killed_varnodes = [Varnode('register', off, 8) for off in [0x0, 0x10, 0x1200]]
        return cls(pcop.addr, pcop.mnemonic, pcop.inputs, pcop.output, killed_varnodes)


class CallOp(ABIOp):
    """
    Because CALL's return values and clobber other varnodes via convention,
    we subclass PcodeOp to keep track of these clobbered (killed) varnodes and
    act like all of them were written by the callee to make SSA valid.
    """
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


class RetOp(ABIOp):
    """
    For the same reasons as we need to have hidden written varnodes for CALL's,
    we need to have hidden read varnodes for RETURN's so that ops that write to return
    varnode locations don't look like dead code.
    """
    def __init__(self, addr, mnemonic, inputs, output=None, killed_varnodes=[]):
        super().__init__(addr, mnemonic, inputs, output, killed_varnodes)

        # This is a bit hacky but since when we convert a varnode to SSA, we check `inputs`
        # to add a use to the definition.
        self.inputs += killed_varnodes

    def convert_to_ssa(self):
        super().convert_to_ssa()

        ssa_killed_varnodes = []
        for vnode in self.killed_varnodes:
            ssa_killed_varnodes.append(vnode.convert_to_ssa(self, assignment=False))

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

    @staticmethod
    def fromblock(blk, v):
        return PhiOp(blk.start, 
                     'MULTIEQUAL', 
                     [p for p in blk.predecessors],
                     v)

    def replace_input(self, *args):
        if all([isinstance(inpt, Varnode) for inpt in self.inputs]):
            super().replace_input(*args)
        else:
            predecessor = args[0]

            if predecessor in self.inputs:
                idx = self.inputs.index(predecessor)
                vnode = SSAVarnode.get_latest(self.output)

                super().replace_input(idx, vnode)
                vnode.add_use(self, idx=idx)

    def convert_to_ssa(self):
        self.output = self.output.convert_to_ssa(self, assignment=True)


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
        new_pcode = []

        for pcop in self.pcode:
            pcop.simplify()

            if not (pcop.can_be_propagated() or pcop.is_dead()):
                new_pcode.append(pcop)
                continue

            if pcop.is_dead():
                pcop.relink_inputs(start_idx=0)

            prop_vnode = pcop.inputs[0]
            pcop.output.propagate_change_to(prop_vnode)

        changed = len(self.pcode) != len(new_pcode)
        self.pcode = new_pcode

        return changed

    def unwind_version(self):
        for pcop in self.pcode:
            pcop.unwind_version()

    def convert_to_ssa(self):
        for pcop in self.pcode:
            pcop.convert_to_ssa()

    def convert_to_stmts(self):
        stmts = []

        for pcop in self.pcode:
            stmts.extend(pcop.convert_to_stmts())

        return stmts

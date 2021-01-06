import pdb
from functools import reduce

from data_flow import DataFlowObj, ExprUse
from variable import Variable

MNEMONIC_TO_OPSTR = {
    'INT_ADD': '+',
    'INT_SUB': '-',
    'INT_LEFT': '<<',
    'INT_RIGHT': '>>',
    'BOOL_NEGATE': '!',
    'BOOL_OR': '||',
    'BOOL_AND': '&&',
    'INT_EQUAL': '==',
    'INT_LESS': '<',
    'INT_SLESS': 's<',
    'LOAD': '*',
    'STORE': '*',
    'COPY': '',
    'MULTIEQUAL': 'phi',
    'INT_ZEXT': 'zext',
    'INT_REM': '%',
    'INT_OR': '|',
    'INT_AND': '&'
}


class Expr(DataFlowObj):
    CACHE = {}

    def use_type(self):
        return ExprUse

    def is_compound(self):
        return False

    def constituents(self):
        return {self}

    def break_out(self):
        # TODO: Overwrite variable if this is its last use.
        var = Variable.fromexpr(self)
        self.propagate_change_to(var)
        return var

    @staticmethod
    def fromvnode(vnode):
        if vnode in Expr.CACHE:
            return Expr.CACHE[vnode]
        elif vnode.is_const():
            return ConstExpr(vnode.offset)
        elif vnode.version == 0 or vnode.defn is None:
            vnode_expr = VarnodeExpr(vnode)

            if vnode_expr in Variable.CACHE:
                return Variable.CACHE[vnode_expr]

            return vnode_expr

        defn = vnode.defn
        arity = defn.arity()
        expr = None

        if defn.is_call() or defn.is_phi() or arity > 2:
            expr = NaryExpr.frompcop(defn)
        elif arity == 1:
            expr = UnaryExpr.frompcop(defn)
        elif arity == 2:
            expr = BinaryExpr.frompcop(defn)
        else:
            raise ValueError('Cannot create expression for 0-arity pcode expression %s' % defn)

        if expr.is_compound():
            Expr.CACHE[vnode] = expr

        return expr


class ConstExpr(Expr):
    def __init__(self, const):
        super().__init__()
        self.const = const

    def __hash__(self):
        return hash(self.const)

    def __eq__(self, other):
        if isinstance(other, int):
            return self.const == other
        elif isinstance(other, ConstExpr):
            return self.const == other.const
        else:
            pdb.set_trace()

    def __repr__(self):
        return hex(self.const)


class VarnodeExpr(Expr):
    def __init__(self, vnode):
        super().__init__()
        self.vnode = vnode

    def __hash__(self):
        return hash(self.vnode)

    def __eq__(self, other):
        return self.vnode == other.vnode

    def __repr__(self):
        return str(self.vnode)


class CompoundExpr(Expr):
    def __init__(self, mnemonic, *inputs):
        super().__init__()
        self.mnemonic = mnemonic
        self.inputs = list(inputs)
        self.opstr = MNEMONIC_TO_OPSTR.get(mnemonic, mnemonic)

        # TODO: Handle multiple inputs that are the same Expr (`idxs` in add_use).
        for i, inpt in enumerate(inputs):
            inpt.add_use(self, idx=i)

        self._parse_inputs()

    def _parse_inputs(self):
        raise NotImplementedError()

    def is_compound(self):
        return True

    def constituents(self):
        return reduce(lambda x,y: x.union(y),
                      [inpt.constituents() for inpt in self.inputs])

    def replace_input(self, idx, new_input):
        self.inputs[idx] = new_input
        self._parse_inputs()

    def bool_not(self):
        if self.mnemonic == 'BOOL_NEGATE':
            return self.hs

        return UnaryExpr('BOOL_NEGATE', self)

    def simplify(self):
        if self.mnemonic == 'BOOL_NEGATE' and self.hs.mnemonic == 'BOOL_NEGATE':
            return self.hs.hs

        return self

    @classmethod
    def frompcop(cls, pcop):
        expr_inputs = [Expr.fromvnode(v) for v in pcop.inputs]

        if pcop.is_identity():
            return expr_inputs[0]

        return cls(pcop.mnemonic, *expr_inputs).simplify()


class UnaryExpr(CompoundExpr):
    def _parse_inputs(self):
        self.hs = self.inputs[0]

    def __repr__(self):
        return '%s(%s)' % (self.opstr, self.hs)


class BinaryExpr(CompoundExpr):
    def _parse_inputs(self):
        self.lhs = self.inputs[0]
        self.rhs = self.inputs[1]

    def __repr__(self):
        if self.mnemonic == 'LOAD':
            return str(UnaryExpr(self.mnemonic, self.rhs))

        return '(%s %s %s)' % (self.lhs, self.opstr, self.rhs)


class NaryExpr(CompoundExpr):
    def _parse_inputs(self):
        pass

    def __repr__(self):
        inputs_str = ', '.join([str(i) for i in self.inputs])
        return '%s(%s)' % (self.opstr, inputs_str)

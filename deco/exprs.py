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

    @staticmethod
    def fromvnode(vnode):
        if vnode in Expr.CACHE:
            return Expr.CACHE[vnode]
        elif vnode in Variable.CACHE:
            expr = Variable.CACHE[vnode]
            Expr.CACHE[vnode] = expr
            return expr

        if vnode.is_const():
            return ConstExpr(vnode.offset)
        elif vnode.version == 0 or vnode.defn is None:
            return VarnodeExpr(vnode)

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

        Expr.CACHE[vnode] = expr
        return expr


class ConstExpr(Expr):
    def __init__(self, const):
        super().__init__()
        self.const = const

    def __repr__(self):
        return hex(self.const)


class VarnodeExpr(Expr):
    def __init__(self, vnode):
        super().__init__()
        self.vnode = vnode

    def __repr__(self):
        return str(self.vnode)


class VariableExpr(Expr):
    def __init__(self, var):
        super().__init__()
        self.var = var

    def __repr__(self):
        return str(self.vnode)


class CompoundExpr(Expr):
    def __init__(self, mnemonic, *inputs):
        super().__init__()
        self.mnemonic = mnemonic
        self.inputs = inputs
        self.opstr = MNEMONIC_TO_OPSTR.get(mnemonic, mnemonic)

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
        return cls(pcop.mnemonic, *expr_inputs).simplify()


class UnaryExpr(CompoundExpr):
    def __init__(self, mnemonic, hs):
        super().__init__(mnemonic, hs)
        self.hs = hs

    def __repr__(self):
        return '%s(%s)' % (self.opstr, self.hs)


class BinaryExpr(CompoundExpr):
    def __init__(self, mnemonic, lhs, rhs):
        super().__init__(mnemonic, lhs, rhs)
        self.lhs = lhs
        self.rhs = rhs

    def __repr__(self):
        if self.mnemonic == 'LOAD':
            return str(UnaryExpr(self.mnemonic, self.rhs))

        return '(%s %s %s)' % (self.lhs, self.opstr, self.rhs)


class NaryExpr(CompoundExpr):
    def __repr__(self):
        if self.mnemonic == 'STORE':
            return '%s(%s) = %s' % (self.opstr, self.inputs[1], self.inputs[2])

        inputs_str = ', '.join([str(i) for i in self.inputs])
        return '%s(%s)' % (self.opstr, inputs_str)

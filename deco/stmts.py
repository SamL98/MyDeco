from exprs import Expr
from node import Node
from utils import addr_to_str


class Stmt(object):
    def __init__(self, addr):
        self.addr = addr

    def __repr__(self):
        return '%s: STMT' % addr_to_str(self.addr)


class AssignStmt(Stmt):
    def __init__(self, addr, var, expr):
        super().__init__(addr)
        self.var = var
        self.expr = expr
        self.expr.defn = self

    def __repr__(self):
        return '%s = %s' % (self.var, self.expr)


class ExprStmt(Stmt):
    """
    Basically an address-tied expression.
    An expression pulled out of the aether and into the program.

    NOTE: We're assuming that the wrapped expression is a compound expression.
    """
    def __init__(self, addr, expr):
        super().__init__(addr)
        self.expr = expr
        self.expr.defn = self

    def __repr__(self):
        return str(self.expr)

    def replace_input(self, idx, new_input):
        self.expr.inputs[idx] = new_input


class StoreStmt(ExprStmt):
    def __repr__(self):
        return '*(%s) = %s' % (self.expr.inputs[1], self.expr.inputs[2])


class IfStmt(Stmt):
    def __init__(self, addr, condition, target):
        super().__init__(addr)
        self.condition = condition
        self.condition.defn = self
        self.target = target

    def __repr__(self):
        lines = ['IF (%s) THEN' % self.condition]
        lines += ['\t' + line for line in str(self.target).split('\n')]
        lines += ['END']
        return '\n'.join(lines)

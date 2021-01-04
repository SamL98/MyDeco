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

    def __repr__(self):
        return '%s = %s' % (self.var, self.expr)


class StoreStmt(Stmt):
    def __init__(self, addr, dst, data):
        super().__init__(addr)
        self.dst = dst
        self.data = data

    def __repr__(self):
        return '*(%s) = %s' % (self.dst, self.data)


class CallStmt(Stmt):
    def __init__(self, addr, *params):
        super().__init__(addr)
        self.params = params


class IfStmt(Stmt):
    def __init__(self, addr, condition, target):
        super().__init__(addr)
        self.condition = condition
        self.target = target

    def __repr__(self):
        lines = ['IF (%s) THEN' % self.condition]
        lines += ['\t' + line for line in str(self.target).split('\n')]
        lines += ['END']
        return '\n'.join(lines)

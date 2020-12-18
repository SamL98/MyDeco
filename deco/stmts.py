from exprs import Expr
from node import Node
from pcode import addr_to_str


class Stmt(Node):
    def __init__(self, block, **kwargs):
        super().__init__(**kwargs)
        self.start = block.start
        self.block = block

    def __repr__(self):
        return '%s: STMT' % addr_to_str(self.start)


class IfStmt(Stmt):
    def __init__(self, predicate, action, fallthrough, invert=False, **kwargs):
        super().__init__(predicate, **kwargs)

        self.condition = Expr.fromvnode(predicate.block.pcode[-1].inputs[1])

        if invert:
            self.condition = not self.condition

        self.predicate = predicate
        self.action = action
        self.fallthrough = fallthrough

    def __repr__(self):
        lines = ['IF (%s) THEN' % self.condition]
        lines += ['\t' + line for line in str(self.action).split('\n')]
        lines += ['END']
        lines += str(self.fallthrough).split('\n')
        return '\n'.join(lines)

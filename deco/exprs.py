class Expr(object):
    @staticmethod
    def fromvnode(vnode):
        if vnode.version == 0 or vnode.defn is None:
            return VarnodeExpr(vnode)

        defn = vnode.defn
        arity = defn.arity()

        if arity == 1:
            return UnaryExpr(defn)
        elif arity == 2:
            return BinaryExpr(defn)
        elif arity == 3:
            return TernaryExpr(defn)
        elif arity > 0:
            return NaryExpr(defn)
        else:
            raise ValueError('Cannot create expression for 0-arity pcode expression %s' % defn)


class VarnodeExpr(Expr):
    def __init__(self, vnode):
        self.vnode = vnode

    def __repr__(self):
        return str(self.vnode)


class PcodeExpr(Expr):
    def __init__(self, pcop):
        self.mnemonic = pcop.mnemonic
        self.inputs = [Expr.fromvnode(v) for v in pcop.inputs]
        self.output = None

        if pcop.output is not None:
            self.output = Expr.fromvnode(pcop.output)


class UnaryExpr(PcodeExpr):
    def __repr__(self):
        pass

class BinaryExpr(PcodeExpr):
    def __repr__(self):
        pass

class TernaryExpr(PcodeExpr):
    def __repr__(self):
        pass

class NaryExpr(PcodeExpr):
    def __repr__(self):
        pass

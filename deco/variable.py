class Variable(object):
    CACHE = {}

    def __init__(self, name, vnode):
        self.name = name
        self.vnode = vnode

    def __repr__(self):
        return self.name

    @staticmethod
    def get_name():
        return 'v%d' % len(Variable.CACHE)

    @staticmethod
    def fromvnode(vnode):
        if vnode in Variable.CACHE:
            return Variable.CACHE[vnode]

        name = Variable.get_name()
        var = Variable(name, vnode)

        Variable.CACHE[vnode] = var
        return var

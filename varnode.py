from collections import defaultdict, namedtuple

Use = namedtuple('Use', ('pcop', 'idx'))


class Varnode(object):
    def __init__(self, space, offset, size):
        self.space = space
        self.offset = offset
        self.size = size

    def __repr__(self):
        if self.space == 'const':
            return '%s:%d' % (hex(self.offset), self.size)
        elif self.space == 'unique':
            return 'U%x:%d' % (self.offset, self.size)
        else:
            return '[%s]%s:%d' % (self.space, hex(self.offset), self.size)

    def __hash__(self):
        return hash((self.space, self.offset, self.size))

    def __eq__(self, other):
        if isinstance(other, int):
            return self.offset == other
        elif isinstance(other, Varnode):
            return self.space == other.space and \
                   self.offset == other.offset and \
                   self.size == other.size
        else:
            raise TypeError(type(other))

    @classmethod
    def unserialize(cls, j):
        return cls(j['space'], int(j['offset'], 16), int(j['size'], 16))

    def is_ram(self):
        return self.space == 'ram'

    def is_unique(self):
        return self.space == 'unique'

    def is_const(self):
        return self.space == 'const'

    def dominates(self, other):
        return other.is_const()

    @staticmethod
    def convert_to_ssa(vnode, curr_pcop, create=False):
        ssa_vnode = None

        if not create and hash(vnode) in SSAVarnode.EXISTING_VARNODES:
            ssa_vnode = SSAVarnode.EXISTING_VARNODES[hash(vnode)]
            ssa_vnode.add_use(curr_pcop)

        else:
            ssa_vnode = SSAVarnode(vnode.space, vnode.offset, vnode.size, curr_pcop)

        return ssa_vnode


class SSAVarnode(Varnode):
    VERSION_LOOKUP = defaultdict(int)

    def __init__(self, space, offset, size, defn):
        super().__init__(space, offset, size)
        SSAVarnode.EXISTING_VARNODES[hash(self)] = self

        self.version = SSAVarnode.get_version(self)
        self.defn = defn
        self.uses = []

    def add_use(self, pcop):
        use = Use(pcop, pcop.inputs.index(self))
        self.uses.append(use)

    def __repr__(self):
        return '%s (%d)' % (super().__repr__(), self.version)

    @staticmethod
    def get_version(vnode):
        ver = SSAVarnode.VERSION_LOOKUP[hash(vnode)]
        SSAVarnode.VERSION_LOOKUP[hash(vnode)] += 1
        return ver


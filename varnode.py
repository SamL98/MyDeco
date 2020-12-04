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
            # We can't just raise an exception because we'll be comparing Varnodes
            # to Blocks in partially-filled-in PhiOp's.
            #raise TypeError(type(other))
            return False

    @classmethod
    def unserialize(cls, j):
        return cls(j['space'], int(j['offset'], 16), int(j['size'], 16))

    @classmethod
    def fromstring(cls, s):
        space = 'const'

        if s.startswith('U'):
            space = 'unique'
            s = s.strip('U')
        elif s.startswith('['):
            space_idx = s.index(']')
            space = s[1:space_idx]
            s = s[space_idx+1:]

        comps = s.split(':')
        offset = int(comps[0], 16)
        size = int(comps[1])

        return cls(space, offset, size)

    def is_ram(self):
        return self.space == 'ram'

    def is_unique(self):
        return self.space == 'unique'

    def is_const(self):
        return self.space == 'const'

    def dominates(self, other):
        return other.is_const()

    def convert_to_ssa(self, curr_pcop, assignment=False):
        ssa_vnode = SSAVarnode.get_latest(self)

        if not assignment and ssa_vnode is not None:
            ssa_vnode.add_use(curr_pcop)
        else:
            ssa_vnode = SSAVarnode(self.space, self.offset, self.size, curr_pcop)

        return ssa_vnode


class SSAVarnode(Varnode):
    VERSION_LOOKUP = defaultdict(int)
    EXISTING_VARNODES = defaultdict(list)

    def __init__(self, space, offset, size, defn):
        super().__init__(space, offset, size)
        SSAVarnode.EXISTING_VARNODES[hash(self)].append(self)

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

    @staticmethod
    def get_latest(vnode):
        if hash(vnode) in SSAVarnode.EXISTING_VARNODES:
            vnodes = SSAVarnode.EXISTING_VARNODES[hash(vnode)]
            if len(vnodes) > 0:
                return vnodes[-1]

        return None

    def unwind_version(self):
        if hash(self) in SSAVarnode.EXISTING_VARNODES:
            vnodes = SSAVarnode.EXISTING_VARNODES[hash(self)]
            if len(vnodes) > 0:
                vnodes.pop(-1)


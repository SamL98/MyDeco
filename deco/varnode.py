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
    def fromjson(cls, j):
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

    def is_register(self):
        return self.space == 'register'

    def is_const(self):
        return self.space == 'const'

    def dominates(self, other):
        return other.is_const()

    def is_pc(self):
        # TODO: Make nice (and arch-inderpendent).
        return self.is_register() and self.offset == 0x288

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

    def __init__(self, space, offset, size, defn, version=None):
        super().__init__(space, offset, size)
        SSAVarnode.EXISTING_VARNODES[hash(self)].append(self)

        if version is None:
            self.version = SSAVarnode.get_version(self)

        self.defn = defn
        self.uses = []

    def __eq__(self, other):
        super_eq = super().__eq__(other)

        if type(other) == SSAVarnode:
            super_eq = super_eq and self.version == other.version

        return super_eq

    def __hash__(self):
        return super().__hash__()

    def add_use(self, pcop, idx=None):
        if idx is None:
            idx = pcop.inputs.index(self)

        use = Use(pcop, idx)
        self.uses.append(use)

    def get_use_idx(self, pcop):
        idx = -1

        for i, use in enumerate(self.uses):
            if use.pcop == pcop:
                idx = i
                break

        return idx

    def update_use(self, pcop):
        idx = self.get_use_idx(pcop)

        if idx >= 0:
            self.uses[idx] = Use(pcop, pcop.inputs.index(self))

    def remove_use(self, pcop):
        idx = self.get_use_idx(pcop)

        if idx >= 0:
            del self.uses[idx]

    def __repr__(self):
        return '%s (%d)' % (super().__repr__(), self.version)

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

        size_str, ver_str = comps[1].split(' ')
        size = int(size_str)
        version = int(ver_str.strip('()'))

        vnode = Varnode(space, offset, size)
        latest = SSAVarnode.get_latest(vnode)

        if latest is not None and latest.version == version:
            return latest

        return cls(space, offset, size, None, version=version)

    @staticmethod
    def get_version(vnode):
        ver = SSAVarnode.VERSION_LOOKUP[hash(vnode)]
        SSAVarnode.VERSION_LOOKUP[hash(vnode)] += 1
        return ver

    @staticmethod
    def get_latest(vnode):
        ssa_vnode = None

        if hash(vnode) in SSAVarnode.EXISTING_VARNODES:
            ssa_vnodes = SSAVarnode.EXISTING_VARNODES[hash(vnode)]
            if len(ssa_vnodes) > 0:
                ssa_vnode = ssa_vnodes[-1]

        # TODO: Figure out if we should create the varnode in all cases.
        #       We definitely want to sometimes if the varnode is a parameter for example.
        if ssa_vnode is None:
            ssa_vnode = SSAVarnode(vnode.space, vnode.offset, vnode.size, None)

        return ssa_vnode

    def unwind_version(self):
        if hash(self) in SSAVarnode.EXISTING_VARNODES:
            vnodes = SSAVarnode.EXISTING_VARNODES[hash(self)]
            if len(vnodes) > 0:
                vnodes.pop(-1)

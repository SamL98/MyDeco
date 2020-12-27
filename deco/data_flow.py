class Use(object):
    def __init__(self, user, idxs):
        self.user = user
        self.idxs = idxs


class VarnodeUse(Use):
    def __init__(self, pcop, idxs):
        super().__init__(pcop, idxs)
        self.pcop = pcop


class ExprUse(Use):
    def __init__(self, expr, idxs):
        super().__init__(expr, idxs)
        self.expr = expr


class DataFlowObj(object):
    def __init__(self, defn=None):
        self.defn = defn
        self.uses = []

    def use_type(self):
        raise NotImplementedError()

    def get_input_idxs(self, user):
        return [i for i, v in enumerate(user.inputs) if v == self]

    def add_use(self, user, idx=None, idxs=[]):
        if len(idxs) == 0 and idx is None:
            idxs = self.get_input_idxs(user)
        elif idx is not None:
            idxs = [idx]

        use = self.use_type()(user, idxs)
        self.uses.append(use)

    def get_use_idx(self, user):
        idx = -1

        for i, use in enumerate(self.uses):
            if use.user == user:
                idx = i
                break

        return idx

    def update_use(self, user):
        idx = self.get_use_idx(user)

        if idx >= 0:
            self.uses[idx] = self.use_type()(user, self.get_input_idxs(user))

    def remove_use(self, user):
        idx = self.get_use_idx(user)

        if idx >= 0:
            del self.uses[idx]


from functools import reduce

from cfg import CFG


class Function(object):
    def __init__(self, cfg):
        self.cfg = cfg
        self.cfg.convert_to_ssa()

    def __repr__(self):
        return str(self.cfg)

    @staticmethod
    def fromjson(j):
        cfg = CFG.fromjson(j)
        return Function(cfg)

    def simplify(self):
        #self.cfg = self.cfg.simplify()
        self.cfg.simplify()

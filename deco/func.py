from functools import reduce

from cfg import CFG
from hlcfg import HLCFG


class Function(object):
    def __init__(self, cfg):
        self.cfg = cfg
        self.cfg.convert_to_ssa()
        self.cfg.simplify()

        self.ast = HLCFG.fromcfg(self.cfg)
        print(self.ast)

    def __repr__(self):
        return str(self.cfg)

    @staticmethod
    def fromjson(j):
        cfg = CFG.fromjson(j)
        return Function(cfg)

    def draw(self):
        self.cfg.draw()

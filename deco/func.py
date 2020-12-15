from functools import reduce

from stmts.ast import AST
from cfg import CFG


class Function(object):
    def __init__(self, cfg):
        self.cfg = cfg
        self.cfg.convert_to_ssa()
        self.cfg.simplify()

        #self.ast = AST.fromcfg(self.cfg)

    def __repr__(self):
        return str(self.cfg)

    @staticmethod
    def fromjson(j):
        cfg = CFG.fromjson(j)
        return Function(cfg)

    def draw(self):
        self.cfg.draw()

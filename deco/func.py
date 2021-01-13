from functools import reduce

from cfg import CFG
from stmt_list import MyAST


class Function(object):
    def __init__(self, cfg):
        self.cfg = cfg
        self.cfg.convert_to_ssa()
        self.cfg.simplify()
        #print(self.cfg)

        #self.ast = MyAST.fromcfg(self.cfg)
        #self.ast.simplify()
        #print(self.ast)
        self.ast = MyAST(None, [])

    def __repr__(self):
        return str(self.cfg)

    @staticmethod
    def fromjson(j):
        cfg = CFG.fromjson(j)
        return Function(cfg)

    def tojson(self):
        cfg_j = self.cfg.tojson()
        ast_j = self.ast.tojson()
        return {'cfg': cfg_j, 'ast': ast_j}

    def draw(self):
        self.cfg.draw()

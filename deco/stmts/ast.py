from graph import Graph


class AST(Graph):
    def __init__(self, stmts):
        self.stmts = stmts

    @staticmethod
    def fromcfg(self, cfg):
        stmts = []

        cfg.dfs(pre_fn=pre_fn, 
                post_fn=post_fn)

        return AST(stmts)


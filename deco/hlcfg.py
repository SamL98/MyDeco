from graph import Graph
from stmts import Stmt, IfStmt


class HLCFG(Graph):
    """
    I initially wanted to call this class AST but pdb overwrote it since it's part of a
    standard Python package. Therefore, here we are with High-Level CFG (HLCFG).
    """
    def __init__(self, entry, stmts):
        super().__init__(stmts)
        self.entry = entry
        self.stmts = stmts

    def __repr__(self):
        """
        We want to start by printing the statement containing the entry block.
        Then we can print each statement as we traverse the graph.
        """
        return str(self.entry)

    @staticmethod
    def fromcfg(cfg):
        blk2stmt = {}
        stmts = []

        def wrap_block(blk):
            stmts.append(Stmt(blk))
            blk2stmt[blk] = stmts[-1]

        def label_block(blk):
            """
            From the CFG, group the blocks into higher-level control structures.
            e.g. For a block that CBRANCH's, take the two successors and if one is in the
                 dominance frontier of the other, the former is the if's child and the condition
                 should be inverted accordingly (if it isn't the actual branch target).
            """
            stmt = None

            if blk.branches() and blk.is_conditional():
                tgt, ft = blk.target(), blk.fallthrough()
                invert = False

                if tgt in cfg.frontier(ft):
                    tgt, ft = ft, tgt
                    invert = True

                predicate = blk2stmt[blk]
                action = blk2stmt[tgt]
                fallthru = blk2stmt[ft]

                stmt = IfStmt(predicate, action, fallthru, invert=invert)
                blk2stmt[predicate.block] = stmt
                fallthru.add_predecessor(stmt)

            if stmt is not None:
                stmts.append(stmt)

        cfg.dfs(pre_fn=wrap_block,
                post_fn=label_block)

        entry = blk2stmt[cfg.entry]
        return HLCFG(entry, stmts)


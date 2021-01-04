from functools import reduce

from blocks import Block
from exprs import Expr
from graph import Graph
from stmts import *
from variable import Variable


class StmtBlock(Block):
    def __init__(self, stmts, addr=None, **kwargs):
        if addr is None:
            addr = stmts[0].addr
        super().__init__(addr, stmts, **kwargs)
        self.stmts = stmts

    def __repr__(self):
        return '\n'.join([str(blk) for blk in self.stmts])


class StmtBlockList(object):
    def __init__(self, blocks):
        self.blocks = blocks

    def __repr__(self):
        return '\n'.join([str(blk) for blk in self.blocks])

    @staticmethod
    def fromcfg(cfg):
        blk2ast = {}

        def preprocess_block(blk):
            stmts = sorted(blk.convert_to_stmts(), key=lambda s: s.addr)
            stmt_block = StmtBlock(stmts, addr=blk.start)

            ast = StmtBlockList([stmt_block])
            blk2ast[blk] = ast

        def postprocess_block(blk):
            ast = blk2ast[blk]

            if blk.branches() and blk.is_conditional():
                pcop = blk.pcode[-1]

                condition = Expr.fromvnode(pcop.inputs[1])
                tgt, ft = blk.target(), blk.fallthrough()

                if tgt in cfg.frontier(ft):
                    condition = condition.bool_not()
                    tgt, ft = ft, tgt

                # Pop the statement block from the current AST and put it into its own AST.
                tgt_ast = blk2ast[tgt]
                del blk2ast[tgt]

                if_stmt = IfStmt(pcop.addr, condition, tgt_ast)
                ast.blocks[0].stmts.append(if_stmt)

                # Then accumulate the if's AST with the fallthrough and pop the fallthrough's AST.
                ft_ast = blk2ast[ft]
                del blk2ast[ft]

                ast.blocks.extend(ft_ast.blocks)

        cfg.dfs_(cfg.entry,
                 set(),
                 pre_fn=preprocess_block,
                 post_fn=postprocess_block)

        return blk2ast[cfg.entry]


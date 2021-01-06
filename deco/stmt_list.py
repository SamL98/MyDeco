import pdb
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

        # FIXME
        if len(stmts) > 0:
            self.end = stmts[-1].addr
        else:
            self.end = self.start

    def __repr__(self):
        return '\n'.join([str(blk) for blk in self.stmts])

    def add_stmt(self, stmt):
        self.stmts.append(stmt)
        self.end = self.stmts[-1].addr

    def get_insert_idx(self, addr):
        for i, stmt in enumerate(self.stmts):
            if addr <= stmt.addr:
                return i
        return i


class StmtBlockList(object):
    def __init__(self, blocks):
        self.blocks = blocks

    def __repr__(self):
        return '\n'.join([str(blk) for blk in self.blocks])


class MyAST(object):
    def __init__(self, entry, asts):
        self.entry = entry
        self.asts = asts

    def __repr__(self):
        return str(self.entry)

    def block_containing(self, addr):
        for ast in self.asts:
            for blk in ast.blocks:
                if blk.start <= addr and addr < blk.end:
                    return blk
        pdb.set_trace()

    def _percolate_assignment(self, assign):

    def simplify(self):
        for expr in Expr.CACHE.values():
            if len(expr.uses) >= 2:
                var = expr.break_out()

                constituents = {c for c in expr.constituents() if c.defn is not None}

                if len(constituents) == 0:
                    blk = self.entry.blocks[0]
                    assign = AssignStmt(blk.start, var, expr)
                    blk.stmts = [assign] + blk.stmts
                else:
                    insert_addr = max([c.defn.addr for c in constituents]) + 1 # poor form

                    blk = self.block_containing(insert_addr)
                    insert_idx = blk.get_insert_idx(insert_addr)

                    assign = AssignStmt(insert_addr, var, expr)
                    blk.stmts.insert(insert_idx, assign)

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
                #del blk2ast[tgt]

                if_stmt = IfStmt(pcop.addr, condition, tgt_ast)
                ast.blocks[0].add_stmt(if_stmt)

                # Then accumulate the if's AST with the fallthrough and pop the fallthrough's AST.
                ft_ast = blk2ast[ft]
                del blk2ast[ft]

                ast.blocks.extend(ft_ast.blocks)

        cfg.dfs_(cfg.entry,
                 set(),
                 pre_fn=preprocess_block,
                 post_fn=postprocess_block)

        return MyAST(blk2ast[cfg.entry], blk2ast.values())


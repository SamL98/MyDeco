from functools import reduce

from graph import Graph


class CFG(Graph):
    def __init__(self, blocks):
        super().__init__(blocks)

        self.sort_by_postorder()
        self.generate_dom_tree()
        self.generate_dom_frontiers()

        self.blocks = self.nodes
        self.entry = self.start

    def insert_phis(self):
        phis_inserted = 0
        visited = set()
        all_varnodes = reduce(lambda x,y: x+y,
                              [blk.written_varnodes(ignore_uniq=True) for blk in self.blocks])

        for blk in self.blocks:
            buff = self.frontier(blk)

            while len(buff) > 0:
                df_blk = buff.pop()
        
                if df_blk in visited:
                    continue

                phis_inserted += df_blk.insert_phis(all_varnodes)

                visited.add(df_blk)
                buff.update(self.frontier(df_blk))

        return phis_inserted

    def convert_to_ssa(self):
        self.insert_phis()

        def convert_block_to_ssa(blk):
            blk.convert_to_ssa()

        def unwind_version(blk):
            blk.unwind_version()

        self.dom_tree.dfs_(self.entry, 
                           set(), 
                           pre_fn=convert_block_to_ssa, 
                           post_fn=unwind_version)

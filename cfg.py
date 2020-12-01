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
        visited = set()
        all_varnodes = reduce(lambda x,y: x+y,
                              [blk.written_varnodes(ignore_uniq=True) for blk in self.blocks])

        for blk in self.blocks:
            buff = self.frontier(blk)

            while len(buff) > 0:
                df_blk = buff.pop(0)
        
                if df_blk in visited:
                    continue

                df_blk.insert_phis(all_varnodes)

                visited.add(df_blk)
                buff.extend(self.frontier(df_blk))

    def convert_to_ssa(self):
        pass

from varnode import Varnode


class ABI(object):
    def __init__(self, input_locs, output_locs, killed_locs):
        self.input_locs = input_locs
        self.output_locs = output_locs
        self.killed_locs = killed_locs

    def input_loc(self, idx, dt=None):
        if idx >= len(self.input_locs):
            return None

        return self.input_locs[idx]

    def output_loc(self, idx, dt=None):
        if idx >= len(self.output_locs):
            return None

        return self.output_locs[idx]


class x64_ABI(ABI):
    def input_loc(self, idx, dt=None):
        if idx >= len(self.input_locs):
            stack_off = 8 * (idx - len(self.input_locs))
            return Varnode()
        else:
            return super().input_loc(idx, dt)


# TODO: Arch-independent, obviously.
abi = x64_ABI(

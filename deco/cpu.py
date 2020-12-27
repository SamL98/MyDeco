from varnode import Varnode


class CPU(object):
    def __init__(self, registers):
        self.registers = registers

cpu = CPU({
    Varnode.reg(0, 8): 'RAX',
    Varnode.reg(0, 4): 'EAX',
})

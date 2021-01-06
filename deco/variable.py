from data_flow import DataFlowObj, ExprUse


class Variable(DataFlowObj):
    # TODO: Make Variable a subclass of Expr.
    CACHE = {}

    def __init__(self, value, name=None):
        super().__init__()

        if name is None:
            name = Variable.get_name()

        self.name = name
        self.value = value

        Variable.CACHE[value] = self

    def __repr__(self):
        return self.name

    def use_type(self):
        return ExprUse

    def is_compound(self):
        return False

    def constituents(self):
        return self.value.constituents()

    @staticmethod
    def get_name():
        return 'v%d' % len(Variable.CACHE)

    @staticmethod
    def fromexpr(expr, name=None):
        return Variable(expr, name=name)

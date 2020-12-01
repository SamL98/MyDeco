import json
import math
import sys

from collections import defaultdict
from functools import reduce
from os.path import join

from func import Function


if __name__ == '__main__':
    func_name = sys.argv[1]

    with open(join('funcs', '%s.json' % func_name)) as f:
        func_j = json.load(f)

    func = Function.unserialize(func_j)
    #func.simplify()
    #print(func)


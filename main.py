import sys
sys.path.insert(0, 'deco')

import json
import math

from collections import defaultdict
from functools import reduce
from os.path import join

from func import Function


if __name__ == '__main__':
    func_name = sys.argv[1]

    with open(join('funcs', '%s.json' % func_name)) as f:
        func_j = json.load(f)

    func = Function.fromjson(func_j)
    #print(func.tojson())
    print(func)
    #func.draw()


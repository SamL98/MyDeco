import json

pcode_j = []

def serialize_varnode(v):
    return {
        'space': v.getAddress().addressSpace.name,
        'offset': hex(v.offset).strip('L'),
        'size': hex(v.size).strip('L')
    }

func = getFunctionContaining(currentAddress)
insn = getInstructionAt(func.entryPoint)

while insn is not None and getFunctionContaining(insn.address) == func:
    insn_j = {
        'addr': hex(insn.address.offset).strip('L'),
        'length': insn.length,
        'pcode': []
    }

    for pcop in insn.pcode:
        pcop_j = {
            'addr': float(insn.address.offset) + insn.length * float(pcop.seqnum.time) / float(len(insn.pcode)),
            'mnemonic': pcop.mnemonic,
            'inputs': []
        }

        for inpt in pcop.inputs:
            pcop_j['inputs'].append(serialize_varnode(inpt))

        if pcop.output is not None:
            pcop_j['output'] = serialize_varnode(pcop.output)

        insn_j['pcode'].append(pcop_j)

    pcode_j.append(insn_j)
    insn = insn.next

with open('/Users/samlerner/Projects/mydeco/funcs/%s.json' % func.name, 'w') as f:
    json.dump(pcode_j, f, indent=True)

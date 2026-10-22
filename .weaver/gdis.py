"""Disassemble main.elf at a vaddr: python .weaver/gdis.py 0xc686fc [count]"""
import sys
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
args=[a for a in sys.argv[1:] if not a.startswith('--')]
elf='work/elf/main.elf'
addr=int(args[0],0); n=int(args[1]) if len(args)>1 else 12
f=ELFFile(open(elf,'rb'))
md=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
for s in f.iter_segments():
    if s['p_type']=='PT_LOAD' and s['p_vaddr']<=addr<s['p_vaddr']+s['p_filesz']:
        off=s['p_offset']+addr-s['p_vaddr']
        f.stream.seek(off); data=f.stream.read(n*4)
        for i in md.disasm(data,addr): print('%x: %s %s'%(i.address,i.mnemonic,i.op_str))
        break

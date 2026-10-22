"""plt_sym.py <elf> <got_slot_addr_hex|plt_stub_hex> ...  : name the relocation/symbol of a GOT slot (JUMP_SLOT) or PLT stub (lazy-bound call target).
Uses work/elf/<mod>.elf (pyelftools). The addresses are module offsets (not absolute)."""
import sys
from elftools.elf.elffile import ELFFile
e = ELFFile(open(sys.argv[1], 'rb'))
dyn = e.get_section_by_name('.dynsym')
rels = {}
for secname in ('.rela.plt', '.rela.dyn'):
    s = e.get_section_by_name(secname)
    if not s: continue
    for r in s.iter_relocations():
        rels.setdefault(r['r_offset'], (secname, r))
def img_read(off, n):
    for seg in e.iter_segments():
        if seg['p_type'] == 'PT_LOAD' and seg['p_vaddr'] <= off < seg['p_vaddr'] + seg['p_filesz']:
            return seg.data()[off - seg['p_vaddr']: off - seg['p_vaddr'] + n]
    return b''
import struct
for a in sys.argv[2:]:
    a = int(a, 0)
    if a not in rels:
        # maybe a PLT stub: decode adrp/ldr/add
        w = struct.unpack('<4I', img_read(a, 16))
        if (w[0] & 0x9f000000) == 0x90000000:
            imm = ((w[0] >> 29) & 3) | (((w[0] >> 5) & 0x7ffff) << 2)
            if imm & 0x100000: imm -= 0x200000
            page = ((a & ~0xfff) + (imm << 12))
            off = ((w[1] >> 10) & 0xfff) << 3
            a = page + off
    r = rels.get(a)
    if not r: print(hex(a), 'no relocation'); continue
    sec, rel = r
    sym = dyn.get_symbol(rel['r_info_sym']) if rel['r_info_sym'] else None
    print(hex(a), sec, 'type', rel['r_info_type'], 'sym', sym.name if sym else None, 'shndx', sym['st_shndx'] if sym else None, 'addend', hex(rel['r_addend']))

"""Facts about the NSOs the runtime needs: layout, dynamic tags, init/fini arrays, relocation types (TLS), imports and who
defines them, well-known entry symbols.   python .weaver/modfacts.py [--imports-out DIR]   (run with tools .venv python, cwd recomp/)"""
import sys, struct, collections, os
sys.path.insert(0, '.')
from nxrecomp import program, nso
mods = [('rtld', 0x7000000000, None), ('main', 0x7100000000, 0), ('sdk', 0x7500000000, 1), ('subsdk0', 0x7600000000, 2)]
outdir = sys.argv[sys.argv.index('--imports-out') + 1] if '--imports-out' in sys.argv else None
DT = {1: 'NEEDED', 2: 'PLTRELSZ', 3: 'PLTGOT', 4: 'HASH', 5: 'STRTAB', 6: 'SYMTAB', 7: 'RELA', 8: 'RELASZ', 9: 'RELAENT', 10: 'STRSZ', 11: 'SYMENT',
      12: 'INIT', 13: 'FINI', 14: 'SONAME', 20: 'PLTREL', 23: 'JMPREL', 25: 'INIT_ARRAY', 26: 'FINI_ARRAY', 27: 'INIT_ARRAYSZ', 28: 'FINI_ARRAYSZ',
      32: 'PREINIT_ARRAY', 33: 'PREINIT_ARRAYSZ', 0x6ffffef5: 'GNU_HASH', 0x6ffffff9: 'RELACOUNT'}
RT = {257: 'ABS64', 1025: 'GLOB_DAT', 1026: 'JUMP_SLOT', 1027: 'RELATIVE', 1028: 'TLS_DTPMOD', 1029: 'TLS_DTPREL', 1030: 'TLS_TPREL', 1031: 'TLSDESC', 1032: 'IRELATIVE'}
WELL = ['nnMain', 'nninitStartup', 'nnMain', 'main', '_start', '_init', '_fini', '__nnmusl_init_dso_handle', 'exit', 'abort', '__cxa_atexit',
        '__tls_get_addr', '__nn_', '_ZN2nn2os6detail']
defs, undefs, imgs = {}, {}, {}
for name, base, idx in mods:
    d = open('../game/exefs/' + name, 'rb').read()
    info = nso.nso_info(d)
    from nxrecomp.image import Image
    img = Image.from_nso(d, base, name)
    imgs[name] = img
    print('=== %s  base 0x%x  build-id %s' % (name, base, info['build_id']))
    print('  segments: ' + '; '.join('%s vaddr 0x%x size 0x%x' % (('text', 'ro', 'data')[i], s['vaddr'], len(s['data'])) for i, s in enumerate(info['segments']))
          + '; bss 0x%x (starts 0x%x)' % (info['bss'], img.bss[0]))
    print('  .text 0x%x..0x%x   MOD0 at 0x%x   eh_frame_hdr 0x%x   dynamic 0x%x' % (img.text[0], img.text[0] + img.text[1], img.mod0, img.eh_hdr, img.meta['dynamic']))
    ext = bytes(img.mem[img.mod0 + 0x1c:img.mod0 + 0x40])
    print('  MOD0 extension: ' + ext[:24].hex(' ') + ('  (%s)' % ext[:4].decode('latin-1') if ext[:3].isalnum() else ''))
    print('  dynamic tags: ' + ', '.join('%s=0x%x' % (DT.get(k, k), v) for k, v in img.dt.items() if k not in (0,)))
    for tag_a, tag_s, nm in ((25, 27, 'init_array'), (26, 28, 'fini_array'), (32, 33, 'preinit_array')):
        if tag_a in img.dt and img.dt.get(tag_s, 0):
            n = img.dt[tag_s] // 8
            ents = [img.ptr_at(img.dt[tag_a] + 8 * i) for i in range(n)]
            print('  %s: %d entries at 0x%x; first: %s' % (nm, n, img.base + img.dt[tag_a], ' '.join('%x' % e for e in ents[:4])))
    for tag, nm in ((12, 'DT_INIT'), (13, 'DT_FINI')):
        if tag in img.dt:
            print('  %s = 0x%x' % (nm, base + img.dt[tag]))
    c = collections.Counter(info & 0xffffffff for _, info, _ in img.relocs()); j = collections.Counter(info & 0xffffffff for _, info, _ in img.jmprel())
    print('  RELA: ' + ', '.join('%s=%d' % (RT.get(k, k), v) for k, v in c.items()) + '   JMPREL: ' + ', '.join('%s=%d' % (RT.get(k, k), v) for k, v in j.items()))
    syms = img.symbols()
    nd = [s for s in syms if s[3] and s[0]]; nu = [s for s in syms if not s[3] and s[0]]
    defs[name] = {s[0]: base + s[4] for s in nd}; undefs[name] = [s[0] for s in nu]
    print('  dynsym: %d total, %d defined (%d FUNC), %d undefined' % (len(syms), len(nd), sum(1 for s in nd if s[1] == 2), len(nu)))
    for w in ('nnMain', 'nninitStartup', '_init', '_fini', 'main', '_start'):
        if w in defs[name]:
            print('  symbol %s = 0x%x' % (w, defs[name][w]))
    if name == 'rtld':
        w0 = img.u32(0); print('  rtld word0 %08x (b +0x%x)' % (w0, (w0 & 0x3ffffff) * 4 if (w0 & 0xfc000000) == 0x14000000 else -1))
print()
for name in ('main', 'sdk', 'subsdk0'):
    ud = undefs[name]
    prov = collections.Counter(); left = []
    for u in ud:
        where = [m for m in ('main', 'sdk', 'subsdk0') if m != name and u in defs[m]]
        if where: prov[where[0]] += 1
        else: left.append(u)
    print('%s: %d undefined imports -> provided by ' % (name, len(ud)) + ', '.join('%s %d' % kv for kv in prov.items()) + ', host/libc/unresolved %d' % len(left))
    pfx = collections.Counter((u.split('(')[0].split('::')[0] if not u.startswith('_Z') else ('_Z*' + ('nn' if u.startswith('_ZN2nn') else 'other'))) for u in left)
    print('   unresolved by prefix: ' + ', '.join('%s=%d' % kv for kv in pfx.most_common(12)))
    if outdir:
        os.makedirs(outdir, exist_ok=True)
        with open(os.path.join(outdir, '%s.imports.tsv' % name), 'w') as f:
            f.write('index\tname\tprovider\n')
            allsyms = imgs[name].symbols()
            for i, s in enumerate(allsyms):
                if not s[3] and s[0]:
                    w = [m for m in ('main', 'sdk', 'subsdk0') if m != name and s[0] in defs[m]]
                    f.write('%d\t%s\t%s\n' % (i, s[0], w[0] if w else '-'))

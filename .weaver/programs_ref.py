"""programs_ref.py -- S24 reference list of shader programs from the Python survey corpus (work/survey/shaders/corpus): every program set
(vertex + fragment [+ geometry]) as the runtime's code hashes (first 16 hex digits of SHA-1 of the code block). Writes the MPRPRG01 file
the C++ scan in tools/setup must reproduce: magic 'MPRPRG01', u32 count, u32 0, then count records of 3 x u64 little-endian (vs, fs, gs; 0 = none),
sorted, unique.   python programs_ref.py OUT.bin"""
import csv, hashlib, struct, sys, collections
corp = r'D:\AI\Active\Metroid-Prime\work\survey\shaders\corpus'
real = {}
sets = collections.defaultdict(dict)
for r in csv.DictReader(open(corp + '/manifest.tsv'), delimiter='\t'):
    lab = r['code_sha1_16']
    if lab not in real:
        real[lab] = hashlib.sha1(open(corp + '/' + r['code_file'], 'rb').read()).hexdigest()[:16]
    base, _, s = r['id'].rpartition('_s')
    sets[base][r['stage']] = int(real[lab], 16)
tri = sorted(set((d.get('vertex', 0), d.get('fragment', 0), d.get('geometry', 0)) for d in sets.values() if 'vertex' in d and 'fragment' in d))
with open(sys.argv[1], 'wb') as f:
    f.write(b'MPRPRG01' + struct.pack('<II', len(tri), 0))
    for t in tri: f.write(struct.pack('<3Q', *t))
print(len(tri), 'programs written to', sys.argv[1])

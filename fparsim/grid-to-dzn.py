from __future__ import print_function
import sys

inpfile = open(sys.argv[1])
outfile = open(sys.argv[2],'w')

inpline = ''
num_processors = ''
num_links = ''
for inpline in inpfile:
    if not inpline.lstrip().startswith('%'):
        [num_processors, num_links] = inpline.split()
        break

p_from = ''
p_to = ''
r_ref = ''
for inpline in inpfile:
    if not inpline.lstrip().startswith('%'):
        [p_from, p_to, r_ref] = inpline.split()
        break
p_from = int(p_from) + 1
p_to = int(p_to) + 1

p = []
cc = [['0' for i in range(int(num_processors))] for j in range(int(num_processors))]
proc_id = 0
for inpline in inpfile:
    if not inpline.lstrip().startswith('%'):
        cols = inpline.split()
        p.append(int(cols[0]))
        chunks = [cols[i:i+3] for i in range(1,len(cols),3)]
        for chunk in chunks:
            cc[proc_id][int(chunk[0])] = chunk[1]
        proc_id += 1

outfile.write('M = {};\n'.format(num_processors))
outfile.write('p = {};\n'.format(p))
outfile.write('InvRref = {};\n'.format(int(1/float(r_ref))))
outfile.write('Pfrom = {};\n'.format(p_from))
outfile.write('Pto = {};\n'.format(p_to))
outfile.write('cc = [|{}|];\n'.format(',\n\t|'.join((','.join(cc_elem for cc_elem in cc_row)) for cc_row in cc)))

inpfile.close()
outfile.close()

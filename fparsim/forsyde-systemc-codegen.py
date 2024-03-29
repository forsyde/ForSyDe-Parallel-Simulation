from __future__ import print_function
import sys
import os
import subprocess
import xml.etree.ElementTree as ET

SIGNAL_DEPTH = 2

# Input ForSyDe model
tree = ET.parse(sys.argv[1])

# Input model characteristics
ctree = ET.parse(sys.argv[2])

# Output folder
outfolder = sys.argv[3]

inproot = tree.getroot()
inparent = {c:p for p in inproot.iter() for c in p}

inpcharroot = ctree.getroot()

def getbindings(port):
    bound = None
    if port==None:
        return bound
    #binding to signals
    if port.attrib['direction']=='in':
        bound = inproot.findall("signal/[@target='{}'][@target_port='{}']".format(
            inparent[port].attrib['name'],
            port.attrib['name']
        ))
    else:
        bound = inproot.findall("signal/[@source='{}'][@source_port='{}']".format(
            inparent[port].attrib['name'],
            port.attrib['name']
        ))
    # binding to top-level ports
    bound += inproot.findall("port/[@bound_process='{}'][@bound_port='{}']".format(
        inparent[port].attrib['name'],
        port.attrib['name']
    ))
    return bound

def gensynactor(cp):
    sink_node = sys.argv[-1]
    output = open('{}/{}_{}.hpp'.format(outfolder, cp.attrib['name'], cp.attrib['component_name']),'w')
    inpports = cp.findall("port/[@direction='in']")
    outports = cp.findall("port/[@direction='out']")
    output.write('#ifndef {0}_{1}_HPP\n#define {0}_{1}_HPP\n'.format(cp.attrib['name'].upper(),cp.attrib['component_name'].upper()))
    output.write('#include "forsyde.hpp"\n')
    output.write('using namespace std;\n')
    # generate the synthetic function
    if len(inpports)==0:
        fotype = '{}&'.format(outports[0].attrib['type'] if len(outports)==1 else
            'tuple<{}>'.format(','.join('vector<{}>'.format(p.attrib['type']) for p in outports))
        )
        otoks = cp.attrib['otoks'][1:-1].split(',')
        output.write('void {}_{}_leaf_func ({} out1, const {} inp1) {{\n{}\n{}\n}}\n'.format(
            cp.attrib['name'],
            cp.attrib['component_name'],
            fotype,
            fotype,
            'static int i=0;volatile int j,k;\nfor(j=0;j<{};j++)for(k=0;k<1000000;k++); std::cout<<"from: {} iter: "<<i++<<std::endl;\n'.format(
                inpcharroot.find("Element[@process='{}']".format(cp.attrib['name'])).attrib['executionTime'],
                cp.attrib['name']
                ),
            '\n'.join('get<{}>(out1).resize({});'.format(i,otok) for i,otok in enumerate(otoks)) if len(otoks)>1 else ''
            ))
    elif len(outports)==0:
        fitype = 'const {}&'.format(inpports[0].attrib['type'] if len(inpports)==1 else
            'tuple<{}>'.format(','.join('vector<{}>'.format(p.attrib['type']) for p in inpports))
        )
        output.write('void {}_{}_leaf_func ({} inp1) {{\n{}\n{}\n}}\n'.format(
            cp.attrib['name'],
            cp.attrib['component_name'],
            fitype,
            'static int i=0;volatile int j,k;\nfor(j=0;j<{};j++)for(k=0;k<1000000;k++); std::cout<<"from: {} iter: "<<i++<<std::endl;\n'.format(
                inpcharroot.find("Element[@process='{}']".format(cp.attrib['name'])).attrib['executionTime'],
                cp.attrib['name']
                ),
            'if (i>=10) MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);' if sink_node == cp.attrib['name'] else ''
            ))
    else:
        fitype = 'const vector<{}>&'.format(inpports[0].attrib['type'] if len(inpports)==1 else
            'tuple<{}>'.format(','.join('vector<{}>'.format(p.attrib['type']) for p in inpports))
        )
        fotype = 'vector<{}>&'.format(outports[0].attrib['type'] if len(outports)==1 else
            'tuple<{}>'.format(','.join('vector<{}>'.format(p.attrib['type']) for p in outports))
        )
        otoks = cp.attrib['otoks'][1:-1].split(',')
        output.write('void {}_{}_leaf_func ({} out1, {} inp1) {{\n{}\n{}\n{}\n}}\n'.format(
            cp.attrib['name'],
            cp.attrib['component_name'],
            fotype,
            fitype,
            'static int i=0;volatile int j,k;\nfor(j=0;j<{};j++)for(k=0;k<1000000;k++); std::cout<<"from: {} iter: "<<i++<<std::endl;\n'.format(
                inpcharroot.find("Element[@process='{}']".format(cp.attrib['name'])).attrib['executionTime'],
                cp.attrib['name']
                ),
            '\n'.join('get<{}>(out1[0]).resize({});'.format(i,otok) for i,otok in enumerate(otoks)) if len(otoks)>1 else '',
            'if (i>=10) MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);' if sink_node == cp.attrib['name'] else ''
            ))
    # generate the synthetic module 
    output.write('SC_MODULE({}_{}) {{\n'.format(cp.attrib['name'],cp.attrib['component_name']))
    for port in cp.findall('port'):
        output.write('\tForSyDe::{}::{}_port<{}> {};\n'.format(
            port.attrib['moc'].upper(),
            port.attrib['direction'],
            port.attrib['type'],
            port.attrib['name']
        ))
    # TODO: define two zipper signals zi, zo
    if len(inpports)>1:
        output.write('\tForSyDe::SDF::signal< tuple<{}> > zi;\n'.format(
            ','.join('vector<{}>'.format(p.attrib['type']) for p in inpports)
        ))
    if len(outports)>1:
        output.write('\tForSyDe::SDF::signal< tuple<{}> > zo;\n'.format(
            ','.join('vector<{}>'.format(p.attrib['type']) for p in outports)
        ))
    output.write('\tSC_CTOR({}_{}) {{\n'.format(cp.attrib['name'],cp.attrib['component_name']))
    
    if len(inpports)>1:
        output.write('\t\tauto zip1 = new ForSyDe::SDF::zipN<{}>("zip1",{});\n'.format(
            ','.join(t.attrib['type'] for t in inpports),
            cp.attrib['itoks']
        ))
        for i,port in enumerate(inpports):
            output.write('\t\tget<{}>(zip1->iport)({});\n'.format(i,port.attrib['name']))
        output.write('\t\tzip1->oport1(zi);\n')

    if len(inpports)==0:
        output.write('\t\tForSyDe::SDF::make_source("{2}_{0}_leaf", {2}_{0}_leaf_func, {{}}, 10, {1});\n'.format(
                cp.attrib['component_name'],
                'zo' if len(outports)>1 else outports[0].attrib['name'],
                cp.attrib['name'],
            ))
    elif len(outports)==0:
        output.write('\t\tForSyDe::SDF::make_sink("{2}_{0}_leaf", {2}_{0}_leaf_func, {1});\n'.format(
                cp.attrib['component_name'],
                'zi' if len(inpports)>1 else inpports[0].attrib['name'],
                cp.attrib['name'],
            ))
    else:
        output.write('\t\tForSyDe::SDF::make_comb("{5}_{0}_leaf", {5}_{0}_leaf_func, {1}, {2}, {3}, {4});\n'.format(
                cp.attrib['component_name'],
                '1' if len(outports)>1 else cp.attrib['otoks'][1:-1],
                '1' if len(inpports)>1 else cp.attrib['itoks'][1:-1],
                'zo' if len(outports)>1 else outports[0].attrib['name'],
                'zi' if len(inpports)>1 else inpports[0].attrib['name'],
                cp.attrib['name'],
            ))

    if len(outports)>1:
        output.write('\t\tauto unzip1 = new ForSyDe::SDF::unzipN<{}>("unzip1",{});\n'.format(
            ','.join(t.attrib['type'] for t in outports),
            cp.attrib['otoks']
        ))
        output.write('\t\tunzip1->iport1(zo);\n')
        for i,port in enumerate(outports):
            output.write('\t\tget<{}>(unzip1->oport)({});\n'.format(i,port.attrib['name']))
    output.write('}\n};\n')
    output.write('#endif\n')
    output.close()

output = open('{}/{}.hpp'.format(outfolder, inproot.attrib['name']),'w')

# generate the process network
output.write('#include <forsyde.hpp>\n')
# include composite process definitions
for cp in inproot.findall('composite_process'):
    # should generate childs recursively?
    if '-r' in sys.argv:
        # is it a synthetic benchmark test?
        if '-s' in sys.argv:
            gensynactor(cp)
        else:
            subprocess.call(['python {} {} {}'.format(sys.argv[0],os.path.dirname(sys.argv[1])+'/'+cp.attrib['component_name']+'.xml',sys.argv[2])], shell=True)
    output.write('#include "{}_{}.hpp"\n'.format(cp.attrib['name'],cp.attrib['component_name']))
# include leaf process definitions
for lp in inproot.findall('leaf_process'):
    for pcarg in lp.findall('process_constructor/argument'):
        if pcarg.attrib['name'].endswith('_func'):
            output.write('#include "{}{}.hpp"\n'.format(lp.attrib['name'],pcarg.attrib['name']))
# the top-level module
output.write('SC_MODULE({}) {{\n'.format(inproot.attrib['name']))
# top-level ports
for port in inproot.findall('port'):
    # print              ("*[@name='{}']/port[@name='iport1']".format(port.attrib['bound_process']))
    # print (inproot.find("*[@name='{}']/port[@name='iport1']".format((port.attrib['bound_process'])).attrib['moc']).upper())
    output.write('\tForSyDe::{}::{}_port<{}> {};\n'.format(
        port.attrib['moc'].upper(),
        port.attrib['direction'],
        port.attrib['type'],
        port.attrib['name']
    ))
# top-level signals
for sig in inproot.findall('signal'):
    output.write('\tForSyDe::{}::signal<{}> {};\n'.format(
        sig.attrib['moc'].upper(),
        sig.attrib['type'],
        sig.attrib['name']
    ))
# the constructor
output.write('SC_CTOR({}){} {{\n'.format(
    inproot.attrib['name'],
    '' if inproot.find('signal') is None else ': '+','.join('{0}("{0}",{1})'.format(sig.attrib['name'],SIGNAL_DEPTH) for sig in inproot.findall('signal'))
    ))
# top-level leaves
for lp in inproot.findall('leaf_process'):
    # output.write('\tauto {} = new ForSyDe::{}::{}({});\n'.format(
    #     lp.attrib['name'],
    #     lp.find('process_constructor').attrib['moc'],
    #     lp.find('process_constructor').attrib['name'],
    #     ','.join(arg.attrib['name'] for arg in lp.find('process_constructor').findall('argument'))
    # ))
    lpins = lp.findall("port/[@direction='in']")
    lpout = lp.find("port/[@direction='out']")
    output.write('\tauto {0} = ForSyDe::{1}::make_{2}("{0}",{3}{4}{5});\n'.format(
        lp.attrib['name'],
        lp.find('process_constructor').attrib['moc'].upper(),
        lp.find('process_constructor').attrib['name'],
        ','.join(arg.attrib['value'] for arg in lp.find('process_constructor').findall('argument')),
        (','+getbindings(lpout)[0].attrib['name']) if lpout is not None else '',
        (','+(','.join(getbindings(p)[0].attrib['name'] for p in lpins))) if len(lpins)>0 else '',
    ))

    if lpout is not None:
        for i,bound in enumerate(getbindings(lpout)):
            if i>0:
                output.write('\t\t{}->{}({});\n'.format(
                    lp.attrib['name'],
                    lpout.attrib['name'],
                    bound.attrib['name']
                ))
# top-level composites
for cp in inproot.findall('composite_process'):
    output.write('\tauto {0} = new {0}_{1}("{0}");\n'.format(
        cp.attrib['name'],
        cp.attrib['component_name']
    ))
    for port in cp.findall('port'):
        bound = None
        boundsig = None
        boundport = None
        if port.attrib['direction']=='in':
            boundsig = inproot.find("signal/[@target='{}'][@target_port='{}']".format(
                cp.attrib['name'],
                port.attrib['name']
            ))
        else:
            boundsig = inproot.find("signal/[@source='{}'][@source_port='{}']".format(
                cp.attrib['name'],
                port.attrib['name']
            ))
        if boundsig != None:
            bound = boundsig
        else:
            boundport = inproot.find("port/[@bound_process='{}'][@bound_port='{}']".format(
                cp.attrib['name'],
                port.attrib['name']
            ))
            bound = boundport
        output.write('\t\t{}->{}({});\n'.format(
            cp.attrib['name'],
            port.attrib['name'],
            bound.attrib['name']
        ))
output.write('}\n')
output.write('};\n')
output.close()

if '-m' in sys.argv:
    output = open('{}/main.cpp'.format(outfolder),'w')
    output.write('#include "{}.hpp"\n'.format(inproot.attrib['name']))
    output.write('int sc_main(int argc, char **argv) {\n')
    output.write('MPI_Init (&argc, &argv);\n')
    output.write('\t{0} top1("{0}1");\n\n'.format(inproot.attrib['name']))
    output.write('\tsc_core::sc_start();\n\n')
    output.write('MPI_Finalize();\n')
    output.write('\treturn 0;\n')
    output.write('}\n')

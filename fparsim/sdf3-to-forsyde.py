from __future__ import print_function
import sys
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Input SDF3 model
tree = ET.parse(sys.argv[1])
#output ForSyDe-XML
#output = open(sys.argv[2],'w')

inproot = tree.getroot()
inproot_sdf = inproot.find('applicationGraph').find('sdf')

outroot = ET.Element('process_network')
outroot.set('name', os.path.splitext(os.path.basename(sys.argv[2]))[0])

# Generate signals
for inpchannel in inproot.findall('./applicationGraph/sdf/channel'):
    channelattribs = inpchannel.attrib
    outchannel = ET.SubElement(outroot,'signal')
    outchannel.set('name', channelattribs['name'])
    outchannel.set('moc', 'sdf')
    outchannel.set('type', 'double')
    outchannel.set('source', channelattribs['srcActor'])
    outchannel.set('source_port', channelattribs['srcPort'])
    outchannel.set('target', channelattribs['dstActor'])
    outchannel.set('target_port', channelattribs['dstPort'])

# Generate delay actors
for inpchannel in inproot.findall('./applicationGraph/sdf/channel'):
    channelattribs = inpchannel.attrib
    if 'initialTokens'in channelattribs and channelattribs['initialTokens']>0:
        # make a delayn
        outprocess = ET.SubElement(outroot,'leaf_process')
        outprocess.set('name', channelattribs['name'] + '_delay')
        ET.SubElement(outprocess,'port', {'name':"iport1",'moc':'sdf','type':"double",'direction':"in"})
        ET.SubElement(outprocess,'port', {'name':"oport1",'moc':'sdf','type':"double",'direction':"out"})
        outpc = ET.SubElement(outprocess,'process_constructor', {'name':"delayn",'moc':"sdf"})
        ET.SubElement(outpc,'argument', {'name':"init_val",'value':"0.0"})
        ET.SubElement(outpc,'argument', {'name':"n",'value':channelattribs['initialTokens']})
        
        # make a new signal
        outsignal = outroot.find("signal/[@name='{}']".format(channelattribs['name']))
        newoutsig = ET.Element('signal')
        newoutsig.set('name', channelattribs['name'] + '_delaysig')
        newoutsig.set('moc', 'sdf')
        newoutsig.set('type', 'double')
        newoutsig.set('source', channelattribs['name'] + '_delay')
        newoutsig.set('source_port', 'oport1')
        newoutsig.set('target', outsignal.attrib['target'])
        newoutsig.set('target_port', outsignal.attrib['target_port'])
        outroot.insert(list(outroot).index(outroot.find('leaf_process')), newoutsig)

        # rewire
        outsignal.set('target', channelattribs['name'] + '_delay')
        outsignal.set('target_port', 'iport1')

# for inpactor in inproot.findall('./applicationGraph/sdf/actor'):
#     actorattribs = inpactor.attrib
#     outprocess = ET.SubElement(outroot,'leaf_process')
#     outprocess.set('name', actorattribs['name'])
#     for inpport in inpactor.findall('port'):
#         portattribs = inpport.attrib
#         outport = ET.SubElement(outprocess,'port')
#         outport.set('name', portattribs['name'])
#         outport.set('type', 'double')
#         outport.set('direction', portattribs['type'])
#     outpc = ET.SubElement(outprocess,'process_constructor')
#     outpcnuminps = len(inpactor.findall("port/[@direction='in']"))
#     outpcnumouts = len(inpactor.findall("port/[@direction='out']"))
#     outpcname = ''
#     if outpcnuminps>0 and outpcnumouts>0:
#         outpcname = 'comb{}'.format(outpcnuminps if outpcnuminps>1 else '')
#     elif outpcnuminps>0 and outpcnumouts==0:
#         outpcname = 'source'
#     else:
#         outpcname = 'sink'
#     outpc.set('name', outpcname)

# Generate processes
for inpactor in inproot.findall('./applicationGraph/sdf/actor'):
    actorattribs = inpactor.attrib
    outprocess = ET.SubElement(outroot,'composite_process')
    outprocess.set('name', actorattribs['name'])
    outpcnuminps = len(inpactor.findall("port/[@type='in']"))
    outpcnumouts = len(inpactor.findall("port/[@type='out']"))
    outprocess.set('component_name', 'actor_{}_{}'.format(outpcnuminps, outpcnumouts))
    outprocess.set('itoks', '{' + (','.join(p.attrib['rate'] for p in inpactor.findall("port/[@type='in']"))) + '}')
    outprocess.set('otoks', '{' + (','.join(p.attrib['rate'] for p in inpactor.findall("port/[@type='out']"))) + '}')
    for inpport in inpactor.findall('port'):
        portattribs = inpport.attrib
        outport = ET.SubElement(outprocess,'port')
        outport.set('name', portattribs['name'])
        outport.set('moc', 'sdf')
        outport.set('type', 'double')
        outport.set('direction', portattribs['type'])

xmlstr = minidom.parseString(ET.tostring(outroot)).toprettyxml(indent="    ")
with open(sys.argv[2], "w") as f:
    f.write(xmlstr)
# outet = ET.ElementTree(outroot)
# outet.write(sys.argv[2])
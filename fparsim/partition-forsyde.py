from __future__ import print_function
import sys
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from copy import deepcopy

# Input ForSyDe model
seqtree = ET.parse(sys.argv[1])

# Input number of partitions
numparts = sys.argv[2]

# Input partitioning
parttree = ET.parse(sys.argv[3])

# Output folder
outfolder = sys.argv[4]

inproot = seqtree.getroot()
# cut set
def cutserpred(sig):
    src = parttree.find("Element/[@process='{}']".format(sig.attrib['source'])).attrib['processor']
    dst = parttree.find("Element/[@process='{}']".format(sig.attrib['target'])).attrib['processor']
    return (src != dst)

cutset = filter(cutserpred, inproot.findall('signal'))

outroots = []
for part in range(int(numparts)):
    outroot = None
    outroot = ET.Element('process_network')
    outroot.set('name', '{}_{}'.format(inproot.attrib['name'],part))
    outroots.append(outroot)

for inproc in inproot.findall('composite_process'):
    part = parttree.find("Element/[@process='{}']".format(inproc.attrib['name'])).attrib['processor']
    outroots[int(part)].append(inproc)
for inproc in inproot.findall('leaf_process'):
    part = parttree.find("Element/[@process='{}']".format(inproc.attrib['name'])).attrib['processor']
    outroots[int(part)].append(inproc)
for i, inpsig in enumerate(inproot.findall('signal')):
    if not (inpsig in cutset):
        part = parttree.find("Element/[@process='{}']".format(
            inpsig.attrib['source']
        )).attrib['processor']
        outroots[int(part)].append(inpsig)
    else:
        spart = parttree.find("Element/[@process='{}']".format(
            inpsig.attrib['source']
        )).attrib['processor']
        dpart = parttree.find("Element/[@process='{}']".format(
            inpsig.attrib['target']
        )).attrib['processor']
        # add sender
        sender = ET.SubElement(outroots[int(spart)], 'leaf_process')
        sender.set('name', 'sender_{}'.format(i))
        ET.SubElement(sender, 'port', {'name':'iport1', 'type':'double', 'direction':'in'})
        senderpc = ET.SubElement(sender, 'process_constructor', {'name':'sender', 'moc':'sdf'})
        ET.SubElement(senderpc, 'argument', {'name':'destination', 'value':dpart})
        ET.SubElement(senderpc, 'argument', {'name':'tag', 'value':str(i)})
        # add receiver
        receiver = ET.SubElement(outroots[int(dpart)], 'leaf_process')
        receiver.set('name', 'receiver_{}'.format(i))
        ET.SubElement(receiver, 'port', {'name':'oport1', 'type':'double', 'direction':'out'})
        receiverpc = ET.SubElement(receiver, 'process_constructor', {'name':'receiver', 'moc':'sdf'})
        ET.SubElement(receiverpc, 'argument', {'name':'source', 'value':spart})
        ET.SubElement(receiverpc, 'argument', {'name':'tag', 'value':str(i)})
        # add signal to source
        outroots[int(spart)].append(deepcopy(inpsig))
        inpsigsrc = outroots[int(spart)].find("signal/[@name='{}']".format(inpsig.attrib['name']))
        inpsigsrc.attrib['target'] = sender.attrib['name']
        inpsigsrc.attrib['target_port'] = 'iport1'
        # add signal to destination
        outroots[int(dpart)].append(deepcopy(inpsig))
        inpsigdst = outroots[int(dpart)].find("signal/[@name='{}']".format(inpsig.attrib['name']))
        inpsigdst.attrib['source'] = receiver.attrib['name']
        inpsigdst.attrib['source_port'] = 'oport1'


for part in range(int(numparts)):
    xmlstr = minidom.parseString(ET.tostring(outroots[part])).toprettyxml(indent="    ")
    with open('{}/{}_{}.xml'.format(outfolder,inproot.attrib['name'],part), "w") as f:
        f.write(xmlstr)
from __future__ import print_function
import sys
import xml.etree.ElementTree as ET
import xml.etree.ElementTree as ET1

output = open(sys.argv[2],'w')
#output = open('50exectime.xml','w')
tree = ET.parse(sys.argv[1])
#tree = ET.parse('50.xml')

root = tree.getroot()
wroot = ET1.Element('Root')

for actor in root.iter('actor') :
    edgedict = {}
    exectime = "0"
    for actprop in root.iter('actorProperties') :
        if actor.attrib["name"] == actprop.attrib["actor"] :
            exectime = actprop[0][0].attrib['time']
            ET1.SubElement(wroot , 'Element' , attrib = {'executionTime' : str(exectime), 'process' : str(actor.attrib["name"])})

output.write(ET1.tostring(wroot, encoding='us-ascii', method='xml'))
output.close()


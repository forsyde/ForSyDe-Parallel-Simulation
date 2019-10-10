from __future__ import print_function
import sys
import xml.etree.ElementTree as ET

def toSDFConvention(name) :
    return "a" + str(int(name)-1)

input = open(sys.argv[1],'r')
#input = open('graph31.txt.part.4','r')
output = open(sys.argv[2],'w')
#output = open ('graphdist31.xml','w')
synthetic = '' if len(sys.argv)<4 else ET.parse(sys.argv[3]).getroot()

root = ET.Element('Root')
i = 0
for line in input :
    ET.SubElement(root , 'Element' , attrib = {'process' : str('a' + str(i))  , 'processor' : line[0]})
    if synthetic != '':
        for channel in synthetic.findall("applicationGraph/sdf/channel/[@dstActor='{}']".format(('a' + str(i)))):
            ET.SubElement(root , 'Element' , attrib = {'process' : channel.attrib['name']+'_delay'  , 'processor' : line[0]})
    i = i + 1

output.write(ET.tostring(root, encoding='us-ascii', method='xml'))
output.close()

from __future__ import print_function
import sys
import xml.etree.ElementTree as ET
def printnode(name) :
    return str((int(name.replace("a","")) + 1))

output = open(sys.argv[2],'w')
#output = open('partitioning.dzn','w')
tree = ET.parse(sys.argv[1])
#tree = ET.parse('file2.xml')

numprocessors = sys.argv[3]

root = tree.getroot()
nodeNumber = 0
channelNumber = 0

for actor in root.iter('actor') :
    nodeNumber = nodeNumber + 1

for channel in root.iter('channel') :
    if not (channel.attrib['srcActor'] == channel.attrib['dstActor']) :
        channelNumber = channelNumber + 1

for channel in root.iter('channel') :
    for channels in root.iter('channel') :
        if channel != channels :
            if ((not (channels.attrib["srcActor"] == channels.attrib["dstActor"])) and (channel.attrib['srcActor'] == channels.attrib['srcActor']) and (channel.attrib['dstActor'] == channels.attrib['dstActor'])) :
                secondSize = 0
                firstSize = 0
                for chp in root.iter('channelProperties') :
                     if (chp.attrib["channel"] == channels.attrib["name"]) :
                         secondSize = int(chp.find("tokenSize").attrib["sz"])
                         root[0][1].remove(chp)
                     if (chp.attrib["channel"] == channel.attrib["name"]) :
                         firstSize = int(chp.find("tokenSize").attrib["sz"])
                for chp in root.iter('channelProperties') :
                    if (chp.attrib["channel"] == channel.attrib["name"]) :
                        chp.find("tokenSize").set("sz",str(firstSize+secondSize))
                        root[0][0].remove(channels)


output.write('M = {};\n'.format(numprocessors))
output.write("N = " + str(nodeNumber) + ';' + " \n")
exectimeStr = ""
for act in root.iter('actor') :
    edgedict = {}
    exectime = "0"
    for actprop in root.iter('actorProperties') :
        if act.attrib["name"] == actprop.attrib["actor"] :
            exectime = actprop[0][0].attrib['time']
    exectimeStr = exectimeStr + str(exectime) + ","
if exectimeStr.endswith(','):
    exectimeStr = exectimeStr[:-1]

output.write("e = [" + exectimeStr + "]" + ";" + "\n")

matrix = "[|"
for act1 in root.iter('actor') :
    for act2 in root.iter('actor') :
        flag = 0
        for ch in root.iter('channel') :
            if (ch.attrib['srcActor'] == act1.attrib['name']) and (ch.attrib['dstActor'] == act2.attrib['name']) :
                for chprop in root.iter('channelProperties') :
                    if chprop.attrib['channel'] == ch.attrib['name'] :
                        matrix = matrix + str(chprop[0].attrib['sz']) + ','
                        flag = 1
        if flag == 0 :
            matrix = matrix + '0' + ','
    matrix = matrix + '\n' + '|'

matrix = matrix[:-2]

output.write("c = " + matrix + "|]" + ";")

output.close()

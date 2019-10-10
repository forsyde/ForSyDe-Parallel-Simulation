from __future__ import print_function
import subprocess
import sys
import argparse
from os.path import basename
from shutil import copy

SDF_PATH = '/home/shaniaki/Downloads/sdf3/build/release/Linux/bin/'
PAGRID_PLATFORM = '~/Downloads/PaGridL/Example/cpu.grid'
TEMPLATE_PATH = '../templates'

parser = argparse.ArgumentParser(description='The ForSyDe Parallel & Distributed Simulation Flow')
parser.add_argument('apptype', choices=['real', 'synthetic'], help='An introspected output of a real application or a generated synthetic one')
parser.add_argument('partitioner', choices=['metis', 'pagrid'], help='The partitioning tool used')
parser.add_argument('-n', '--numprocesses', type=int, help='For synthetic applications, the number of application nodes')
parser.add_argument('-p', '--numprocessors', type=int, help='For simple homogeneous architectures, the number of processors')
parser.add_argument('-o', '--outputfolder', type=str, help='The output folder where the generated files reside')
args = parser.parse_args()

#if args.apptype=='real':
#  print ('n= ', args.numprocesses)
#else:
#  print ('synthetic')
#sys.exit()
#num_processes = sys.argv[1];
#num_processors = sys.argv[2];

if args.outputfolder is None:
	args.outputfolder = "../examples"

# set number of actors in sdf.opt
if args.apptype=='synthetic':
	if args.numprocesses is None:
		print ('Must provide the number of processes for synthetic application')
		sys.exit()
	else:
		num_processes = str(args.numprocesses)

	with open(TEMPLATE_PATH + '/sdf3-template.opt') as f:
	    newText=f.read().replace('_num_processes_', num_processes)
	with open(args.outputfolder+'/sdf3.opt', "w") as f:
	    f.write(newText)

	# Generate SDF3
	print ('Generating the SDF graph...')
	subprocess.call([SDF_PATH + 'sdf3generate-sdf --settings {0}/sdf3.opt --output {0}/{1}.xml'.format(args.outputfolder,num_processes)], shell=True)

	# Convert to Metis Format
	print ('Converting to Metis graph format...')
	subprocess.call(['python sdf3-to-metis.py {0}/{1}.xml {0}/{1}.metis'.format(args.outputfolder,num_processes)], shell=True)

	if args.partitioner=='metis':
		if args.numprocessors is None:
			print ('Must provide the number of processors for partitioning a synthetic application with Metis')
			sys.exit()
		else:
			num_processors = str(args.numprocessors)
		# Invoke Metis
		print ('Partioning with Metis...')
		subprocess.call(['gpmetis {0}/{1}.metis {2}'.format(args.outputfolder,num_processes,num_processors)], shell=True)

		# Convert to partitions to XML
		subprocess.call(['python partitions-to-xml.py {0}/{1}.metis.part.{2} {0}/{1}.map.{2}.xml {0}/{1}.xml'.format(args.outputfolder,num_processes,num_processors)], shell=True)
		
	elif args.partitioner=='pagrid':
		if PAGRID_PLATFORM is None:
			print ('Must provide the PaGrid platform file for partitioning a synthetic application with PaGrid')
			sys.exit()
		else:
			num_processors = 8#basename(PAGRID_PLATFORM)
		# Invoke Pagrid
		print ('Partioning with Pagrid...')
		subprocess.call(['pagrid {0}/{1}.metis {2}'.format(args.outputfolder,num_processes,PAGRID_PLATFORM)], shell=True)

		# Convert to partitions to XML
		subprocess.call(['python partitions-to-xml.py {1}.metis.cpu.grid.result {0}/{1}.map.{2}.xml'.format(args.outputfolder,num_processes,num_processors)], shell=True)
#elif args.apptype=='real':
	
	
# Convert the sequential model to ForSyDe-XML
print ('Converting the model to ForSyDe-XML...')
subprocess.call(['python sdf3-to-forsyde.py {0}/{1}.xml {0}/forsyde_{1}.xml'.format(args.outputfolder,num_processes)], shell=True)

# Partition the model
print ('Partitioning the model...')
subprocess.call(['mkdir -p {0}/{1}.map.{2}'.format(args.outputfolder,num_processes,num_processors)], shell=True)
subprocess.call(['python partition-forsyde.py {0}/forsyde_{1}.xml {2} {0}/{1}.map.{2}.xml {0}/{1}.map.{2}'.format(args.outputfolder,num_processes,num_processors)], shell=True)

# Generate SystemC projects
print ('Generating source codes for the partitioned model...')
subprocess.call(['mkdir -p {0}/{1}.map.{2}-src'.format(args.outputfolder,num_processes,num_processors)], shell=True)
copy(TEMPLATE_PATH+'/Makefile.defs','{0}/{1}.map.{2}-src/'.format(args.outputfolder,num_processes,num_processors))
# subprocess.call(['cp {3}/Makefile.defs {0}/{1}.map.{2}-src/'.format(args.outputfolder,num_processes,num_processors,TEMPLATE_PATH)])
# print('cp {3}/Makefile {0}/{1}.map.{2}-src/'.format(args.outputfolder,num_processes,num_processors,TEMPLATE_PATH))
# subprocess.call(['cp {3}/Makefile {0}/{1}.map.{2}-src/'.format(args.outputfolder,num_processes,num_processors,TEMPLATE_PATH)])
copy(TEMPLATE_PATH+'/Makefile','{0}/{1}.map.{2}-src/'.format(args.outputfolder,num_processes,num_processors))
for i in range(int(num_processors)):
	subprocess.call(['mkdir -p {0}/{1}.map.{2}-src/forsyde_{1}_{3}'.format(args.outputfolder,num_processes,num_processors,i)], shell=True)
	# subprocess.call(['cp {4}/Makefile-sub {0}/{1}.map.{2}-src/forsyde_{1}_{3}/Makefile'.format(args.outputfolder,num_processes,num_processors,i,TEMPLATE_PATH)])
	copy(TEMPLATE_PATH+'/Makefile-sub','{0}/{1}.map.{2}-src/forsyde_{1}_{3}/Makefile'.format(args.outputfolder,num_processes,num_processors,i))
	if args.apptype=='synthetic':
		subprocess.call(['python forsyde-systemc-codegen.py {0}/{1}.map.{2}/forsyde_{1}_{3}.xml {0}/{1}.map.{2}-src/forsyde_{1}_{3} -m -r -s'.format(args.outputfolder,num_processes,num_processors,i)], shell=True)
	else:
		subprocess.call(['python forsyde-systemc-codegen.py {0}/{1}.map.{2}/forsyde_{1}_{3}.xml {0}/{1}.map.{2}-src/forsyde_{1}_{3} -m -r'.format(args.outputfolder,num_processes,num_processors,i)], shell=True)


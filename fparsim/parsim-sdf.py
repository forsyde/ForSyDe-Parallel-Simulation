from __future__ import print_function
import subprocess
import sys
import argparse
from os.path import basename
from shutil import copy

SDF_PATH = '~/Downloads/sdf3/build/release/Linux/bin/'
TEMPLATE_PATH = '../templates'
MINIZINC_PATH = '~/Downloads/MiniZincIDE-2.3.2-bundle-linux/bin/'

parser = argparse.ArgumentParser(description='The ForSyDe Parallel & Distributed Simulation Flow')
parser.add_argument('partitioner', choices=['metis', 'pagrid', 'cp-homo', 'cp-hetero'], help='The partitioning tool used')
parser.add_argument('-n', '--numprocesses', type=int, help='For synthetic applications, the number of application nodes')
parser.add_argument('-p', '--numprocessors', type=int, help='For simple homogeneous architectures, the number of processors')
parser.add_argument('-o', '--outputfolder', type=str, help='The output folder where the generated files reside')
parser.add_argument('-g', '--pagridplatform', type=str, help='The PaGrid platform specification file (if used)')
parser.add_argument('-t', '--heteroplatform', type=str, help='The CP-based heterogeneous platform specification file (if used)')
parser.add_argument('-s', '--sourcefolder', type=str, help='Source codes of the application')
parser.add_argument('-m', '--topname', type=str, help='Name of the top-level module')
args = parser.parse_args()

if args.outputfolder is None:
	args.outputfolder = "../examples"



# Compile the sequential application model
# TODO

# Execute the input application model
subprocess.call(['mkdir -p {0}/gen'.format(args.sourcefolder)], shell=True)
# TODO

# Extract application characteristics
print ('Extracting application characteristics...')
# TODO
# subprocess.call(['python ExecutionTimeFromSDF3.py {0}/{1}.xml {0}/{1}-charasteristics.xml'.format(args.outputfolder,num_processes)], shell=True)

# Convert to Metis Format
print ('Converting to Metis graph format...')
subprocess.call(['python forsyde-to-metis.py {0}/gen/{1}.xml {2}/{1}.metis'.format(args.sourcefolder,args.topname,args.outputfolder)], shell=True)

if args.partitioner=='metis':
	if args.numprocessors is None:
		print ('Must provide the number of processors for partitioning a synthetic application with Metis')
		sys.exit()
	else:
		num_processors = str(args.numprocessors)
	# Invoke Metis
	print ('Partioning with Metis...')
	subprocess.call(['gpmetis {0}/{1}.metis {2}'.format(args.outputfolder,args.topname,num_processors)], shell=True)

	# Convert partitions to XML
	subprocess.call(['python partitions-to-xml.py {0}/{1}.metis.part.{2} {0}/{1}.map.{2}.xml {0}/{1}.xml'.format(
		args.outputfolder,
		args.topname,
		num_processors)], shell=True)
	
elif args.partitioner=='cp-homo':
	if args.numprocessors is None:
		print ('Must provide the number of processors for partitioning a synthetic application with Metis')
		sys.exit()
	else:
		num_processors = str(args.numprocessors)
	
	# Convert graph to the Zinc data file
	print ('Converting to the Zinc application data format...')
	subprocess.call(['python sdf3-to-dzn.py {0}/{1}.xml {0}/app-{1}.dzn'.format(args.outputfolder,args.topname)], shell=True)

	# Generate platform Zinc data file
	print ('Generating the Zinc platform data format...')
	with open('{0}/plat-{1}.dzn'.format(args.outputfolder,num_processors), 'w') as f:
		f.write('M={};\n'.format(num_processors))

	# Invoke Minizinc for Homogeneous Partitioning
	print ('Invoking the MiniZinc CP model for homogeneous partitioning...')
	subprocess.call([MINIZINC_PATH+'minizinc --solver OR-Tools ../minizinc/partitioning-homogeneous.mzn {0}/app-{1}.dzn {0}/plat-{2}.dzn -o {0}/{1}.cp-homo.part.{2}-raw -p 8 -t 30000'.format(
		args.outputfolder,
		args.topname,
		num_processors)], shell=True)

	# strip the last two lines
	with open('{0}/{1}.cp-homo.part.{2}-raw'.format(args.outputfolder,args.topname,num_processors)) as f1:
		lines = f1.readlines()
	with open('{0}/{1}.cp-homo.part.{2}'.format(args.outputfolder,args.topname,num_processors), 'w') as f2:
		for line in lines:
			if not (line.startswith('-') or line.startswith('=')):
				f2.write(line)
			else:
				break
	
	# Convert partitions to XML
	subprocess.call(['python partitions-to-xml.py {0}/{1}.cp-homo.part.{2} {0}/{1}.map.{2}.xml {0}/{1}.xml'.format(
		args.outputfolder,
		args.topname,
		num_processors)], shell=True)

elif args.partitioner=='pagrid':
	if args.pagridplatform is None:
		print ('Must provide the PaGrid platform file for partitioning a synthetic application with PaGrid')
		sys.exit()
	else:
		for line in open(args.pagridplatform):
			print(line,line.split()[0])
			if not line.startswith('%'):
				num_processors = line.split()[0]
				break

	# Invoke Pagrid
	print ('Partioning with Pagrid...')
	subprocess.call(['pagrid {0}/{1}.metis {2}'.format(args.outputfolder,args.topname,args.pagridplatform)], shell=True)

	# Convert the partitions to XML
	subprocess.call(['python partitions-to-xml.py {1}.metis.{3}.result {0}/{1}.map.{2}.xml {0}/{1}.xml'.format(
		args.outputfolder,
		args.topname,
		num_processors,
		basename(args.pagridplatform))], shell=True)

elif args.partitioner=='cp-hetero':
	if args.heteroplatform is None:
		print ('Must provide the CP-based heterogeneous platform file for partitioning a synthetic application with Minizinc')
		sys.exit()
	else:
		for line in open(args.heteroplatform):
			if not line.startswith('%'):
				num_processors = line.split()[0]
				break

	# Convert graph to the Zinc data file
	print ('Converting to the Zinc application data format...')
	subprocess.call(['python sdf3-to-dzn.py {0}/{1}.xml {0}/app-{1}.dzn'.format(args.outputfolder,args.topname)], shell=True)

	# Generate platform Zinc data file
	subprocess.call(['python grid-to-dzn.py {2} {0}/plat-{1}.dzn'.format(args.outputfolder,num_processors,args.heteroplatform)], shell=True)

	# Invoke Minizinc for Heterogeneous Partitioning
	print ('Invoking the MiniZinc CP model for heterogeneous partitioning...')
	subprocess.call([MINIZINC_PATH+'minizinc --solver OR-Tools ../minizinc/partitioning-heterogeneous.mzn {0}/app-{1}.dzn {0}/plat-{2}.dzn -o {0}/{1}.cp-hetero.part.{2}-raw -p 8 -t 30000'.format(args.outputfolder,args.topname,num_processors)], shell=True)

	# strip the last two lines
	with open('{0}/{1}.cp-hetero.part.{2}-raw'.format(args.outputfolder,args.topname,num_processors)) as f1:
		lines = f1.readlines()
	with open('{0}/{1}.cp-hetero.part.{2}'.format(args.outputfolder,args.topname,num_processors), 'w') as f2:
		for line in lines:
			if not (line.startswith('-') or line.startswith('=')):
				f2.write(line)
			else:
				break

	# Convert partitions to XML
	subprocess.call(['python partitions-to-xml.py {0}/{1}.cp-hetero.part.{2} {0}/{1}.map.{2}.xml {0}/{1}.xml'.format(
		args.outputfolder,
		args.topname,
		num_processors)], shell=True)

# Convert the sequential model to ForSyDe-XML
print ('Converting the model to ForSyDe-XML...')
subprocess.call(['python sdf3-to-forsyde.py {0}/{1}.xml {0}/forsyde_{1}.xml'.format(args.outputfolder,args.topname)], shell=True)

# Partition the model
print ('Partitioning the model...')
subprocess.call(['mkdir -p {0}/{1}.map.{2}'.format(args.outputfolder,args.topname,num_processors)], shell=True)
subprocess.call(['python partition-forsyde.py {0}/forsyde_{1}.xml {2} {0}/{1}.map.{2}.xml {0}/{1}.map.{2}'.format(
	args.outputfolder,
	args.topname,
	num_processors)], shell=True)

# Convert the sequential model to ForSyDe-XML
print ('Converting the model to ForSyDe-XML...')
subprocess.call(['python sdf3-to-forsyde.py {0}/{1}.xml {0}/forsyde_{1}.xml'.format(args.outputfolder,args.topname)], shell=True)

# Partition the model
print ('Partitioning the model...')
subprocess.call(['mkdir -p {0}/{1}.map.{2}'.format(args.outputfolder,args.topname,num_processors)], shell=True)
subprocess.call(['python partition-forsyde.py {0}/forsyde_{1}.xml {2} {0}/{1}.map.{2}.xml {0}/{1}.map.{2}'.format(
	args.outputfolder,
	args.topname,
	num_processors)], shell=True)

# Generate SystemC projects
print ('Generating source codes for the partitioned model...')
subprocess.call(['mkdir -p {0}/{1}.map.{2}-src'.format(args.outputfolder,args.topname,num_processors)], shell=True)
copy(TEMPLATE_PATH+'/Makefile.defs','{0}/{1}.map.{2}-src/'.format(args.outputfolder,args.topname,num_processors))
copy(TEMPLATE_PATH+'/Makefile','{0}/{1}.map.{2}-src/'.format(args.outputfolder,args.topname,num_processors))
for i in range(int(num_processors)):
	subprocess.call(['mkdir -p {0}/{1}.map.{2}-src/forsyde_{1}_{3}'.format(args.outputfolder,args.topname,num_processors,i)], shell=True)
	copy(TEMPLATE_PATH+'/Makefile-sub','{0}/{1}.map.{2}-src/forsyde_{1}_{3}/Makefile'.format(args.outputfolder,args.topname,num_processors,i))
	subprocess.call(['python forsyde-systemc-codegen.py {0}/{1}.map.{2}/forsyde_{1}_{3}.xml {0}/{1}-charasteristics.xml {0}/{1}.map.{2}-src/forsyde_{1}_{3} -m -r'.format(
		args.outputfolder,
		args.topname,
		num_processors,
		i)], shell=True)

#invoke make
subprocess.call(['make -j -C {0}/{1}.map.{2}-src/'.format(args.outputfolder,args.topname,num_processors)], shell=True)

# Deploy the MPI executables
print ('Deploying the MPI executables...')
subprocess.call(['mkdir -p {0}/{1}.map.{2}-deploy'.format(args.outputfolder,args.topname,num_processors)], shell=True)
output = open('{0}/{1}.map.{2}-deploy/appfile'.format(args.outputfolder,args.topname,num_processors),'w')
for i in range(int(num_processors)):
	copy('{0}/{1}.map.{2}-src/forsyde_{1}_{3}/run.x'.format(args.outputfolder,args.topname,num_processors,i),
	'{0}/{1}.map.{2}-deploy/forsyde_{1}_{3}'.format(args.outputfolder,args.topname,num_processors,i))
	output.write('-np 1 forsyde_{0}_{1}\n'.format(args.topname,i))
output.close()

# Run the MPI job
print ('Running the MPI job...')
subprocess.call(['mpiexec --app appfile'], cwd='{0}/{1}.map.{2}-deploy'.format(args.outputfolder,args.topname,num_processors), shell=True)


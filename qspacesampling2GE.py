import argparse
import math
from os import path

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description="""
This script allows you to convert a samples.txt file generated
from the Emmanuel Caruyer's web application to a tensorXXX.dat file.
    """,
    epilog="""
link to the webapp to generate your samples.txt files :
http://www.emmanuelcaruyer.com/q-space-sampling.php

Please kindly cite the following relevant article when you use
the sampling scheme :

Emmanuel Caruyer, Christophe Lenglet, Guillermo Sapiro, Rachid Deriche.
Design of multishell sampling schemes with uniform coverage in diffusion MRI.
Magnetic Resonance in Medicine, Wiley, 2013, 69 (6), pp. 1534-1540.
http://dx.doi.org/10.1002/mrm.24736

As usual it's "AS IS" and for research only !
    """
)
parser.add_argument('samples', type=argparse.FileType('r'),
    help='Sample.txt generate from http://www.emmanuelcaruyer.com/q-space-sampling.php')
parser.add_argument('outputfile', type=str,
    help='Ouput file in the GE tensorXXX.dat format')
parser.add_argument('bvalues', nargs='+', type=float,
    help='B-Values vector separated by spaces (i.e: 1000 2000 3000). Number must match the shells in [samples]')
parser.add_argument('--overwrite',
    help='Overwrite ouput file if exist', action='store_true')
parser.add_argument('--N', type=int,
    help='Add a b=0 image every [N] volumes')

args = parser.parse_args()



if args.N == None:
    print('N is zero')
    N = -1
else:
    N = args.N

# Some verbose about the arguments
print('Arguments :')
print('-----------')
print('Samples file: {}'.format(args.samples.name))
print('Output file: {}'.format(args.outputfile))
print('bvalues: {}'.format(args.bvalues))
if N > 0 : 
    print('b=0 every: {} volumes'.format(N))
else:
    print('No additional b=0 images\n')

print('')

# Check that output file does not exist
if not args.overwrite:
    if path.exists(args.outputfile):
        print('ERROR: file {} already exist, use --overwrite if you want to erase it'.format(
            args.outputfile))
        exit(1)

# Read samples file and do some sanity check
shells = []
u_x = []
u_y = []
u_z = []
for l in args.samples.readlines():
    if l.startswith('#'):
        # Header of the file
        continue
    data = l.split()
    try:
        shells.append(int(data[0]))
    except ValueError:
        print('ERROR: samples.txt file seems wrong. Shells are not integer, please check the input file')
        exit(1)
    try:
        u_x.append(float(data[1]))
        u_y.append(float(data[2]))
        u_z.append(float(data[3]))
    except ValueError:
        print('ERROR: samples.txt file seems wrong. Vectors coordinates are not numbers, please check the input file')
        exit(1)

n_shells = len(set(shells))
n_dir = len(shells)
shell_sizes = list()
for s in range(n_shells):
	shell_sizes.append(int(shells.count(s+1)))

if len(args.bvalues) != n_shells:
    print('ERROR: found {} shells in {} and {} bvalues are provided on the command line'.format(
        n_shells, args.samples.name, len(args.bvalues)))

# Scale the diffusion gradient according to the bvalues
b_max = float(max(args.bvalues))
for i in range(n_dir):
    b = args.bvalues[shells[i]-1]/b_max

    # The norm of is probably not exactly one so we will rescale it
    norm = math.sqrt(u_x[i] * u_x[i] + u_y[i] * u_y[i] + u_z[i] * u_z[i])

    # Seems that GE reverse the x-gradient (see README.md)
    u_x[i] = - u_x[i] * math.sqrt(b) / norm
    u_y[i] = u_y[i] * math.sqrt(b) / norm
    u_z[i] = u_z[i] * math.sqrt(b) / norm


if N > 0:
    n_b0s = math.floor(n_dir / N)
    print('INFO: There are {} directions in total, and we will add {} b=0 images, giving a total of {}'.format(
    n_dir, n_b0s, n_dir + n_b0s))
else:
    n_b0s = 0

# Write the tensor.dat
j = 0
with open(args.outputfile, 'w') as f:
    # Write a small header
    f.write('# {} DWI directions distributed in {} shells\n'.format(n_dir,n_shells))
    f.write('# bvalues: {}\n'.format(args.bvalues))
    f.write('# shell sizes: {}\n'.format(shell_sizes))
    f.write('# bmax: {}\n'.format(b_max))

    if N > 0:
        f.write('# {} b=0 volumes, interspersed every {} frames\n'.format(n_b0s, N))
    else:
        f.write('# No additional b=0 images\n')
    # For convenience, and if the number of directions > 6 we write a
    # 6 b=0 directions scheme that you could use for a reverse polarity sequence.
    f.write('6\n')
    for i in range(6):
        f.write('0 0 0\n')
    f.write('{}\n'.format(n_dir + n_b0s))
    print('------------------------------')
    for i in range(n_dir):
        j = j +1
        print('{0}:\t{1:1.2f}\t{2:1.2f}\t{3:1.2f}'.format(j, u_x[i], u_y[i], u_z[i]))
        f.write('{} {} {}\n'.format(u_x[i], u_y[i], u_z[i]))
        if N > 0 and i > 0 and i % N == 0:
            j = j +1
            print('{}:\t0\t0\t0'.format(j))
            f.write('0 0 0\n')

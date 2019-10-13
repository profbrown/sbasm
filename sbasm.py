import sys
from Assembler.Assembler import Assembler


def print_usage():
	"""
	Prints the usage for this script.
	"""
	print('Usage: python sbasm.py <input file name> <output file name, default a.mif>')
	
	
if __name__ == "__main__":
	argc = len(sys.argv)
	
	if argc >= 4:
		print('ERROR: Too many arguments.')
		print_usage()
	elif argc <= 1:
		print('ERROR: Too few arguments.')
		print_usage()
	else:
		# Parse the in and out file names from the arguments.
		# Default the output filename to a.mif.
		in_filename = sys.argv[1]
		out_filename = 'a.mif'

		if argc > 2:
			out_filename = sys.argv[2]
		
		# Create the assembler and assemble.
		a = Assembler(in_filename, out_filename)
		a.assemble()

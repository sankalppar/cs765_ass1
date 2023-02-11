import argparse

parser = argparse.ArgumentParser()
parser.add_argument('n')
parser.add_argument('z0')
parser.add_argument('z1')
args = parser.parse_args()
print(args.n)

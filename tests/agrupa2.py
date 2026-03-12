#!/usr/bin/env python

"""
Docstring for agrupa1

O script deve ser invocado de acordo com a seguinte sintaxe:

    $ python agrupa1.py [-i FICHEIRO_ENTRADA] [-o FICHEIRO_SAIDA] [-n NUM]

    FICHEIRO_ENTRADA : valor por omissão -> sys.stdin
    FICHEIRO_SAIDA  : valor por omissão -> sys.stdout
    NUM : valor por omissão -> 2

    $ python agrupa1.py -i nomes_completos.txt -o resultados.txt -n 3
    $ python agrupa1.py -o grupos.txt -i nomes_completos.txt -n 3
    $ python agrupa1.py -n 3 -o grupos.txt -i nomes_completos.txt
    

"""

from argparse import ArgumentParser
from random import shuffle


def group_elements (elements: list, group_size: int) -> list[list]:



    """
    Devolve uma lista grupos aleatórios de elementos da lista ´elements´.
    A dimensao dos grupos é dada por ´group_size´. O último grupo pode ter menos elementos do que os outros.
    
    exemplos
    L1 = [10, 20, 30, 40, 50]
    L2 = group_elements(L1, 2)
    L2 => [[30, 10], [50, 20], [40]]
    """

    shuffle(elements)
    groups = []
    for i in range(0, len(elements), group_size):
        groups.append(elements[i:i + group_size])
    return groups


def main ():

    from docopt import docopt
    import sys

    doc = f"""
Groups lines from an input given by INPUT FILE.

Usage: 
    {sys.argv[0]} [-i INPUT_FILE] [-o OUTPUT_FILE] [-n NUM]
Options:
    -i INPUT_FILE, --input-file=INPUT_FILE      Path to input file 
    -o OUTPUT_FILE, --output-file=OUTPUT_FILE   Path to output file
    -n NUM, --group-size=NUM                    Group size [default: 2]
"""
    args = docopt(doc)
    print(args)

    lines = []
    in_file = open(args['--input-file'], 'rt') if args['--input-file'] else sys.stdin
    with in_file:
        for line in in_file:
            lines.append(line[:-1] if line == '\n' else line)

    groups = group_elements(lines, group_size=int(args['--group-size']))

    out_file= open(args['--output-file'], 'wt') if args['--output-file'] else sys.stdout
    with open(args['--output-file'], 'wt') as out_file:
        for group in groups:
            line = ', '.join(group)
            print(line, file=out_file)
"""
    parser = ArgumentParser(
        description="Group lines from the input given by INPUT_FILE"
    )
    parser.add_argument(
        "-i", "--input-file", 
        metavar = 'INPUT_FILE_PATH', 
        help="Path to input file"
    )
    parser.add_argument(
        "-o", "--output-file", 
        metavar = 'OUTPUT_FILE_PATH', 
        help="Path to output file",
    )
    parser.add_argument(
        "-n", "--group-size", 
        type=int, 
        default=2, 
        help="Number of lines per group",
    )   
    
    args = parser.parse_args()
    
    
        
    

    
"""

if __name__ == "__main__":
    main()
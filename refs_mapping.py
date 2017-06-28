#! /usr/bin/python3

#File hgncsymbol-uniprot-06jun2017.list was obtained from the HGNC page (http://www.genenames.org/).
#Clicked on "Downloads" tab and then selected the txt file in "protein-coding gene" Locus Group.
#File contained 19067 genes at the time. The file is then split in two files: human_genelist.txt
#contains all the entries that have a 1:1 gene:uniprot relationship, and human_genelist-exceptions.txt
#contains the remainng entries.

# Gene symbols have a maximum of 10 characters

infile = open('hgncsymbol-uniprot-06jun2017.list')
outfile1 = open('human_genelist.txt','w')
outfile2 = open('human_genelist-exceptions.txt','w')

for line in infile:
    tokens = line.split()
    l = len(tokens)
    if l == 2:
        outfile1.write('%-10s  %-6s\n' % (tokens[0], tokens[1]) )
    if l != 2:
        outfile2.write('%-10s ' % tokens[0])
        for i in range(1,l):
            outfile2.write(' %-6s' % tokens[i])
        outfile2.write('\n')


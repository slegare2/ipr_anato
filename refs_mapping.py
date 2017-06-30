#! /usr/bin/python3

# File uniprot-hproteome.tsv.gz was obtained from UniProt REST
# using script fetch_files.py.

import os
import gzip
import csv

# Choose which version of InterPro to use (must have been downloaded first
# using fetch_files.py)
ipr_version = 63
print('Extracting UniProt references and isoforms associated with InterPro version %i.' % ipr_version)

# Ensure that input fasta and tsv files are dated as expected.
dates = []
for infile in os.listdir('downloaded-files'):
    if 'uniprot-hproteome-%i' % ipr_version in infile:
        dash = infile.rindex('-')
        dot = infile.index('.')
        date = infile[dash+1:dot]
        dates.append(date)
dates_set = set(dates)
if len(dates_set) == 1:
    date_ext = list(dates_set)[0]
elif len(dates_set) > 1:
    print('A unique date is expected for uniprot-hproteome-%i fasta and tsv files.' % ipr_version)
    exit()


tsvfile = gzip.open('downloaded-files/uniprot-hproteome-%i-%s.tsv.gz' % (ipr_version, date_ext), 'rt')
fastafile = gzip.open('downloaded-files/uniprot-hproteome-%i-%s.fasta.gz' % (ipr_version, date_ext), 'rt')

outfile = gzip.open('refs_mapping-%i.xml.gz' % ipr_version, 'wt')

# Get the length of each isoform by counting the 
# number of residues in fasta entry.
isoform_lengths = {}
first = True
for line in fastafile:
    if '>sp' in line:

        if not first:
            isoform_lengths[isoform_id] = l
        first = False

        pipe = line.index('|')+1
        unpipe = line[pipe:].index('|') + pipe
        isoform_id = line[pipe:unpipe]            
        l = 0
    else:
        l += len(line) - 1
# For the last entry
isoform_lengths[isoform_id] = l


outfile.write('<mapping>\n')

reader = csv.reader(tsvfile, delimiter='\t')
first = True
for entry in reader:
    if not first: 
        uniprot_ac = entry[0]
        hgnc_symbol = entry[1]
        hgnc_synonyms = entry[2]
        hgnc_id = entry[3][:-1]
        alt_prods = entry[4]

        synonyms = hgnc_synonyms.split()
        
        # Process the "ALTERNATIVE PRODUCTS" part of entry.
        isoform_info = alt_prods.split(';')
        isoforms = []
        seq_types = []
        for field in isoform_info:
            if 'IsoId' in field:
                equal_sign = field.index('=')
                # Sometimes, there are other ids for a same isoform.
                # I just take the first it these cases.
                try:
                    coma = field.index(',')
                    isoform_id = field[equal_sign+1:coma]
                except:
                    isoform_id = field[equal_sign+1:]
                isoforms.append(isoform_id)
            if 'Sequence' in field:
                equal_sign = field.index('=')
                seq_string = field[equal_sign+1:]
                if seq_string == 'Displayed':
                    seq_types.append('canonical')
                else:
                    seq_types.append('alternative')

        # Get the length of each isoform.
        lengths = []
        for isoform in isoforms:
            try:
                l = isoform_lengths[isoform]
            except:
                dash = isoform.index('-')
                canon = isoform[:dash]
                l = isoform_lengths[canon]
            lengths.append(l)

        # Write to file in xml style.
        outfile.write('<entry uniprot_ac="%s" hgnc_symbol="%s" hgnc_id="%s"' % (uniprot_ac, hgnc_symbol, hgnc_id) )
        if len(synonyms) == 0 and len(isoforms) == 0:
            outfile.write('/>\n')
        else:
            outfile.write('>\n')
        for syn in synonyms:
            outfile.write('  <synonym>%s</synonym>\n' % syn)
        for i in range(len(isoforms)):
            outfile.write('  <isoform>\n')
            outfile.write('    <id>%s</id>\n' % isoforms[i])
            outfile.write('    <length>%s</length>\n' % lengths[i])
            outfile.write('    <type>%s</type>\n' % seq_types[i])
            outfile.write('  </isoform>\n')
        if len(synonyms) > 0 or len(isoforms) > 0:
            outfile.write('</entry>\n')

    first = False

outfile.write('</mapping>\n')

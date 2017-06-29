#! /usr/bin/python3

# Extract the reviewed entries from the InterPro file match_complete.xml.gz
# which contains the InterPro domains all UniProt entries.
#
# File match_complete.xml.gz is very large (~15Go compressed) and we do not
# know the number of lines in advance. It presumably contains ~85 millon 
# entries (the number of protein sequences in TrEMBL).

import os
import gzip
import time
import shutil


# Choose which version of InterPro to use (must have been downloaded first
# using fetch_files.py)
ipr_version = 63
print('Updating protein domain data to InterPro %i.' % ipr_version)

# Ensure that input files are as expected.
dates = []
for infile in os.listdir('downloaded-files'):
    if 'uniprot-hproteome-%i' % ipr_version in infile and 'fasta.gz' in infile:
        dash = infile.rindex('-')
        dot = infile.index('.')
        date = infile[dash+1:dot]
        dates.append(date)
dates_set = set(dates)
if len(dates_set) == 1:
    date_ext = list(dates_set)[0]
elif len(dates_set) > 1:
    print('A unique date is expected for uniprot-hproteome-%i fasta file.' % ipr_version)


# Input files.
rev_human_proteome = gzip.open('downloaded-files/uniprot-hproteome-%i-%s.fasta.gz' % (ipr_version, date_ext),'r')
complete_match_in = gzip.open('downloaded-files/match_complete-%i.xml.gz' % ipr_version,'r')

# Output files.
matchrun_out = open('interpro_swiss_run.out','w')
proteome_list = open('uniprot-entries-%i-%s.txt' % (ipr_version, date_ext),'w')
swiss_match_out = gzip.open('ipr_reviewed_human_match-%i.xml.gz' % ipr_version,'wt')


# Extract UniProt ACs from uniprot-human-proteome-02jun2017.fasta.gz.
# -------------------------------------------------------------------
n = 0
reviewed_protlist = []
for line in rev_human_proteome:
    stringline = line.decode("utf-8")
    if '>sp' in stringline:
        pipe = stringline.index('|')+1
        unpipe = stringline[pipe:].index('|') + pipe
        uniprot_ac = stringline[pipe:unpipe]
        reviewed_protlist.append(uniprot_ac)

# Sort ACs so that they are in the same order as in match_complete.xml.gz.
sorted_protlist = sorted(reviewed_protlist)

# Print sorted list of ACs to file.
for uniprot_ac in sorted_protlist:
        n += 1
        proteome_list.write('%5i %s\n' % (n, uniprot_ac) )
proteome_list.close()
print('Searching for %i reviewed entries in match_complete.xml.gz' % n)
# -------------------------------------------------------------------


# Useful variables.
n = 0
pos = 0
sublist_ind = 0
sublist_size = 4
writeit = False
starttime = time.time()

sublist = sorted_protlist[sublist_ind:sublist_ind + sublist_size]

# Element Tree expects xml files to have a single root tag.
swiss_match_out.write('<interpromatch>\n')

# Loop over file match_complete.xml.gz.
for line in complete_match_in:
    stringline = line.decode("utf-8") 

    # Find UniProt AC in match_complete.xml.gz lines.
    if '<protein id=' in stringline:
        quote = stringline.index('"')+1
        unquote = stringline[quote:].index('"') + quote
        uniprot_ac = stringline[quote:unquote]

        # Check if AC is in the UniProt reviewed human genome.
        # If so, start writing entry to output file.
        if uniprot_ac in sublist:
            n += 1
            acfound = 'Found reviewed UniProt Accession %i: %s %s'%(n,uniprot_ac,sublist)
            print(acfound)
            matchrun_out.write('%s\n' % (acfound) )
            writeit = True

            # Check if AC was the first element of sublist.
            # Otherwise, that means a reviewed entry is missing or 
            # incorrectly ordered in match_complete.xml.gz.
            ac_index = sublist.index(uniprot_ac)
            if ac_index != 0:
                print('AC ', end='')
                matchrun_out.write('AC ')
                for i in range(ac_index):
                    print('%s' % sublist[i], end='')
                    matchrun_out.write('%s' % sublist[i] )
                print(' were skipped. %s' % sublist)
                matchrun_out.write('were skipped. %s\n' % sublist)
            
            # Update sublist.
            sublist_ind += 1 + ac_index
            sublist = sorted_protlist[sublist_ind:sublist_ind + sublist_size]

    if writeit:
        swiss_match_out.write('%s' %(stringline) )

    # Entry stops with the line containing string '</protein>'.
    if '</protein>' in stringline:
        writeit = False

    # Print progress.
    pos += 1
    if pos%10000000 == 0:
        t = time.time() - starttime
        progress = ('%iM lines parsed in %is, %i AC found. '
                    'Searching for %s' 
                    % (pos/1000000, t, n, ' '.join(sublist) )
        )
        print(progress)
        matchrun_out.write('%s\n' %(progress) )

swiss_match_out.write('</interpromatch>\n')

# Make a copy of the generated file, since it took so long.
shutil.copyfile('ipr_reviewed_human_match-%i.xml' % ipr_version, 
                'ipr_reviewed_human_match-%i-copy.xml' % ipr_version)


#! /usr/bin/python3

# Send the latest version of refs_mapping.xml.gz, ipr_shortnames.xml.gz
# and ipr_reviewed_human_match.xml.gz to ENS personnal page using lftp.

import os
import urllib.request
import ipr_updater as ipru
import lxml.html
from lxml import etree

# Local directory where custom files were written by update_ipr.py. 
writedir = 'anatomizer_ipr_files'
# Remote directory where files are stored to be available for download.
ftpdir = 'anatomizer_ipr_files'


def remote_version(file_list):
    """ 
    Check the latest version of a list of files.
    """
    match_versions = []
    for file_name in file_list:
       # Find version as first series of int characters.
       start = 0
       for i in range(len(file_name)):
           try:
               x = int(file_name[i])
               start = i-1
           except:
               pass

           if start > 0:
               try:
                   x = int(file_name[i])
               except:
                   end = i
                   break

       version = int(file_name[start:end])
       match_versions.append(version)
    if len(match_versions) > 0:
        sorted_versions = sorted(match_versions)
        rem_version = sorted_versions[-1]
    else:
        rem_version = 0

    return rem_version


# Find latest version of InterPro files on local directory "writedir".
# ---------------------------------------------------------------------------
mapping_version = ipru.local_version(writedir,
                                     'refs_mapping-', 'xml.gz')

shortname_version = ipru.local_version(writedir,
                                       'ipr_shortnames-', 'xml.gz')

match_version = ipru.local_version(writedir,
                                   'ipr_reviewed_human_match-',
                                   'xml.gz', 'copy')

if mapping_version != shortname_version or mapping_version != match_version:
    raise ipru.IprUpdaterError('Latest version of each file does not match.')
# ---------------------------------------------------------------------------


# Find latest version of InterPro files on remote site perso.ens-lyon.fr
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
enspage = urllib.request.urlopen('http://perso.ens-lyon.fr/sebastien.legare/%s/' % ftpdir)
content = enspage.read()
tree = lxml.etree.HTML(content)
entries = tree.findall('.//a')

mapping_files = []
shortname_files = []
match_files = []
for entry in entries:
    field = entry.text
    if 'refs_mapping-' in field and 'xml.gz' in field:
        mapping_files.append(field)
    if 'ipr_shortnames-' in field and 'xml.gz' in field:
        shortname_files.append(field)
    if 'ipr_reviewed_human_match-' in field and 'xml.gz' in field:
        match_files.append(field)

rem_mapping_version = remote_version(mapping_files)
rem_shortname_version = remote_version(shortname_files)
rem_match_version = remote_version(match_files)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Build lftp command line.
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
cmd_string = "lftp -u slegare perso.ens-lyon.fr -e 'cd %s;" % ftpdir

# Ask user if he wants to overwrite existing files on remote site.
# refs_mapping
send = False

exist = False
ask = 'n'
overwrite = False
if rem_mapping_version == mapping_version:
    exist = True
    ask = input('file refs_mapping-%i.xml.gz already exists on remote. Overwrite it? [y/N] ' % mapping_version)
    if ask.lower() == 'y' or ask.lower() == 'yes':
        overwrite = True
if not exist or overwrite:
    cmd_string = cmd_string + """ echo "transfering refs_mapping-%i.xml.gz"; """ % mapping_version
    cmd_string = cmd_string + " put %s/refs_mapping-%i.xml.gz;" % (writedir, mapping_version)
    send = True

# ipr_shortnames
exist = False
ask = 'n'
overwrite = False
if rem_shortname_version == shortname_version:
    exist = True
    ask = input('file ipr_shortnames-%i.xml.gz already exists on remote. Overwrite it? [y/N] ' % shortname_version)
if ask.lower() == 'y' or ask.lower() == 'yes':
    overwrite = True
if not exist or overwrite:
    cmd_string = cmd_string + """ echo "transfering ipr_shortnames-%i.xml.gz"; """ % shortname_version
    cmd_string = cmd_string + " put %s/ipr_shortnames-%i.xml.gz;" % (writedir, shortname_version)
    send = True

# ipr_reviewed_human_match
exist = False
ask = 'n'
overwrite = False
if rem_match_version == match_version:
    exist = True
    ask = input('file ipr_reviewed_human_match-%i.xml.gz already exists on remote. Overwrite it? [y/N] ' % match_version)
if ask.lower() == 'y' or ask.lower() == 'yes':
    overwrite = True
if not exist or overwrite:
    cmd_string = cmd_string + """ echo "transfering ipr_reviewed_human_match-%i.xml.gz"; """ % match_version
    cmd_string = cmd_string + " put %s/ipr_reviewed_human_match-%i.xml.gz;" % (writedir, match_version)
    send = True

cmd_string = cmd_string + " quit'"
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# Run lftp
if send:
    os.system(cmd_string)


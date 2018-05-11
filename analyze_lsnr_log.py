#!/usr/bin/python

'''
A script to analyze the Oracle listener log
'''

import re
import os
import os.path
from datetime import datetime
from optparse import OptionParser

# process command line options
parser = OptionParser(usage="usage: %%prog\n%s" % __doc__)
parser.add_option("-f", "--file", dest="filename",
						default = None,
						help = "Name of the listener logfile. When specified, we won't attempt to query the running listener process.")

(options, args) = parser.parse_args()
lsnr_log_file = options.filename

if lsnr_log_file is None :
	# get the listener log, if not specified as a command line argument
	lsnr_stat = os.popen("lsnrctl status").read().rstrip()
	lsnr_log_line_search = re.search(r'Listener Log File.*$', lsnr_stat, re.M|re.I)
	if lsnr_log_line_search is None:
		# can't find 'Listener Log File'
		print
		print "Cannot find 'Listener Log File' entry in 'lsnrctl status' output"
		print "'lsnrctl status' output is:"
		print
		print lsnr_stat
		exit(1)
	
	lsnr_log_line = lsnr_log_line_search.group()
	lsnr_log_file = re.sub(r'Listener Log File *','',lsnr_log_line)
	if re.search(r'\.xml$', lsnr_log_file, re.M|re.I):
		# file is xml, replace the "alert" with "trace" and the "log.xml" with "listener.log"
		lsnr_log_file = lsnr_log_file.replace('log.xml','listener.log').replace("alert","trace")

if not os.path.isfile(lsnr_log_file):
	print
	print "Listener log should be: " + lsnr_log_file
	print "But file does not exist"
	exit(1)

lsnrf = open(lsnr_log_file,"r")

# variables
line_count=0
dict_program = {}
col_width = 25

print
print "Analyzing log: " + lsnr_log_file + "..."

# process the log
for line in lsnrf:
		if "* establish *" in line:
				line_date = line.split("*")[0].split(" ")[0]
				line_datef = datetime.strptime(line_date,"%d-%b-%Y")
				line_connectdata = line.split("*")[1]
				line_address = line.split("*")[1]
				data_search = re.search(r'PROGRAM=[^\)]*', line_connectdata, re.M|re.I)
				if data_search is not None:
						line_prog = data_search.group().split("=")[1].split("\\")[-1]
                                                if line_prog == "" : line_prog = "*UNSPECIFIED*"
						if line_prog != "null":
								try:
										dict_program[line_datef,line_prog] += 1
								except KeyError:
										dict_program[line_datef,line_prog] = 1
								line_count +=1
lsnrf.close

print "done"

# preparing output
all_keys = dict_program.keys()
date_list = sorted(list(set([k[0] for k in all_keys])))
prog_list = sorted(list(set([k[1] for k in all_keys])))

# print output
print 
print "Please choose from the following output options:"
print "1. csv format"
print "2. text table format"
output_format = raw_input()

print
print "Connection Analysis"
print "==================="
print "First date in log:                ", date_list[0].strftime("%Y-%m-%d")
print "Last date in log:                 ", date_list[-1].strftime("%Y-%m-%d")
print "Number of connections in the log: ", line_count
print
print "Connection distribution per day:"
print "================================"
print 

if output_format == "1":
	print "Date",
	for p in prog_list:
		print "," + p,
	print
	for d in date_list:
		print d.strftime("%Y-%m-%d"),
		for p in prog_list:
			if dict_program.get((d, p), None):
				print "," + str(dict_program[d,p]),
			else:
				print ",",
		print
elif output_format == "2":
	for i in range(len(prog_list)+1):
		print "|".ljust(col_width + 2,"="),
	print "|"
	print "| Date".ljust(col_width + 2),
	for p in prog_list:
		print "| " + p.ljust(col_width)[:col_width],
	print "|"
	for i in range(len(prog_list)+1):
		print "|=".ljust(col_width + 2,"="),
	print "|"
	for d in date_list:
		print "| " + d.strftime("%Y-%m-%d").ljust(col_width)[:col_width],
		for p in prog_list:
			if dict_program.get((d, p), None):
				print "| " + str(dict_program[d,p]).ljust(col_width)[:col_width],
			else:
				print "|".ljust(col_width + 2),
		print "|"
	for i in range(len(prog_list)+1):
		print "|".ljust(col_width + 2,"="),
print "|"

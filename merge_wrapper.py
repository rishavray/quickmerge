#!/usr/bin/env python
import subprocess
import sys
import argparse

#Required:
#the 'nucmer','delta-filter', and 'merger' executables must be in the user's PATH

parser = argparse.ArgumentParser(description = 'run mummer and the merge program.')
parser.add_argument("hybrid_assembly_fasta", help="the output of a hybrid assembly program such as DBG2OLC")
parser.add_argument("self_assembly_fasta",help="the output of a self assembly program such as PBcR")
parser.add_argument("-pre","--prefix", help="the prefix for all output files")
parser.add_argument("-hco","--hco", help="the quickmerge hco parameter (default=5.0)")
parser.add_argument("-c","--c", help="the quickmerge c parameter (default=1.5)")
parser.add_argument("-l","--length_cutoff", help="minimum seed contig length to be merged (default=0)")
parser.add_argument("--no_nucmer", help="skip the nucmer step",action="store_true")
parser.add_argument("--no_delta", help="skip the nucmer and delta-filter steps",action="store_true")
parser.add_argument("--stop_after_nucmer", help="do not perform the delta-filter and merger steps",action="store_true")
parser.add_argument("--stop_after_df", help="do not perform the merger step",action="store_true")
parser.add_argument("-lm", "--length_minimum", help="set the minimum alignment length necessary for use in quickmerge (default 0)")
parser.add_argument("--clean_only", help="generate safe FASTA files for merging, but do not merge",action="store_true")
parser.add_argument("-t", help="Number of threads to use for E-MEM. default = 1",action="store_true")

args=parser.parse_args()
if args.prefix:
    prefix = args.prefix
else:
    prefix = "out"
hypath = args.hybrid_assembly_fasta
selfpath = args.self_assembly_fasta
if args.t:
    threads = args.t
else:
    threads = 1
if args.hco:
    hco = args.hco
else:
    hco = 5.0
if args.c:
    c = args.c
else:
    c = 1.5
if args.length_cutoff:
    length_cutoff = args.length_cutoff
else:
    length_cutoff = 0
if args.length_minimum:
    length_minimum = args.length_minimum
else:
    length_minimum = 0


##define functions:
def test_for_namedups(connection1,connection2):
    ok1=True
    ok2=True
    names = set()
    badnames = {}
    for line in connection1:
        if line[0] == ">":
            line = line.rstrip('\n')
            name = "_".join(line[1:].split(" "))
            if not name in names:
                names.add(name)
            else:
                ok1 = False
                badnames[name] = 0
    for line in connection2:
        if line[0] == ">":
            line = line.rstrip('\n')
            name = line[1:].join(line[1:].split(" "))
            if not name in names:
                names.add(name)
            else:
                ok2 = False
                badnames[name] = 0
    return([ok1,ok2,names,badnames])

def fix_namedup(name):
    global badnames
    if name not in badnames:
        return(name)
    else:
        badnames[name] += 1
        newname = str(name) + "." + str(badnames[name])
        while newname in badnames or newname in names:
            badnames[name] += 1
            newname = str(name) + "." + str(badnames[name])
        return(newname)

#check for fasta header compatibility:
testpaths = [str(hypath),str(selfpath)]
order = ["hybrid","self"]

a = test_for_namedups(open(testpaths[0],"r"),open(testpaths[1],"r"))
ok1 = a[0]
ok2 = a[1]
names = a[2]
badnames = a[3]

#check for fasta line compatibility and uppercase compatibility:
for iteration in range(0,2):
    file = testpaths[iteration]
    with open(file,"r") as tfile:
        i = 0
        ok = True
        for linea in tfile:
            line = linea.rstrip('\n')
            if i % 2 == 0 and line[0] != ">": ok = False
            if " " in line: ok = False
            if line[0] != ">" and not line.isupper(): ok = False
            i += 1



        #if fasta isn't compatible, make oneline version of fasta:
        if not ok:
            tfile.seek(0)
            tempoutpath = order[iteration] + "_oneline.fa"
            with open(tempoutpath,"w") as tout:
                header = ""
                seq = ""
                for linea in tfile:
                    line = linea.rstrip('\n')
                    #print line # debug line
                    if line[0] == ">":
                        #print line # debug line
                        if len(header) > 0 and len(seq) > 0:
                            if not ok1 or not ok2:
                                header_out = ">" + str(fix_namedup(header[1:]))
                            else:
                                header_out = header
                            tout.write(header_out + "\n" + seq.upper() + "\n")
                        if not " " in line:
                            header = line
                        else:
                            header = "_".join(map(str,line.split(" ")))
                        seq = ""
                    else:
                        seq = seq + line
                if not ok1 or not ok2:
                    header_out = ">" + str(fix_namedup(header[1:]))
                else:
                    header_out = header
                tout.write(header_out + "\n" + seq.upper() + "\n")
            #change hypath and selfpath to use the temporary (oneline) fastas:
            if iteration == 0:
                hypath = tempoutpath
            else:
                selfpath = tempoutpath
            

#run nucmer:
if not args.no_nucmer and not args.no_delta and not args.clean_only:
    subprocess.call(['nucmer','-t',str(threads),'-l','100','-prefix',str(prefix),str(selfpath),str(hypath)])

#run the delta filter on the nucmer alignment:
if not args.no_delta and not args.stop_after_nucmer and not args.clean_only:
    with open(str(str(prefix)+'.rq.delta'), "w") as outfile:
        subprocess.call(['delta-filter','-i','95','-r','-q',str(str(prefix)+'.delta')],stdout=outfile)

#append the correct options to the merger call:
mergercall = ['quickmerge','-d',str(str(prefix)+'.rq.delta'),'-q',str(hypath),'-r',str(selfpath)]
#if args.hco:
mergercall.append('-hco')
mergercall.append(str(hco))
#if args.c:
mergercall.append('-c')
mergercall.append(str(c))
#if args.length_cutoff:
mergercall.append('-l')
mergercall.append(str(length_cutoff))
#if args.length_minimum:
mergercall.append('-lm')
mergercall.append(str(length_minimum))

#run the merging program
if not args.stop_after_nucmer and not args.stop_after_df and not args.clean_only:
    subprocess.call(mergercall)


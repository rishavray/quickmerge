#!/bin/bash
cd example
../MUMmer3.23/nucmer -t 2 -l 100 -prefix out  S1.fasta S2.fasta
../MUMmer3.23/delta-filter -i 95 -r -q out.delta > out.rq.delta
../quickmerge -d out.rq.delta -q S2.fasta -r S1.fasta -hco 5.0 -c 1.5 -l n -ml m -o merge.fasta

#!/usr/bin/env bash

###
echo "testing cutRelationCrisp..."
cd cutRelationCrisp

./cutRelationCrisp.py -i tests/in1 -o tests
diff -s tests/outranking.xml tests/out1/outranking.xml > /dev/null
e1=$?
diff -s tests/messages.xml tests/out1/messages.xml > /dev/null
e2=$?
if [[ $e1 != 0 || $e2 != 0 ]]; then echo "error!"; else echo "ok"; fi
rm tests/outranking.xml && rm tests/messages.xml

./cutRelationCrisp.py -i tests/in2 -o tests
diff -s tests/outranking.xml tests/out2/outranking.xml > /dev/null
e1=$?
diff -s tests/messages.xml tests/out2/messages.xml > /dev/null
e2=$?
if [[ $e1 != 0 || $e2 != 0 ]]; then echo "error!"; else echo "ok"; fi
rm tests/outranking.xml && rm tests/messages.xml

###
echo "testing ElectreConcordance..."
cd ../ElectreConcordance

./ElectreConcordance.py -i tests/in1 -o tests
diff -s tests/concordance.xml tests/out1/concordance.xml > /dev/null
e1=$?
diff -s tests/messages.xml tests/out1/messages.xml > /dev/null
e2=$?
if [[ $e1 != 0 || $e2 != 0 ]]; then echo "error!"; else echo "ok"; fi
rm tests/concordance.xml && rm tests/messages.xml

./ElectreConcordance.py -i tests/in2 -o tests
diff -s tests/concordance.xml tests/out2/concordance.xml > /dev/null
e1=$?
diff -s tests/messages.xml tests/out2/messages.xml > /dev/null
e2=$?
if [[ $e1 != 0 || $e2 != 0 ]]; then echo "error!"; else echo "ok"; fi
rm tests/concordance.xml && rm tests/messages.xml

###
echo "testing ElectreConcordanceWithInteractions..."
cd ../ElectreConcordanceWithInteractions

./ElectreConcordanceWithInteractions.py -i tests/in -o tests
diff -s tests/concordance.xml tests/out/concordance.xml > /dev/null
e1=$?
diff -s tests/messages.xml tests/out/messages.xml > /dev/null
e2=$?
if [[ $e1 != 0 || $e2 != 0 ]]; then echo "error!"; else echo "ok"; fi
rm tests/concordance.xml && rm tests/messages.xml

###
echo "testing ElectreCredibility..."
cd ../ElectreCredibility

./ElectreCredibility.py -i tests/in1 -o tests
diff -s tests/credibility.xml tests/out1/credibility.xml > /dev/null
e1=$?
diff -s tests/messages.xml tests/out1/messages.xml > /dev/null
e2=$?
if [[ $e1 != 0 || $e2 != 0 ]]; then echo "error!"; else echo "ok"; fi
rm tests/credibility.xml && rm tests/messages.xml

./ElectreCredibility.py -i tests/in2 -o tests
diff -s tests/credibility.xml tests/out2/credibility.xml > /dev/null
e1=$?
diff -s tests/messages.xml tests/out2/messages.xml > /dev/null
e2=$?
if [[ $e1 != 0 || $e2 != 0 ]]; then echo "error!"; else echo "ok"; fi
rm tests/credibility.xml && rm tests/messages.xml

./ElectreCredibility.py -i tests/in3 -o tests
diff -s tests/credibility.xml tests/out3/credibility.xml > /dev/null
e1=$?
diff -s tests/messages.xml tests/out3/messages.xml > /dev/null
e2=$?
if [[ $e1 != 0 || $e2 != 0 ]]; then echo "error!"; else echo "ok"; fi
rm tests/credibility.xml && rm tests/messages.xml

###
echo "testing ElectreDiscordance..."
cd ../ElectreDiscordance

./ElectreDiscordance.py -i tests/in1 -o tests
diff -s tests/discordance.xml tests/out1/discordance.xml > /dev/null
e1=$?
diff -s tests/messages.xml tests/out1/messages.xml > /dev/null
e2=$?
if [[ $e1 != 0 || $e2 != 0 ]]; then echo "error!"; else echo "ok"; fi
rm tests/discordance.xml && rm tests/messages.xml

./ElectreDiscordance.py -i tests/in2 -o tests
diff -s tests/discordance.xml tests/out2/discordance.xml > /dev/null
e1=$?
diff -s tests/messages.xml tests/out2/messages.xml > /dev/null
e2=$?
if [[ $e1 != 0 || $e2 != 0 ]]; then echo "error!"; else echo "ok"; fi
rm tests/discordance.xml && rm tests/messages.xml

###
echo "testing ElectreIsDiscordanceBinary..."
cd ../ElectreIsDiscordanceBinary

./ElectreIsDiscordanceBinary.py -i tests/in -o tests
diff -s tests/discordance.xml tests/out/discordance.xml > /dev/null
e1=$?
diff -s tests/messages.xml tests/out/messages.xml > /dev/null
e2=$?
if [[ $e1 != 0 || $e2 != 0 ]]; then echo "error!"; else echo "ok"; fi
rm tests/discordance.xml && rm tests/messages.xml

###
echo "testing ElectreIsFindKernel..."
cd ../ElectreIsFindKernel

./ElectreIsFindKernel.py -i tests/in1 -o tests
diff -s tests/kernel.xml tests/out1/kernel.xml > /dev/null
e1=$?
diff -s tests/messages.xml tests/out1/messages.xml > /dev/null
e2=$?
if [[ $e1 != 0 || $e2 != 0 ]]; then echo "error!"; else echo "ok"; fi
rm tests/kernel.xml && rm tests/messages.xml

./ElectreIsFindKernel.py -i tests/in2 -o tests
diff -s tests/kernel.xml tests/out2/kernel.xml > /dev/null
e1=$?
diff -s tests/messages.xml tests/out2/messages.xml > /dev/null
e2=$?
if [[ $e1 != 0 || $e2 != 0 ]]; then echo "error!"; else echo "ok"; fi
rm tests/kernel.xml && rm tests/messages.xml

###
echo "testing ElectreIVCredibility..."
cd ../ElectreIVCredibility

./ElectreIVCredibility.py -i tests/in1 -o tests
diff -s tests/credibility.xml tests/out1/credibility.xml > /dev/null
e1=$?
diff -s tests/messages.xml tests/out1/messages.xml > /dev/null
e2=$?
if [[ $e1 != 0 || $e2 != 0 ]]; then echo "error!"; else echo "ok"; fi
rm tests/credibility.xml && rm tests/messages.xml

./ElectreIVCredibility.py -i tests/in2 -o tests
diff -s tests/credibility.xml tests/out2/credibility.xml > /dev/null
e1=$?
diff -s tests/messages.xml tests/out2/messages.xml > /dev/null
e2=$?
if [[ $e1 != 0 || $e2 != 0 ]]; then echo "error!"; else echo "ok"; fi
rm tests/credibility.xml && rm tests/messages.xml

###
echo "testing ElectreTri-CClassAssignments..."
cd ../ElectreTri-CClassAssignments

./ElectreTri-CClassAssignments.py -i tests/in -o tests
diff -s tests/assignments.xml tests/out/assignments.xml > /dev/null
e1=$?
diff -s tests/messages.xml tests/out/messages.xml > /dev/null
e2=$?
if [[ $e1 != 0 || $e2 != 0 ]]; then echo "error!"; else echo "ok"; fi
rm tests/assignments.xml && rm tests/messages.xml

###
echo "testing ElectreTriClassAssignments..."
cd ../ElectreTriClassAssignments

./ElectreTriClassAssignments.py -i tests/in -o tests
diff -s tests/assignments_conjuctive.xml tests/out/assignments_conjuctive.xml > /dev/null
e1=$?
diff -s tests/assignments_disjunctive.xml tests/out/assignments_disjunctive.xml > /dev/null
e2=$?
diff -s tests/messages.xml tests/out/messages.xml > /dev/null
e3=$?
if [[ $e1 != 0 || $e2 != 0 || $e3 != 0 ]]; then echo "error!"; else echo "ok"; fi
rm tests/assignments_conjuctive.xml && rm tests/assignments_disjunctive.xml && rm tests/messages.xml

###
echo "testing ElectreTri-rCClassAssignments..."
cd ../ElectreTri-rCClassAssignments

./ElectreTri-rCClassAssignments.py -i tests/in -o tests
diff -s tests/assignments.xml tests/out/assignments.xml > /dev/null
e1=$?
diff -s tests/messages.xml tests/out/messages.xml > /dev/null
e2=$?
if [[ $e1 != 0 || $e2 != 0 ]]; then echo "error!"; else echo "ok"; fi
rm tests/assignments.xml && rm tests/messages.xml

cd ..

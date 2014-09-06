#!/usr/bin/env bash
set -e

###
echo "testing cutRelationCrisp..."
cd cutRelationCrisp

./cutRelationCrisp.py -i tests/in1 -o tests
diff -s tests/outranking.xml tests/out1/outranking.xml > /dev/null
diff -s tests/messages.xml tests/out1/messages.xml > /dev/null
rm tests/outranking.xml && rm tests/messages.xml
echo "ok"

./cutRelationCrisp.py -i tests/in2 -o tests
diff -s tests/outranking.xml tests/out2/outranking.xml > /dev/null
diff -s tests/messages.xml tests/out2/messages.xml > /dev/null
rm tests/outranking.xml && rm tests/messages.xml
echo "ok"

./cutRelationCrisp.py -i tests/in3 -o tests
diff -s tests/outranking.xml tests/out3/outranking.xml > /dev/null
diff -s tests/messages.xml tests/out3/messages.xml > /dev/null
rm tests/outranking.xml && rm tests/messages.xml
echo "ok"

###
echo "testing ElectreConcordance..."
cd ../ElectreConcordance

./ElectreConcordance.py -i tests/in1 -o tests
diff -s tests/concordance.xml tests/out1/concordance.xml > /dev/null
diff -s tests/messages.xml tests/out1/messages.xml > /dev/null
rm tests/concordance.xml && rm tests/messages.xml
echo "ok"

./ElectreConcordance.py -i tests/in2 -o tests
diff -s tests/concordance.xml tests/out2/concordance.xml > /dev/null
diff -s tests/messages.xml tests/out2/messages.xml > /dev/null
rm tests/concordance.xml && rm tests/messages.xml
echo "ok"

./ElectreConcordance.py -i tests/in3 -o tests
diff -s tests/concordance.xml tests/out3/concordance.xml > /dev/null
diff -s tests/messages.xml tests/out3/messages.xml > /dev/null
rm tests/concordance.xml && rm tests/messages.xml
echo "ok"

###
echo "testing ElectreConcordanceReinforcedPreference..."
cd ../ElectreConcordanceReinforcedPreference

./ElectreConcordanceReinforcedPreference.py -i tests/in -o tests
diff -s tests/concordance.xml tests/out/concordance.xml > /dev/null
diff -s tests/messages.xml tests/out/messages.xml > /dev/null
rm tests/concordance.xml && rm tests/messages.xml
echo "ok"

###
echo "testing ElectreConcordanceWithInteractions..."
cd ../ElectreConcordanceWithInteractions

./ElectreConcordanceWithInteractions.py -i tests/in -o tests
diff -s tests/concordance.xml tests/out/concordance.xml > /dev/null
diff -s tests/messages.xml tests/out/messages.xml > /dev/null
rm tests/concordance.xml && rm tests/messages.xml
echo "ok"

###
echo "testing ElectreCredibility..."
cd ../ElectreCredibility

./ElectreCredibility.py -i tests/in1 -o tests
diff -s tests/credibility.xml tests/out1/credibility.xml > /dev/null
diff -s tests/messages.xml tests/out1/messages.xml > /dev/null
rm tests/credibility.xml && rm tests/messages.xml
echo "ok"

./ElectreCredibility.py -i tests/in2 -o tests
diff -s tests/credibility.xml tests/out2/credibility.xml > /dev/null
diff -s tests/messages.xml tests/out2/messages.xml > /dev/null
rm tests/credibility.xml && rm tests/messages.xml
echo "ok"

./ElectreCredibility.py -i tests/in3 -o tests
diff -s tests/credibility.xml tests/out3/credibility.xml > /dev/null
diff -s tests/messages.xml tests/out3/messages.xml > /dev/null
rm tests/credibility.xml && rm tests/messages.xml
echo "ok"

./ElectreCredibility.py -i tests/in4 -o tests
diff -s tests/credibility.xml tests/out4/credibility.xml > /dev/null
diff -s tests/messages.xml tests/out4/messages.xml > /dev/null
rm tests/credibility.xml && rm tests/messages.xml
echo "ok"

###
echo "testing ElectreCredibilityWithCounterVeto..."
cd ../ElectreCredibilityWithCounterVeto

./ElectreCredibilityWithCounterVeto.py -i tests/in -o tests
diff -s tests/credibility.xml tests/out/credibility.xml > /dev/null
diff -s tests/messages.xml tests/out/messages.xml > /dev/null
rm tests/credibility.xml && rm tests/messages.xml
echo "ok"

###
echo "testing ElectreDiscordance..."
cd ../ElectreDiscordance

./ElectreDiscordance.py -i tests/in1 -o tests
diff -s tests/discordance.xml tests/out1/discordance.xml > /dev/null
diff -s tests/messages.xml tests/out1/messages.xml > /dev/null
diff -s tests/counter_veto_crossed.xml tests/out1/counter_veto_crossed.xml > /dev/null
rm tests/discordance.xml && rm tests/messages.xml && rm tests/counter_veto_crossed.xml
echo "ok"

./ElectreDiscordance.py -i tests/in2 -o tests
diff -s tests/discordance.xml tests/out2/discordance.xml > /dev/null
diff -s tests/messages.xml tests/out2/messages.xml > /dev/null
diff -s tests/counter_veto_crossed.xml tests/out2/counter_veto_crossed.xml > /dev/null
rm tests/discordance.xml && rm tests/messages.xml && rm tests/counter_veto_crossed.xml
echo "ok"

./ElectreDiscordance.py -i tests/in3 -o tests
diff -s tests/discordance.xml tests/out3/discordance.xml > /dev/null
diff -s tests/messages.xml tests/out3/messages.xml > /dev/null
diff -s tests/counter_veto_crossed.xml tests/out3/counter_veto_crossed.xml > /dev/null
rm tests/discordance.xml && rm tests/messages.xml && rm tests/counter_veto_crossed.xml
echo "ok"

./ElectreDiscordance.py -i tests/in4 -o tests
diff -s tests/discordance.xml tests/out4/discordance.xml > /dev/null
diff -s tests/messages.xml tests/out4/messages.xml > /dev/null
diff -s tests/counter_veto_crossed.xml tests/out4/counter_veto_crossed.xml > /dev/null
rm tests/discordance.xml && rm tests/messages.xml && rm tests/counter_veto_crossed.xml
echo "ok"

###
echo "testing ElectreIsDiscordanceBinary..."
cd ../ElectreIsDiscordanceBinary

./ElectreIsDiscordanceBinary.py -i tests/in -o tests
diff -s tests/discordance.xml tests/out/discordance.xml > /dev/null
diff -s tests/messages.xml tests/out/messages.xml > /dev/null
rm tests/discordance.xml && rm tests/messages.xml
echo "ok"

###
echo "testing ElectreIsFindKernel..."
cd ../ElectreIsFindKernel

./ElectreIsFindKernel.py -i tests/in1 -o tests
diff -s tests/kernel.xml tests/out1/kernel.xml > /dev/null
diff -s tests/messages.xml tests/out1/messages.xml > /dev/null
rm tests/kernel.xml && rm tests/messages.xml
echo "ok"

./ElectreIsFindKernel.py -i tests/in2 -o tests
diff -s tests/kernel.xml tests/out2/kernel.xml > /dev/null
diff -s tests/messages.xml tests/out2/messages.xml > /dev/null
rm tests/kernel.xml && rm tests/messages.xml
echo "ok"

###
echo "testing ElectreIVCredibility..."
cd ../ElectreIVCredibility

./ElectreIVCredibility.py -i tests/in1 -o tests
diff -s tests/credibility.xml tests/out1/credibility.xml > /dev/null
diff -s tests/messages.xml tests/out1/messages.xml > /dev/null
rm tests/credibility.xml && rm tests/messages.xml
echo "ok"

./ElectreIVCredibility.py -i tests/in2 -o tests
diff -s tests/credibility.xml tests/out2/credibility.xml > /dev/null
diff -s tests/messages.xml tests/out2/messages.xml > /dev/null
rm tests/credibility.xml && rm tests/messages.xml
echo "ok"

###
echo "testing ElectreTri-CClassAssignments..."
cd ../ElectreTri-CClassAssignments

./ElectreTri-CClassAssignments.py -i tests/in -o tests
diff -s tests/assignments.xml tests/out/assignments.xml > /dev/null
diff -s tests/messages.xml tests/out/messages.xml > /dev/null
rm tests/assignments.xml && rm tests/messages.xml
echo "ok"

###
echo "testing ElectreTriClassAssignments..."
cd ../ElectreTriClassAssignments

./ElectreTriClassAssignments.py -i tests/in -o tests
diff -s tests/assignments_conjuctive.xml tests/out/assignments_conjuctive.xml > /dev/null
diff -s tests/assignments_disjunctive.xml tests/out/assignments_disjunctive.xml > /dev/null
diff -s tests/messages.xml tests/out/messages.xml > /dev/null
rm tests/assignments_conjuctive.xml && rm tests/assignments_disjunctive.xml && rm tests/messages.xml
echo "ok"

###
echo "testing ElectreTri-rCClassAssignments..."
cd ../ElectreTri-rCClassAssignments

./ElectreTri-rCClassAssignments.py -i tests/in -o tests
diff -s tests/assignments.xml tests/out/assignments.xml > /dev/null
diff -s tests/messages.xml tests/out/messages.xml > /dev/null
rm tests/assignments.xml && rm tests/messages.xml
echo "ok"

cd ..

echo "all tests passed successfully!"

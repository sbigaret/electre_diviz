#!/usr/bin/env python

"""
ElectreIsDiscordanceBinary - computes discordance matrix as in Electre Is
method. Resulting discordance indices are from range {0, 1}, hence "binary" in
module's name.

Usage:
    ElectreIsDiscordanceBinary.py -i DIR -o DIR

Options:
    -i DIR     Specify input directory. It should contain following files
               (otherwise program will throw an error):
                   alternatives.xml
                   criteria.xml
                   performanceTable.xml
    -o DIR     Specify output directory.
    --version  Show version.
    -h --help  Show this screen.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import traceback

from docopt import docopt
from lxml import etree
import PyXMCDA as px

from common import (
    create_messages_file,
    get_dirs,
    get_error_message,
    get_trees,
    write_xmcda,
)

__version__ = '0.1.0'


def get_discordances(alternatives, criteria, pref_directions, thresholds, performances):
    discordances = {}
    for a in alternatives:
        b_dict = {}
        for b in alternatives:
            d_dict = {}
            for criterion in criteria:
                if pref_directions[criterion] == 'max':  # 'gain' type criterion
                    if (performances[b][criterion] < performances[a][criterion] +
                            thresholds[criterion]['veto']):
                        d = 0
                    else:
                        d = 1
                else:                                    # 'cost' type criterion
                    if (performances[b][criterion] > performances[a][criterion] -
                            thresholds[criterion]['veto']):
                        d = 0
                    else:
                        d = 1
                d_dict.update({criterion: d})
            b_dict.update({b: d_dict})
        discordances.update({a: b_dict})
    return discordances  # 'partial' discordances (i.e. not aggregated)


def aggregate_discordances(discordances):
    aggregated_discordances = {}
    for a in discordances.iterkeys():
        b_dict = {}
        for b in discordances[a].iterkeys():
            d_aggregated = 0
            for d_partial in discordances[a][b].itervalues():
                if d_partial == 1:
                    d_aggregated = 1
                    break
            b_dict.update({b: d_aggregated})
        aggregated_discordances.update({a: b_dict})
    return aggregated_discordances


def get_input_data(input_dir):
    file_names = (
        'alternatives.xml',
        'criteria.xml',
        'performanceTable.xml',
    )
    trees = get_trees(input_dir, file_names)

    alternatives = px.getAlternativesID(trees['alternatives'])
    criteria = px.getCriteriaID(trees['criteria'])
    pref_directions = px.getCriteriaPreferenceDirections(trees['criteria'], criteria)
    thresholds = px.getConstantThresholds(trees['criteria'], criteria)
    performances = px.getPerformanceTable(trees['performanceTable'], None, None)

    ret = {
        'alternatives': alternatives,
        'criteria': criteria,
        'performances': performances,
        'pref_directions': pref_directions,
        'thresholds': thresholds,
    }
    return ret


def aggregated_discordances_to_xmcda(aggregated_discordances):
    xmcda = etree.Element('alternativesComparisons')
    pairs = etree.SubElement(xmcda, 'pairs')
    for alt1 in aggregated_discordances.iterkeys():
        for alt2 in aggregated_discordances[alt1].iterkeys():
            pair = etree.SubElement(pairs, 'pair')
            initial = etree.SubElement(pair, 'initial')
            alt_id = etree.SubElement(initial, 'alternativeID')
            alt_id.text = alt1
            terminal = etree.SubElement(pair, 'terminal')
            alt_id = etree.SubElement(terminal, 'alternativeID')
            alt_id.text = alt2
            value = etree.SubElement(pair, 'value')
            v = etree.SubElement(value, 'integer')  # XXX boolean..? real..?
            v.text = str(aggregated_discordances[alt1][alt2])
    return xmcda


def main():
    try:
        args = docopt(__doc__, version=__version__)
        input_dir, output_dir = get_dirs(args)
        input_data = get_input_data(input_dir)

        alternatives = input_data['alternatives']
        criteria = input_data['criteria']
        pref_directions = input_data['pref_directions']
        thresholds = input_data['thresholds']
        performances = input_data['performances']

        discordances = get_discordances(alternatives, criteria, pref_directions,
                                        thresholds, performances)
        aggregated_discordances = aggregate_discordances(discordances)

        xmcda = aggregated_discordances_to_xmcda(aggregated_discordances)
        write_xmcda(xmcda, os.path.join(output_dir, 'discordance_binary.xml'))
        create_messages_file(('Everything OK.',), None, output_dir)
        return 0
    except Exception, err:
        traceback.print_exc()
        err_msg = get_error_message(err)
        create_messages_file(None, (err_msg, ), output_dir)
        return 1


if __name__ == '__main__':
    sys.exit(main())

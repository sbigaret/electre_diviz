#!/usr/bin/env python

"""
ElectreIsOutrankingBinary - computes outranking matrix according to Electre Is
method. It takes discordances from range {0, 1} as an input, hence "binary" in
its name.

Usage:
    ElectreIsOutrankingBinary.py -i DIR -o DIR

Options:
    -i DIR     Specify input directory. It should contain following files
               (otherwise program will throw an error):
                   alternatives.xml
                   concordance.xml
                   discordance_binary.xml
                   method_parameters.xml
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
    check_cut_threshold,
    create_messages_file,
    get_dirs,
    get_error_message,
    get_trees,
    write_xmcda,
)

__version__ = '0.1.0'


def get_outranking_binary(alternatives, concordance, discordance_binary, cut_threshold):
    outranking_binary = {}
    for a in alternatives:
        b_dict = {}
        for b in alternatives:
            if concordance[a][b] >= cut_threshold and discordance_binary[a][b] == 0:
                outr = 1
            else:
                outr = 0
            b_dict.update({b: outr})
        outranking_binary.update({a: b_dict})
    return outranking_binary


def get_input_data(input_dir):
    file_names = (
        'alternatives.xml',
        'concordance.xml',
        'method_parameters.xml',
        'discordance_binary.xml',
    )
    trees = get_trees(input_dir, file_names)

    alternatives = px.getAlternativesID(trees['alternatives'])
    # we can also get alternatives from 'concordance.xml', therefore 'alternatives.xml'
    # can be optional - like here:
    # alternatives = list(set([i.text for i in trees['concordance'].findall(".//alternativeID")]))
    concordance = px.getAlternativesComparisons(trees['concordance'], alternatives)
    discordance_binary = px.getAlternativesComparisons(trees['discordance_binary'], alternatives)
    cut_threshold = px.getParameterByName(trees['method_parameters'], 'cut_threshold')
    check_cut_threshold(cut_threshold)

    ret = {
        'alternatives': alternatives,
        'concordance': concordance,
        'cut_threshold': cut_threshold,
        'discordance_binary': discordance_binary,
    }
    return ret


def outranking_binary_to_xmcda(outranking_binary):
    xmcda = etree.Element('alternativesComparisons')
    pairs = etree.SubElement(xmcda, 'pairs')
    for alt1 in outranking_binary.iterkeys():
        for alt2 in outranking_binary[alt1].iterkeys():
            pair = etree.SubElement(pairs, 'pair')
            initial = etree.SubElement(pair, 'initial')
            alt_id = etree.SubElement(initial, 'alternativeID')
            alt_id.text = alt1
            terminal = etree.SubElement(pair, 'terminal')
            alt_id = etree.SubElement(terminal, 'alternativeID')
            alt_id.text = alt2
            value = etree.SubElement(pair, 'value')
            v = etree.SubElement(value, 'integer')  # XXX boolean..? real..?
            v.text = str(outranking_binary[alt1][alt2])
    return xmcda


def main():
    try:
        args = docopt(__doc__, version=__version__)
        input_dir, output_dir = get_dirs(args)
        input_data = get_input_data(input_dir)

        alternatives = input_data['alternatives']
        concordance = input_data['concordance']
        discordance_binary = input_data['discordance_binary']
        cut_threshold = input_data['cut_threshold']

        outranking_binary = get_outranking_binary(alternatives, concordance,
                                                  discordance_binary, cut_threshold)

        xmcda = outranking_binary_to_xmcda(outranking_binary)
        write_xmcda(xmcda, os.path.join(output_dir, 'outranking_binary.xml'))
        create_messages_file(('Everything OK.',), None, output_dir)
        return 0
    except Exception, err:
        traceback.print_exc()
        err_msg = get_error_message(err)
        create_messages_file(None, (err_msg, ), output_dir)
        return 1


if __name__ == '__main__':
    sys.exit(main())

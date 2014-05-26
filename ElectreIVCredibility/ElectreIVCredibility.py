#!/usr/bin/env python

"""
ElectreIVCredibility - computes credibility matrix as presented in Electre IV
method.

Electre IV is a method based on the construction of a set of embedded
outranking relations (similarly to Electre III). There are five such relations,
and every subsequent one accepts an outranking in a less credible
circumstances.

Please note that Electre IV is not the same method as Electre Iv.

Usage:
    ElectreIVCredibility.py -i DIR -o DIR

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

import itertools as it
import os
import sys
import traceback

from docopt import docopt
from lxml import etree
import PyXMCDA as px

from common import (
    get_dirs,
    get_error_message,
    get_trees,
    write_xmcda,
    create_messages_file,
)

__version__ = '0.1.0'


def get_credibility(performances, criteria, thresholds, pref_directions):
    # XXX this function needs serious refactoring (cryptic variables, exceptions
    # used for function's flow steering)
    alt = performances.keys()
    mtx_temp = {i: {j: 0 for j in alt} for i in alt}
    mtx_final = {i: {j: 0 for j in alt} for i in alt}
    pairs = [(i, j) for i in alt for j in alt]
    for pair in pairs:
        # nq, nq, ni, no = number of p's, number of q's and so on
        np = nq = ni = no = 0
        a, b = pair
        if a == b:
            mtx_final[a][b] = 1.0
            continue
        for c in criteria:
            diff = performances[a][c] - performances[b][c]
            if ((pref_directions[c] == 'max' and diff > 0) or
                (pref_directions[c] == 'min' and diff < 0)):
                diff = abs(diff)
                if diff >= thresholds[c]['pref']:  #     diff >= p
                    np += 1
                elif diff > thresholds[c]['ind']:  # q > diff < p
                    nq += 1
                else:                              #     diff <= q
                    ni += 1
            elif diff == 0:
                no += 1
        mtx_temp[a][b] = {'np': np, 'nq': nq, 'ni': ni, 'no': no}
    # at this point we have filled mtx_temp and we can start calculating mtx_final
    for pair in pairs:
        a, b = pair
        if a == b:
            continue
        aSb = mtx_temp[a][b]
        bSa = mtx_temp[b][a]
        try:
            if bSa['np'] + bSa['nq'] == 0 and bSa['ni'] < aSb['np'] + aSb['ni']:
                mtx_final[a][b] = 1.0
                raise Exception
            if bSa['np'] == 0:
                if bSa['nq'] <= aSb['np'] and bSa['nq'] + bSa['ni'] < sum(aSb.values()):
                    mtx_final[a][b] = 0.8
                    raise Exception
                if bSa['nq'] <= aSb['np'] + aSb['nq']:
                    mtx_final[a][b] = 0.6
                    raise Exception
                else:
                    mtx_final[a][b] = 0.4
                    raise Exception
            if bSa['np'] <= 1 and aSb['np'] >= len(criteria) // 2:  # "at least half"
                for c in criteria:
                    diff = performances[b][c] - performances[a][c]
                    if ((pref_directions[c] == 'max' and diff > 0) or
                        (pref_directions[c] == 'min' and diff < 0)):
                        diff = abs(diff)
                        if diff > thresholds[c]['veto']:
                            mtx_final[a][b] = 0.0
                            raise Exception
                mtx_final[a][b] = 0.2
            else:
                mtx_final[a][b] = 0.0
        except Exception:
            continue
    return mtx_final


def get_input_data(input_dir):
    file_names = (
        'alternatives.xml',
        'criteria.xml',
        'performanceTable.xml',
    )
    trees = get_trees(input_dir, file_names)

    criteria = px.getCriteriaID(trees['criteria'])
    pref_directions = px.getCriteriaPreferenceDirections(trees['criteria'], criteria)
    thresholds = px.getConstantThresholds(trees['criteria'], criteria)
    performances = px.getPerformanceTable(trees['performanceTable'], None, None)

    ret = {
        'criteria': criteria,
        'performances': performances,
        'pref_directions': pref_directions,
        'thresholds': thresholds,
    }
    return ret


def credibility_to_xmcda(credibility):
    xmcda = etree.Element('alternativesComparisons')
    pairs = etree.SubElement(xmcda, 'pairs')
    for alt1 in credibility.iterkeys():
        for alt2 in credibility[alt1].iterkeys():
            pair = etree.SubElement(pairs, 'pair')
            initial = etree.SubElement(pair, 'initial')
            alt_id = etree.SubElement(initial, 'alternativeID')
            alt_id.text = alt1
            terminal = etree.SubElement(pair, 'terminal')
            alt_id = etree.SubElement(terminal, 'alternativeID')
            alt_id.text = alt2
            value = etree.SubElement(pair, 'value')
            v = etree.SubElement(value, 'real')
            v.text = str(credibility[alt1][alt2])
    return xmcda


def main():
    try:
        args = docopt(__doc__, version=__version__)
        input_dir, output_dir = get_dirs(args)
        input_data = get_input_data(input_dir)

        performances = input_data['performances']
        criteria = input_data['criteria']
        thresholds = input_data['thresholds']
        pref_directions = input_data['pref_directions']

        credibility = get_credibility(performances, criteria, thresholds,
                                      pref_directions)

        xmcda = credibility_to_xmcda(credibility)
        write_xmcda(xmcda, os.path.join(output_dir, 'credibility.xml'))
        create_messages_file(('Everything OK.',), None, output_dir)
        return 0
    except Exception, err:
        traceback.print_exc()
        err_msg = get_error_message(err)
        create_messages_file(None, (err_msg, ), output_dir)
        return 1

if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python

"""
ElectreConcordance - computes concordance matrix using procedure which is
common to the most methods from the Electre family.

The key feature of this module is its flexibility in terms of the types of
elements allowed to compare, i.e. alternatives vs alternatives, alternatives vs
boundary profiles and alternatives vs central (characteristic) profiles.

Usage:
    ElectreConcordance.py -i DIR -o DIR

Options:
    -i DIR     Specify input directory. It should contain the following files:
                   alternatives.xml
                   categories_profiles.xml (optional)
                   criteria.xml
                   method_parameters.xml
                   performance_table.xml
                   profiles_performance_table.xml (optional)
                   weights.xml
    -o DIR     Specify output directory. Files generated as output:
                   concordance.xml
                   messages.xml
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

from common import (
    comparisons_to_xmcda,
    create_messages_file,
    get_dirs,
    get_error_message,
    get_input_data,
    write_xmcda,
    Vividict,
)

__version__ = '0.2.0'


def get_concordance(comparables_a, comparables_perf_a, comparables_b, comparables_perf_b,
                    criteria, thresholds, pref_directions, weights):

    def _omega(x, y):
        # 'x' and 'y' to keep it as general as possible
        if pref_directions[criterion] == 'max':
            return x - y
        if pref_directions[criterion] == 'min':
            return y - x

    def _get_partial_concordance(x, y, criterion):
        p = thresholds[criterion].get('preference')
        q = thresholds[criterion].get('indifference')
        if _omega(x, y) < -p:
            return 0.0
        elif _omega(x, y) >= -q:
            return 1.0
        else:
            return (_omega(x, y) + p) / (p - q)

    def _get_aggregated_concordance(x, y):
        sum_of_weights = sum([weights[criterion] for criterion in criteria])
        concordance = sum([weights[criterion] * partial_concordances[x][y][criterion]
                           for criterion in criteria]) / sum_of_weights
        return concordance

    two_way_comparison = True if comparables_a != comparables_b else False
    # compute partial concordances
    partial_concordances = Vividict()
    for a in comparables_a:
        for b in comparables_b:
            for criterion in criteria:
                partial_concordances[a][b][criterion] = _get_partial_concordance(
                    comparables_perf_a[a][criterion],
                    comparables_perf_b[b][criterion],
                    criterion,
                )
                if two_way_comparison:
                    partial_concordances[b][a][criterion] = _get_partial_concordance(
                        comparables_perf_b[b][criterion],
                        comparables_perf_a[a][criterion],
                        criterion,
                    )
    # aggregate partial concordances
    aggregated_concordances = Vividict()
    for a in comparables_a:
        for b in comparables_b:
            aggregated_concordances[a][b] = _get_aggregated_concordance(a, b)
            if two_way_comparison:
                aggregated_concordances[b][a] = _get_aggregated_concordance(b, a)
    return aggregated_concordances


def main():
    try:
        args = docopt(__doc__, version=__version__)
        input_dir, output_dir = get_dirs(args)
        filenames = [
            # every tuple below == (filename, is_optional)
            ('alternatives.xml', False),
            ('categories_profiles.xml', True),
            ('criteria.xml', False),
            ('method_parameters.xml', False),
            ('performance_table.xml', False),
            ('profiles_performance_table.xml', True),
            ('weights.xml', False),
        ]
        params = [
            'alternatives',
            'categories_profiles',
            'comparison_with',
            'criteria',
            'performances',
            'pref_directions',
            'profiles_performance_table',
            'thresholds',
            'weights',
        ]
        d = get_input_data(input_dir, filenames, params)

        # getting the elements to compare
        comparables_a = d.alternatives
        comparables_perf_a = d.performances
        if d.comparison_with in ('boundary_profiles', 'central_profiles'):
            comparables_b = [i for i in d.categories_profiles]  # because of central_profiles being a dict
            comparables_perf_b = d.profiles_performance_table
        else:
            comparables_b = d.alternatives
            comparables_perf_b = d.performances

        concordance = get_concordance(
            comparables_a,
            comparables_perf_a,
            comparables_b,
            comparables_perf_b,
            d.criteria,
            d.thresholds,
            d.pref_directions,
            d.weights,
        )

        # serialization etc.
        if d.comparison_with in ('boundary_profiles', 'central_profiles'):
            mcda_concept = 'alternativesProfilesComparisons'
        else:
            mcda_concept = None
        comparables = (comparables_a, comparables_b)
        xmcda = comparisons_to_xmcda(concordance, comparables, mcda_concept=mcda_concept)
        write_xmcda(xmcda, os.path.join(output_dir, 'concordance.xml'))
        create_messages_file(None, ('Everything OK.',), output_dir)
        return 0
    except Exception, err:
        err_msg = get_error_message(err)
        log_msg = traceback.format_exc()
        print(log_msg.strip())
        create_messages_file((err_msg, ), (log_msg, ), output_dir)
        return 1


if __name__ == '__main__':
    sys.exit(main())

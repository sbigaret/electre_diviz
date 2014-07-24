#!/usr/bin/env python

"""
ElectreIsDiscordanceBinary - computes discordance matrix as in Electre Is
method. Resulting discordance indices are from range {0, 1}, hence "binary" in
module's name.

The key feature of this module is its flexibility in terms of the types of
elements allowed to compare, i.e. alternatives vs alternatives, alternatives vs
boundary profiles and alternatives vs central (characteristic) profiles.

Usage:
    ElectreIsDiscordanceBinary.py -i DIR -o DIR

Options:
    -i DIR     Specify input directory.
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

from common import (
    comparisons_to_xmcda,
    create_messages_file,
    get_dirs,
    get_error_message,
    get_input_data,
    write_xmcda,
    Vividict,
)

__version__ = '0.9.0'


def get_discordance(comparables_a, comparables_perf_a, comparables_b, comparables_perf_b,
                    criteria, thresholds, pref_directions):

    def _get_partial_discordance(x, y, criterion):
        v = thresholds[criterion].get('veto')
        if pref_directions[criterion] == 'max':
            if (y < x + v):
                d = 0
            else:
                d = 1
        else:
            if (y > x - v):
                d = 0
            else:
                d = 1
        return d

    def _get_aggregated_discordances(x, y):
        d_aggregated = 0
        for d_partial in partial_discordances[x][y].itervalues():
            if d_partial == 1:
                d_aggregated = 1
                break
        return d_aggregated

    two_way_comparison = True if comparables_a != comparables_b else False
    partial_discordances = Vividict()
    for a in comparables_a:
        for b in comparables_b:
            for criterion in criteria:
                partial_discordances[a][b][criterion] = _get_partial_discordance(
                    comparables_perf_a[a][criterion],
                    comparables_perf_b[b][criterion],
                    criterion,
                )
                if two_way_comparison:
                    partial_discordances[b][a][criterion] = _get_partial_discordance(
                        comparables_perf_b[b][criterion],
                        comparables_perf_a[a][criterion],
                        criterion,
                    )
    aggregated_discordances = Vividict()
    for a in comparables_a:
        for b in comparables_b:
            aggregated_discordances[a][b] = _get_aggregated_discordances(a, b)
            if two_way_comparison:
                aggregated_discordances[b][a] = _get_aggregated_discordances(b, a)
    return aggregated_discordances


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
        ]
        d = get_input_data(input_dir, filenames, params)

        # getting the elements to compare
        comparables_a = d.alternatives
        comparables_perf_a = d.performances
        if d.comparison_with in ('boundary_profiles', 'central_profiles'):
            comparables_b = d.categories_profiles
            comparables_perf_b = d.profiles_performance_table
        else:
            comparables_b = d.alternatives
            comparables_perf_b = d.performances

        discordance = get_discordance(
            comparables_a,
            comparables_perf_a,
            comparables_b,
            comparables_perf_b,
            d.criteria,
            d.thresholds,
            d.pref_directions,
        )

        # serialization etc.
        if d.comparison_with in ('boundary_profiles', 'central_profiles'):
            mcda_concept = 'alternativesProfilesComparisons'
        else:
            mcda_concept = None
        comparables = (comparables_a, comparables_b)
        xmcda = comparisons_to_xmcda(discordance, comparables, mcda_concept=mcda_concept)
        write_xmcda(xmcda, os.path.join(output_dir, 'discordance.xml'))
        create_messages_file(('Everything OK.',), None, output_dir)
        return 0
    except Exception, err:
        traceback.print_exc()
        err_msg = get_error_message(err)
        create_messages_file(None, (err_msg, ), output_dir)
        return 1

if __name__ == '__main__':
    sys.exit(main())

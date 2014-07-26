#!/usr/bin/env python

"""
ElectreConcordanceWithInteractions - computes concordance matrix taking
into account interactions between criteria. Possible interactions are:
'strengthening', 'weakening' and 'antagonistic'.

This module allows to compute concordance matrix for both for alternatives vs
alternatives and alternatives vs profiles comparison - where profiles may be
boundary or central (characteristic).

Usage:
    ElectreConcordanceWithInteractions.py -i DIR -o DIR

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

from itertools import chain
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


def get_concordance(comparables_a, comparables_perf_a, comparables_b, comparables_perf_b,
                    criteria, thresholds, pref_directions, weights,
                    interactions, z_function):

    def _check_net_balance(interactions, weights):
        criteria_affected = set([i[0] for i in chain(interactions.get('weakening', []), interactions.get('antagonistic', []))])
        for criterion in criteria_affected:
            weakening_sum = sum([abs(i[2]) for i in interactions.get('weakening', []) if i[0] == criterion])
            antagonistic_sum = sum([i[2] for i in interactions.get('antagonistic', []) if i[0] == criterion])
            net_balance = weights[criterion] - (weakening_sum + antagonistic_sum)
            if net_balance <= 0:
                raise RuntimeError("Positive net balance condition not fulfilled for criterion '{}'.".format(criterion))
        return

    def _omega(x, y):  # XXX exactly the same as in ElectreConcordance
        # 'x' and 'y' to keep it as general as possible
        if pref_directions[criterion] == 'max':
            return x - y
        if pref_directions[criterion] == 'min':
            return y - x

    def _get_partial_concordance(x, y, criterion):  # XXX exactly the same as in ElectreConcordance
        p = thresholds[criterion].get('preference')
        q = thresholds[criterion].get('indifference')
        if _omega(x, y) < -p:
            return 0.0
        elif _omega(x, y) >= -q:
            return 1.0
        else:
            return (_omega(x, y) + p) / (p - q)

    def _get_aggregated_concordance(x, y):  # ...with interactions
        # XXX I don't like those cryptic variable names here
        if x == y:
            C = 1.0
        else:
            sum_cki = sum([partial_concordances[x][y][c] * weights[c] for c in criteria])
            sum_kij = float(0)
            for interaction_name in ('strengthening', 'weakening'):
                for interaction in interactions.get(interaction_name, []):
                    ci = partial_concordances[x][y][interaction[0]]
                    cj = partial_concordances[x][y][interaction[1]]
                    sum_kij += Z(ci, cj) * interaction[2]
            sum_kih = 0.0
            for interaction in interactions.get('antagonistic', []):
                ci = partial_concordances[x][y][interaction[0]]
                ch = partial_concordances[y][x][interaction[1]]
                sum_kih += Z(ci, ch) * interaction[2]
            sum_ki = sum(weights.values())  # this is only for K
            K = sum_ki + sum_kij - sum_kih
            C = (sum_cki + sum_kij - sum_kih) / K
        return C

    # some initial checks
    _check_net_balance(interactions, weights)
    if z_function == 'multiplication':
        Z = lambda x, y: x * y
    elif z_function == 'minimum':
        Z = lambda x, y: min(x, y)
    else:
        raise RuntimeError("Invalid Z function: '{}'.".format(z_function))

    # XXX this block below is exactly the same as in ElectreConcordance
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
            ('interactions.xml', False),
            ('method_parameters.xml', False),
            ('performance_table.xml', False),
            ('profiles_performance_table.xml', True),
            ('weights.xml', False),
        ]
        params = [
            'alternatives',
            'performances',
            'comparison_with',
            'criteria',
            'interactions',
            'pref_directions',
            'thresholds',
            'weights',
            'z_function',
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

        concordance = get_concordance(
            comparables_a,
            comparables_perf_a,
            comparables_b,
            comparables_perf_b,
            d.criteria,
            d.thresholds,
            d.pref_directions,
            d.weights,
            d.interactions,
            d.z_function,
        )

        # serialization etc.
        if d.comparison_with in ('boundary_profiles', 'central_profiles'):
            mcda_concept = 'alternativesProfilesComparisons'
        else:
            mcda_concept = None
        comparables = (comparables_a, comparables_b)
        xmcda = comparisons_to_xmcda(concordance, comparables, mcda_concept=mcda_concept)
        write_xmcda(xmcda, os.path.join(output_dir, 'concordance.xml'))
        create_messages_file(('Everything OK.',), None, output_dir)
        return 0
    except Exception, err:
        traceback.print_exc()
        err_msg = get_error_message(err)
        create_messages_file(None, (err_msg, ), output_dir)
        return 1


if __name__ == '__main__':
    sys.exit(main())

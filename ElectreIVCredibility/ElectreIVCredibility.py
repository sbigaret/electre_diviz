#!/usr/bin/env python

"""
ElectreIVCredibility - computes credibility matrix as presented in Electre IV
method.

The key feature of this module is its flexibility in terms of the types of
elements allowed to compare, i.e. alternatives vs alternatives, alternatives vs
boundary profiles and alternatives vs central (characteristic) profiles.

Electre IV is a method based on the construction of a set of embedded
outranking relations (similarly to Electre III). There are five such relations,
and every subsequent one accepts an outranking in a less credible
circumstances.

Please note that Electre IV is not the same method as Electre Iv.

Usage:
    ElectreIVCredibility.py -i DIR -o DIR

Options:
    -i DIR     Specify input directory. It should contain the following files:
                   alternatives.xml
                   categories_profiles.xml (optional)
                   criteria.xml
                   method_parameters.xml
                   performance_table.xml
                   profiles_performance_table.xml (optional)
    -o DIR     Specify output directory. Files generated as output:
                   credibility.xml
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

from common import comparisons_to_xmcda, create_messages_file, get_dirs, \
    get_error_message, get_input_data, write_xmcda, Vividict

__version__ = '0.2.0'


def get_credibility(comparables_a, comparables_perf_a, comparables_b,
                    comparables_perf_b, criteria, pref_directions, thresholds):
    """np, nq, ni, no - number of criteria where:
    n_p(a, b) - 'a' is strictly preferred over 'b'
    n_q(a, b) - 'a' is weakly preferred over 'b'
    n_i(a, b) - 'a' is indifferent than 'b', but 'a' has better performance
    n_o(a, b) - 'a' is indifferent than 'b' and both have the same performances
    """
    def _check_diff(diff, criterion):
        if ((pref_directions[criterion] == 'max' and diff > 0) or
                (pref_directions[criterion] == 'min' and diff < 0)):
            diff = abs(diff)
        elif diff == 0:
            pass
        else:
            diff = None
        return diff

    def _check_for_veto(performances_x, performances_y):
        veto = False
        for c in criteria:
            if thresholds[c].get('veto') is None:
                continue
            diff = _check_diff(performances_x[c] - performances_y[c], c)
            if diff > thresholds[c]['veto']:
                veto = True
                break
        return veto

    def _get_criteria_counts(x, y, performances_x, performances_y):
        np = nq = ni = no = 0
        for c in criteria:
            diff = _check_diff(performances_x[c] - performances_y[c], c)
            if diff:
                if diff >= thresholds[c]['preference']:     # diff >= p
                    np += 1
                elif diff > thresholds[c]['indifference']:  # q > diff < p
                    nq += 1
                else:                                       # diff <= q
                    ni += 1
            elif diff == 0:
                no += 1
        return {'np': np, 'nq': nq, 'ni': ni, 'no': no}

    def _get_cred_values(comparables_x, comparables_y, comparables_perf_x,
                         comparables_perf_y, credibility):
        for x in comparables_x:
            for y in comparables_y:
                if x == y:
                    credibility[x][y] = 1.0
                    continue
                # let's abbreviate these two for convenience
                cc_xy = criteria_counts[x][y]
                cc_yx = criteria_counts[y][x]
                if (cc_yx['np'] + cc_yx['nq'] == 0 and
                        cc_yx['ni'] < cc_xy['np'] + cc_xy['nq'] + cc_xy['ni']):
                    credibility[x][y] = 1.0
                    continue
                elif cc_yx['np'] == 0:
                    sum_cc_yx = cc_yx['nq'] + cc_yx['ni']
                    sum_cc_xy = cc_xy['np'] + cc_xy['nq'] + cc_xy['ni']
                    if cc_yx['nq'] <= cc_xy['np'] and sum_cc_yx < sum_cc_xy:
                        credibility[x][y] = 0.8
                        continue
                    elif cc_yx['nq'] <= cc_xy['np'] + cc_xy['nq']:
                        credibility[x][y] = 0.6
                        continue
                    else:
                        credibility[x][y] = 0.4
                elif cc_yx['np'] <= 1 and cc_xy['np'] >= len(criteria) // 2:
                    veto = _check_for_veto(comparables_perf_y[y],
                                           comparables_perf_x[x])
                    if not veto:
                        credibility[x][y] = 0.2
                        continue
                    else:
                        credibility[x][y] = 0.0
                        continue
                else:
                    credibility[x][y] = 0.0
                    continue
        return credibility

    two_way_comparison = True if comparables_a != comparables_b else False
    criteria_counts = Vividict()
    for a in comparables_a:
        for b in comparables_b:
            cc = _get_criteria_counts(a, b, comparables_perf_a[a],
                                      comparables_perf_b[b])
            criteria_counts[a][b] = cc
            if two_way_comparison:
                cc = _get_criteria_counts(b, a, comparables_perf_b[b],
                                          comparables_perf_a[a])
                criteria_counts[b][a] = cc
    credibility = Vividict()
    credibility = _get_cred_values(comparables_a, comparables_b,
                                   comparables_perf_a, comparables_perf_b,
                                   credibility)
    if two_way_comparison:
        credibility = _get_cred_values(comparables_b, comparables_a,
                                       comparables_perf_b, comparables_perf_a,
                                       credibility)
    return credibility


def main():
    try:
        args = docopt(__doc__, version=__version__)
        output_dir = None
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

        credibility = get_credibility(comparables_a, comparables_perf_a,
                                      comparables_b, comparables_perf_b,
                                      d.criteria, d.pref_directions,
                                      d.thresholds)

        # serialization etc.
        if d.comparison_with in ('boundary_profiles', 'central_profiles'):
            mcda_concept = 'alternativesProfilesComparisons'
        else:
            mcda_concept = None
        comparables = (comparables_a, comparables_b)
        xmcda = comparisons_to_xmcda(credibility, comparables,
                                     mcda_concept=mcda_concept)
        write_xmcda(xmcda, os.path.join(output_dir, 'credibility.xml'))
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

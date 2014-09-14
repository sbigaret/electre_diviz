#!/usr/bin/env python

"""
ElectreDiscordance - computes partial (i.e. per-criterion) discordance matrix
using procedure which is common to the most methods from the Electre family.

The key feature of this module is its flexibility in terms of the types of
elements allowed to compare, i.e. alternatives vs alternatives, alternatives vs
boundary profiles and alternatives vs central (characteristic) profiles.

It also brings two new concepts: a 'counter-veto' threshold (cv) and 'pre-veto'
threshold (pv) such as: cv >= v >= pv >= p (where 'v' is 'veto' threshold, and
'p' is 'preference' threshold).

Usage:
    ElectreDiscordance.py -i DIR -o DIR

Options:
    -i DIR     Specify input directory. It should contain the following files:
                   alternatives.xml
                   classes_profiles.xml (optional)
                   criteria.xml
                   method_parameters.xml
                   performance_table.xml
                   profiles_performance_table.xml (optional)
    -o DIR     Specify output directory. Files generated as output:
                   counter_veto_crossed.xml
                   discordance.xml
                   messages.xml
    --version  Show version.
    -h --help  Show this screen.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys
import traceback
from functools import partial

from docopt import docopt

from common import comparisons_to_xmcda, create_messages_file, get_dirs, \
    get_error_message, get_input_data, get_linear, omega, write_xmcda, Vividict

__version__ = '0.2.0'


def get_discordance(comparables_a, comparables_perf_a, comparables_b,
                    comparables_perf_b, criteria, thresholds, pref_directions,
                    use_pre_veto):

    # 'partial' in this function's name has nothing to do w/ functools.partial
    def _get_partial_discordance(x, y, criterion, use_pre_veto):
        _omega = partial(omega, pref_directions, criterion)
        _get_linear = partial(get_linear, pref_directions, criterion, x, y)
        p = _get_linear(thresholds[criterion].get('preference', 0))
        v = _get_linear(thresholds[criterion].get('veto'))
        cv = _get_linear(thresholds[criterion].get('counter_veto'))
        crossed = False  # crossed 'counter_veto' threshold
        if not v:
            return (0.0, crossed)
        if cv is not None and _omega(x, y) > cv:
            crossed = True
        if use_pre_veto:
            # originally (i.e. w/o pre_veto) pv == p
            pv = _get_linear(thresholds[criterion].get('pre_veto', p))
            if _omega(x, y) > -pv:
                pd = 0.0
            elif _omega(x, y) <= -v:
                pd = 1.0
            else:
                pd = (_omega(y, x) - pv) / (v - pv)
        else:
            if _omega(x, y) >= -p:
                pd = 0.0
            elif _omega(x, y) < -v:
                pd = 1.0
            else:
                pd = (_omega(x, y) + p) / (p - v)
        return (pd, crossed)

    two_way_comparison = True if comparables_a != comparables_b else False
    partial_discordance = Vividict()
    cv_crossed = Vividict()
    for a in comparables_a:
        for b in comparables_b:
            for criterion in criteria:
                x = comparables_perf_a[a][criterion]
                y = comparables_perf_b[b][criterion]
                pd, crossed = _get_partial_discordance(x, y, criterion,
                                                       use_pre_veto)
                partial_discordance[a][b][criterion] = pd
                cv_crossed[a][b][criterion] = crossed
                if two_way_comparison:
                    x = comparables_perf_b[b][criterion]
                    y = comparables_perf_a[a][criterion]
                    pd, crossed = _get_partial_discordance(x, y, criterion,
                                                           use_pre_veto)
                    partial_discordance[b][a][criterion] = pd
                    cv_crossed[b][a][criterion] = crossed
    return partial_discordance, cv_crossed


def main():
    try:
        args = docopt(__doc__, version=__version__)
        output_dir = None
        input_dir, output_dir = get_dirs(args)
        filenames = [
            # every tuple below == (filename, is_optional)
            ('alternatives.xml', False),
            ('classes_profiles.xml', True),
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
            'use_pre_veto',
        ]
        d = get_input_data(input_dir, filenames, params)

        # getting the elements to compare
        comparables_a = d.alternatives
        comparables_perf_a = d.performances
        if d.comparison_with in ('boundary_profiles', 'central_profiles'):
            # central_profiles is a dict, so we need to get the keys
            comparables_b = [i for i in d.categories_profiles]
            comparables_perf_b = d.profiles_performance_table
        else:
            comparables_b = d.alternatives
            comparables_perf_b = d.performances

        discordance, cv_crossed = get_discordance(comparables_a,
                                                  comparables_perf_a,
                                                  comparables_b,
                                                  comparables_perf_b,
                                                  d.criteria, d.thresholds,
                                                  d.pref_directions,
                                                  d.use_pre_veto)

        # serialization etc.
        if d.comparison_with in ('boundary_profiles', 'central_profiles'):
            mcda_concept = 'alternativesProfilesComparisons'
        else:
            mcda_concept = None
        comparables = (comparables_a, comparables_b)
        xmcda = comparisons_to_xmcda(discordance, comparables,
                                     use_partials=True,
                                     mcda_concept=mcda_concept)
        write_xmcda(xmcda, os.path.join(output_dir, 'discordance.xml'))
        mcda_concept = 'counterVetoCrossed'
        xmcda = comparisons_to_xmcda(cv_crossed, comparables,
                                     use_partials=True,
                                     mcda_concept=mcda_concept)
        write_xmcda(xmcda, os.path.join(output_dir, 'counter_veto_crossed.xml'))
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

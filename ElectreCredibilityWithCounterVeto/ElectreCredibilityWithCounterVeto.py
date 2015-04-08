#!/usr/bin/env python

"""
ElectreCredibilityWithCounterVeto - computes credibility matrix using procedure
which is common to the most methods from the Electre family.

This module is an extended version of 'ElectreCredibility' in that it is
designed to work with the 'counter-veto' concept - i.e. it requires an
additional input file ('counter_veto_crossed.xml') produced by
'ElectreDiscordance' module, which contains the information for which pairs of
variants and on which criteria the 'counter-veto' threshold has been crossed.

Please note that unlike 'ElectreCredibility', this module can accept
discordance indices only in non-aggregated form (i.e. one index per criterion).

Usage:
    ElectreCredibilityWithCounterVeto.py -i DIR -o DIR

Options:
    -i DIR     Specify input directory. It should contain the following files:
                   alternatives.xml
                   classes_profiles.xml (optional)
                   concordance.xml
                   counter_veto_crossed.xml
                   discordance.xml
                   method_parameters.xml
    -o DIR     Specify output directory. Files generated as output:
                   credibility.xml
                   messages.xml
    --version  Show version.
    -h --help  Show this screen.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys
import traceback

from docopt import docopt

from common import comparisons_to_xmcda, create_messages_file, get_dirs, \
    get_error_message, get_input_data, write_xmcda, Vividict

__version__ = '0.1.0'


def get_credibility(comparables_a, comparables_b, concordance, discordance,
                    with_denominator, only_max_discordance, cv_crossed):

    def _get_credibility_idx(x, y, num_crossed, only_max_discordance):
        discordance_values = discordance[x][y].values()
        if set(discordance_values) == set([0]):  # only zeros
            c_idx = concordance[x][y]
        elif 1 in discordance_values:            # at least one '1'
            if not concordance[x][y] < 1:
                raise RuntimeError("When discordance == 1, "
                                   "concordance must be < 1.")
            c_idx = 0.0
        elif only_max_discordance and not with_denominator:
            c_idx = concordance[x][y] * (1 - max(discordance_values))
        else:
            factors = []
            for d in discordance_values:
                if with_denominator:
                    if d > concordance[x][y]:
                        factor = (1 - d) / (1 - concordance[x][y])
                    else:
                        factor = None
                else:
                    factor = (1 - d)
                if factor:
                    factors.append(factor)
            if factors == []:
                c_idx = concordance[x][y]
            else:
                discordance_aggr = reduce(lambda f1, f2: f1 * f2, factors)
                c_idx = (concordance[x][y] *
                         discordance_aggr ** (1 - num_crossed / num_total))
        return c_idx

    two_way_comparison = True if comparables_a != comparables_b else False
    # 'num_total' == total number of criteria.
    # Instead of this monstrosity below, maybe it would be better to provide
    # 'criteria.xml' as another input..?
    num_total = len(discordance.values()[0].values()[0].keys())
    credibility = Vividict()
    for a in comparables_a:
        for b in comparables_b:
            num_crossed = len(cv_crossed[a][b])
            credibility[a][b] = _get_credibility_idx(a, b, num_crossed,
                                                     only_max_discordance)
            if two_way_comparison:
                credibility[b][a] = _get_credibility_idx(b, a, num_crossed,
                                                         only_max_discordance)
    return credibility


def main():
    try:
        args = docopt(__doc__, version=__version__)
        output_dir = None
        input_dir, output_dir = get_dirs(args)
        filenames = [
            # every tuple below == (filename, is_optional)
            ('alternatives.xml', False),
            ('classes_profiles.xml', True),
            ('concordance.xml', False),
            ('counter_veto_crossed.xml', False),
            ('discordance.xml', False),
            ('method_parameters.xml', False),
        ]
        params = [
            'alternatives',
            'categories_profiles',
            'comparison_with',
            'concordance',
            'cv_crossed',
            'discordance',
            'only_max_discordance',
            'with_denominator',
        ]
        d = get_input_data(input_dir, filenames, params, use_partials=True)

        # getting the elements to compare
        comparables_a = d.alternatives
        if d.comparison_with in ('boundary_profiles', 'central_profiles'):
            # central_profiles is a dict, so we need to get the keys
            comparables_b = [i for i in d.categories_profiles]
        else:
            comparables_b = d.alternatives

        credibility = get_credibility(comparables_a, comparables_b,
                                      d.concordance, d.discordance,
                                      d.with_denominator,
                                      d.only_max_discordance, d.cv_crossed)

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

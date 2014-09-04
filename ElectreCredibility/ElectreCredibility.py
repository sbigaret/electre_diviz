#!/usr/bin/env python

"""
ElectreCredibility - computes credibility matrix using procedure which is
common to the most methods from the Electre family.

The key feature of this module is its flexibility in terms of the types of
elements accepted as input, i.e. concordance or discordance may be a product of
the following comparisons: alternatives vs alternatives, alternatives vs
boundary profiles and alternatives vs central (characteristic) profiles.

Usage:
    ElectreCredibility.py -i DIR -o DIR

Options:
    -i DIR     Specify input directory. It should contain the following files:
                   alternatives.xml
                   classes_profiles.xml (optional)
                   concordance.xml
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

__version__ = '0.2.0'


def get_credibility(comparables_a, comparables_b, concordance, discordance,
                    with_denominator, only_max_discordance, use_partials):

    def _get_credibility_index(x, y, with_denominator, only_max_discordance,
                               use_partials):
        if use_partials:
            discordance_values = discordance[x][y].values()
        else:
            discordance_values = [discordance[x][y]]
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
                    factor = (1 - d)
                factors.append(factor)
            if factors == []:
                c_idx = 0.0
            else:
                c_idx = concordance[x][y] * reduce(lambda f1, f2: f1 * f2,
                                                   factors)
        return c_idx

    two_way_comparison = True if comparables_a != comparables_b else False
    credibility = Vividict()
    for a in comparables_a:
        for b in comparables_b:
            credibility[a][b] = _get_credibility_index(a, b, with_denominator,
                                                       only_max_discordance,
                                                       use_partials)
            if two_way_comparison:
                credibility[b][a] = _get_credibility_index(b, a, with_denominator,
                                                           only_max_discordance,
                                                           use_partials)
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
            ('discordance.xml', False),
            ('method_parameters.xml', False),
        ]
        params = [
            'alternatives',
            'categories_profiles',
            'comparison_with',
            'concordance',
            'discordance',
            'only_max_discordance',
            'with_denominator',
            'use_partials',
        ]
        d = get_input_data(input_dir, filenames, params)

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
                                      d.only_max_discordance,
                                      d.use_partials)

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

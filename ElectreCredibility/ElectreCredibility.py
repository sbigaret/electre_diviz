#!/usr/bin/env python

"""
ElectreCredibility - computes credibility matrix using procedure which is common
to the most methods from the Electre family.

The key feature of this module is its flexibility in terms of the types of
elements accepted as input, i.e. concordance or discordance may be a product of
the following comparisons: alternatives vs alternatives, alternatives vs
boundary profiles and alternatives vs central (characteristic) profiles.

Usage:
    ElectreCredibility.py -i DIR -o DIR

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

def get_credibility(comparables_a, comparables_b, concordance, discordance, use_1_minus_C,
                    use_partials):

    def _get_credibility_index(x, y, use_1_minus_C, use_partials):
        if use_partials:
            discordance_values = discordance[x][y].values()
        else:
            discordance_values = [discordance[x][y]]
        if set(discordance_values) == set([0]):  # only zeros
            c_idx = concordance[x][y]
        elif 1 in discordance_values:            # at least one '1'
            if not concordance[x][y] < 1:
                raise RuntimeError("When discordance == 1, concordance must be < 1.")
            c_idx = 0.0
        else:
            factors = []
            for d in discordance_values:
                if d > concordance[x][y]:  # d_i(a, b) > C(a, b)
                    if use_1_minus_C:
                        factor = (1 - d) / (1 - concordance[x][y])
                    else:
                        factor = (1 - d)
                    factors.append(factor)
            c_idx = concordance[x][y] * reduce(lambda f1, f2: f1 * f2, factors)
        return c_idx

    two_way_comparison = True if comparables_a != comparables_b else False
    credibility = Vividict()
    for a in comparables_a:
        for b in comparables_b:
            credibility[a][b] = _get_credibility_index(a, b, use_1_minus_C, use_partials)
            if two_way_comparison:
                credibility[b][a] = _get_credibility_index(b, a, use_1_minus_C, use_partials)
    return credibility


def main():
    try:
        args = docopt(__doc__, version=__version__)
        input_dir, output_dir = get_dirs(args)
        filenames = [
            # every tuple below == (filename, is_optional)
            ('alternatives.xml', False),
            ('categories_profiles.xml', True),
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
            'use_1_minus_C',
            'use_partials',
        ]
        d = get_input_data(input_dir, filenames, params)

        # getting the elements to compare
        comparables_a = d.alternatives
        if d.comparison_with in ('boundary_profiles', 'central_profiles'):
            comparables_b = d.categories_profiles
        else:
            comparables_b = d.alternatives

        credibility = get_credibility(
            comparables_a,
            comparables_b,
            d.concordance,
            d.discordance,
            d.use_1_minus_C,  # XXX or maybe 'use_denominator'..?
            d.use_partials,
        )

        # serialization etc.
        if d.comparison_with in ('boundary_profiles', 'central_profiles'):
            mcda_concept = 'alternativesProfilesComparisons'
        else:
            mcda_concept = None
        comparables = (comparables_a, comparables_b)
        xmcda = comparisons_to_xmcda(credibility, comparables, mcda_concept=mcda_concept)
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

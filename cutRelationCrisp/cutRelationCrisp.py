#!/usr/bin/env python

"""
cutRelationCrisp - this module applies a cut threshold and determines the type
of the outranking relation between given pairs of alternatives or
alternatives/profiles (boundary or central).

The possible relations are 'preference', 'indifference' and 'incomparability'.
The output is produced for all pairs provided as input - therefore, in case of
getting a 'preference' relation, which is unidirectional, the other direction's
relation (or rather, lack of thereof) will be denoted as 'none'.

Usage:
    cutRelationCrisp.py -i DIR -o DIR

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


def get_outranking_relation(comparables_a, comparables_b, credibility, cut_threshold):
    # two_way_comparison is not needed here
    outranking = Vividict()
    for a in comparables_a:
        for b in comparables_b:
            c_ab = credibility[a][b]
            c_ba = credibility[b][a]
            if c_ab >= cut_threshold and c_ba >= cut_threshold:
                relation = 'indifference'
            elif c_ab >= cut_threshold and c_ba < cut_threshold:
                relation = 'preference_ab'
            elif c_ab < cut_threshold and c_ba >= cut_threshold:
                relation = 'preference_ba'
            elif c_ab < cut_threshold and c_ba < cut_threshold:
                relation = 'incomparability'
            if relation in ('indifference', 'incomparability'):
                outranking[a][b] = relation
                outranking[b][a] = relation
            elif relation in ('preference_ab', 'preference_ba'):
                relation, pair = relation.split('_')
                if pair == 'ab':
                    outranking[a][b] = relation
                    outranking[b][a] = 'none'
                elif pair == 'ba':
                    outranking[b][a] = relation
                    outranking[a][b] = 'none'
    return outranking


def main():
    try:
        args = docopt(__doc__, version=__version__)
        input_dir, output_dir = get_dirs(args)
        filenames = [
            # every tuple below == (filename, is_optional)
            ('alternatives.xml', False),
            ('categories_profiles.xml', True),
            ('credibility.xml', False),
            ('method_parameters.xml', False),
        ]
        params = [
            'alternatives',
            'categories_profiles',
            'comparison_with',
            'credibility',
            'cut_threshold',
        ]
        d = get_input_data(input_dir, filenames, params)

        # getting the elements to compare
        comparables_a = d.alternatives
        if d.comparison_with in ('boundary_profiles', 'central_profiles'):
            comparables_b = d.categories_profiles
        else:
            comparables_b = d.alternatives

        outranking = get_outranking_relation(
            comparables_a,
            comparables_b,
            d.credibility,
            d.cut_threshold,
        )

        # serialization etc.
        if d.comparison_with in ('boundary_profiles', 'central_profiles'):
            mcda_concept = 'alternativesProfilesComparisons'
        else:
            mcda_concept = None
        comparables = (comparables_a, comparables_b)
        xmcda = comparisons_to_xmcda(outranking, comparables, mcda_concept=mcda_concept)
        write_xmcda(xmcda, os.path.join(output_dir, 'outranking.xml'))
        create_messages_file(('Everything OK.',), None, output_dir)
        return 0
    except Exception, err:
        traceback.print_exc()
        err_msg = get_error_message(err)
        create_messages_file(None, (err_msg, ), output_dir)
        return 1


if __name__ == '__main__':
    sys.exit(main())

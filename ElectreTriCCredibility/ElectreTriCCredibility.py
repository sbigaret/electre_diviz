#!/usr/bin/env python

"""
ElectreTriCCredibility - computes credibility matrix as presented in Electre
Tri-C method.

It uses the same procedure as in ElectreTriCredibility - only the input files
are slightly different (central reference actions instead boundary actions).

Usage:
    ElectreTriCCredibility.py -i DIR -o DIR

Options:
    -i DIR     Specify input directory. It should contain following files
               (otherwise program will throw an error):
                   alternatives.xml
                   categoriesProfiles.xml
                   concordance.xml
                   discordances.xml
    -o DIR     Specify output directory.
    --version  Show version.
    -h --help  Show this screen.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from collections import OrderedDict
import os
import sys
import traceback

from docopt import docopt
import PyXMCDA as px

from common import (
    comparisons_to_xmcda,
    create_messages_file,
    get_categories_profiles_central,
    get_dirs,
    get_error_message,
    get_trees,
    getAlternativesComparisons,
    reverseAltComparisons,
    unreverseAltComparisons,
    write_xmcda,
)

__version__ = '0.1.0'


def get_credibility(concordance, discordances, alternatives, categories_profiles):

    def _calculate_credibility_idx(concordance, discordances):
        index = concordance * reduce(
            lambda x, y: x * y,
            [(1 - d) / (1 - concordance) for d in discordances.values() if d > concordance]
        )
        return index

    uc = unreverseAltComparisons(concordance, alternatives, categories_profiles)
    ud = unreverseAltComparisons(discordances, alternatives, categories_profiles)
    concordance_ap, concordance_pa = uc
    discordances_ap, discordances_pa = ud

    credibility_ap = OrderedDict()
    credibility_pa = OrderedDict()
    for a in alternatives:
        indices_ap = OrderedDict()
        indices_pa = OrderedDict()
        for p in categories_profiles:

            # alternative-profile
            if set(discordances_ap[a][p].values()) == set([0]):  # only zeros
                index_ap = concordance_ap[a][p]
            elif 1 in discordances_ap[a][p].values():  # at least one '1'
                if not concordance_ap[a][p] < 1:
                    raise RuntimeError("When discordance == 1, concordance must be < 1.")
                index_ap = 0
            else:
                C_ap = concordance_ap[a][p]
                d_ap = discordances_ap[a][p]
                index_ap = _calculate_credibility_idx(C_ap, d_ap)

            # profile-alternative
            if set(discordances_pa[a][p].values()) == set([0]):
                index_pa = concordance_pa[a][p]
            elif 1 in discordances_pa[a][p].values():
                if not concordance_pa[a][p] < 1:
                    raise RuntimeError("When discordance == 1, concordance must be < 1.")
                index_pa = 0
            else:
                C_pa = concordance_pa[a][p]
                d_pa = discordances_pa[a][p]
                index_pa = _calculate_credibility_idx(C_pa, d_pa)

            indices_ap[p] = index_ap
            indices_pa[p] = index_pa
        credibility_ap[a] = indices_ap
        credibility_pa[a] = indices_pa

    ret = reverseAltComparisons(
        credibility_ap,
        credibility_pa,
        alternatives,
        categories_profiles,
    )
    return ret


def get_input_data(input_dir):
    file_names = (
        'alternatives.xml',
        'categoriesProfiles.xml',
        'concordance.xml',
        'discordances.xml',
    )
    trees = get_trees(input_dir, file_names)

    alternatives = px.getAlternativesID(trees['alternatives'])
    categories_profiles = get_categories_profiles_central(trees['categoriesProfiles'])
    concordance = getAlternativesComparisons(trees['concordance'], alternatives,
                                             categories_profiles)
    discordances = getAlternativesComparisons(trees['discordances'], alternatives,
                                              categories_profiles, partials=True)

    ret = {
        'alternatives': alternatives,
        'categories_profiles': categories_profiles,
        'concordance': concordance,
        'discordances': discordances,
    }
    return ret


def main():
    try:
        args = docopt(__doc__, version=__version__)
        input_dir, output_dir = get_dirs(args)
        input_data = get_input_data(input_dir)

        concordance = input_data['concordance']
        discordances = input_data['discordances']
        alternatives = input_data['alternatives']
        categories_profiles = input_data['categories_profiles']

        credibility = get_credibility(concordance, discordances, alternatives,
                                      categories_profiles)

        xmcda = comparisons_to_xmcda(credibility,
                                     mcdaConcept="alternativesProfilesComparisons")
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

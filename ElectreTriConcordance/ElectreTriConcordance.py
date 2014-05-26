#!/usr/bin/env python

"""
ElectreTriConcordance - computes concordance matrix as in Electre TRI method.

It uses the same procedure as in ElectreTriCConcordance - only the input files
are slightly different (boundary actions instead of central reference actions).

This module (along with ElectreTriClassAssign, ElectreTriDiscordances and
ElectreTriCredibility) is equal to ElectreTriExploitation module split into
four separate parts for user's convenience.

Usage:
    ElectreTriConcordance.py -i DIR -o DIR

Options:
    -i DIR     Specify input directory. It should contain following files
               (otherwise program will throw an error):
                   alternatives.xml
                   categoriesProfiles.xml
                   criteria.xml
                   performanceTable.xml
                   profilesPerformanceTable.xml
                   weights.xml
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
    get_concordance,
    get_dirs,
    get_error_message,
    get_trees,
    reverseAltComparisons,
    write_xmcda,
)

__version__ = '0.1.0'


def get_input_data(input_dir):
    file_names = (
        'alternatives.xml',
        'performanceTable.xml',
        'categoriesProfiles.xml',
        'criteria.xml',
        'profilesPerformanceTable.xml',
        'weights.xml',
    )
    trees = get_trees(input_dir, file_names)

    alternatives = px.getAlternativesID(trees['alternatives'])
    criteria = px.getCriteriaID(trees['criteria'])
    pref_directions = px.getCriteriaPreferenceDirections(trees['criteria'], criteria)
    thresholds = px.getConstantThresholds(trees['criteria'], criteria)
    weights = px.getCriterionValue(trees['weights'], criteria)
    performances = px.getPerformanceTable(trees['performanceTable'], 1, 1)

    # we can't assume that categories will be always available as a separate
    # input file, therefore it's better to extract them from categoriesProfiles
    cp_tree = trees['categoriesProfiles']
    categories = list(set(cp_tree.xpath('//categoriesProfiles//limits//categoryID/text()')))
    # since we just need names of categories profiles, it's better to get them like below
    # - otherwise, to get 'full' categories profiles, we should use this:
    # categories_profiles = px.getCategoriesProfiles(trees['categoriesProfiles'], categories)
    categories_profiles = [p for p in cp_tree.xpath('//categoriesProfiles//alternativeID/text()')]
    # last two args to getPerformanceTable are not used at all anyway...
    profiles_performance_table = px.getPerformanceTable(trees['profilesPerformanceTable'], None, None)

    ret = {
        'alternatives': alternatives,
        'categories_profiles': categories_profiles,
        'criteria': criteria,
        'performances': performances,
        'pref_directions': pref_directions,
        'profiles_performance_table': profiles_performance_table,
        'thresholds': thresholds,
        'weights': weights,
    }
    return ret


def main():
    try:
        args = docopt(__doc__, version=__version__)
        input_dir, output_dir = get_dirs(args)
        input_data = get_input_data(input_dir)

        alternatives = input_data['alternatives']
        categories_profiles = input_data['categories_profiles']
        performances = input_data['performances']
        profiles_performance_table = input_data['profiles_performance_table']
        criteria = input_data['criteria']
        pref_directions = input_data['pref_directions']
        thresholds = input_data['thresholds']
        weights = input_data['weights']

        concordance = get_concordance(alternatives, categories_profiles, performances,
                                      profiles_performance_table, criteria, thresholds,
                                      pref_directions, weights)

        xmcda = comparisons_to_xmcda(concordance, mcdaConcept="alternativesProfilesComparisons")
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

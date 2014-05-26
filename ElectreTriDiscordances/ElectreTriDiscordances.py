#!/usr/bin/env python

"""
ElectreTriDiscordances - computes partial (i.e. per-criterion) discordances as
in Electre TRI method.

It uses the same procedure as in ElectreTriCDiscordances - only the input files
are slightly different (boundary actions instead of central reference actions).

This module (along with ElectreTriClassAssign, ElectreTriConcordance and
ElectreTriCredibility) is equal to ElectreTriExploitation module split into
four separate parts for user's convenience.

Usage:
    ElectreTriDiscordances.py -i DIR -o DIR

Options:
    -i DIR     Specify input directory. It should contain following files
               (otherwise program will throw an error):
                   alternatives.xml
                   categoriesProfiles.xml
                   criteria.xml
                   performanceTable.xml
                   profilesPerformanceTable.xml
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
    reverseAltComparisons,
    write_xmcda,
)

__version__ = '0.1.0'


def get_discordances(alternatives, categories_profiles, criteria, thresholds,
                     performances, pref_directions, profiles_performance_table):

    def _omega(x, y):
        # 'x' and 'y' to keep it as general as possible
        if pref_directions[criterion] == 'max':
            return x - y
        if pref_directions[criterion] == 'min':
            return y - x

    def _get_partial_discordances(x, y, criterion):
        p = thresholds[criterion].get('pref')
        v = thresholds[criterion].get('veto')
        if not v:
            return 0
        if _omega(x, y) >= -p:
            return 0
        elif _omega(x, y) < -v:
            return 1
        else:
            return (_omega(x, y) + p) / (p - v)

    discordances_ap = OrderedDict()
    discordances_pa = OrderedDict()
    for a in alternatives:
        p_dict_ap = OrderedDict()
        p_dict_pa = OrderedDict()
        for p in categories_profiles:
            d_dict_ap = OrderedDict()
            d_dict_pa = OrderedDict()
            for criterion in criteria:

                # compare alternatives with profiles
                x = performances[a][criterion]
                y = profiles_performance_table[p][criterion]
                d_ap = _get_partial_discordances(x, y, criterion)

                # compare profiles with alternatives
                x = profiles_performance_table[p][criterion]
                y = performances[a][criterion]
                d_pa = _get_partial_discordances(x, y, criterion)

                d_dict_ap.update({criterion: d_ap})
                d_dict_pa.update({criterion: d_pa})
            p_dict_ap.update({p: d_dict_ap})
            p_dict_pa.update({p: d_dict_pa})
        discordances_ap.update({a: p_dict_ap})
        discordances_pa.update({a: p_dict_pa})

    ret = reverseAltComparisons(
        discordances_ap,
        discordances_pa,
        alternatives,
        categories_profiles,
    )
    return ret


def get_input_data(input_dir):
    file_names = (
        'alternatives.xml',
        'performanceTable.xml',
        'categoriesProfiles.xml',
        'criteria.xml',
        'profilesPerformanceTable.xml',
    )
    trees = get_trees(input_dir, file_names)

    alternatives = px.getAlternativesID(trees['alternatives'])
    criteria = px.getCriteriaID(trees['criteria'])
    pref_directions = px.getCriteriaPreferenceDirections(trees['criteria'], criteria)
    thresholds = px.getConstantThresholds(trees['criteria'], criteria)
    performances = px.getPerformanceTable(trees['performanceTable'], None, None)
    profiles_performance_table = px.getPerformanceTable(trees['profilesPerformanceTable'], None, None)
    cp_tree = trees['categoriesProfiles']
    # we need only categories profiles' names
    categories_profiles = [p for p in cp_tree.xpath('//categoriesProfiles//alternativeID/text()')]

    ret = {
        'alternatives': alternatives,
        'categories_profiles': categories_profiles,
        'criteria': criteria,
        'performances': performances,
        'pref_directions': pref_directions,
        'profiles_performance_table': profiles_performance_table,
        'thresholds': thresholds,
    }
    return ret


def main():
    try:
        args = docopt(__doc__, version=__version__)
        input_dir, output_dir = get_dirs(args)
        input_data = get_input_data(input_dir)

        alternatives = input_data['alternatives']
        categories_profiles = input_data['categories_profiles']
        criteria = input_data['criteria']
        thresholds = input_data['thresholds']
        performances = input_data['performances']
        pref_directions = input_data['pref_directions']
        profiles_performance_table = input_data['profiles_performance_table']

        discordances = get_discordances(alternatives, categories_profiles, criteria,
                                        thresholds, performances, pref_directions,
                                        profiles_performance_table)

        xmcda = comparisons_to_xmcda(discordances, partials=True,
                                     mcdaConcept="alternativesProfilesComparisons")
        write_xmcda(xmcda, os.path.join(output_dir, 'discordances.xml'))
        create_messages_file(('Everything OK.',), None, output_dir)
        return 0
    except Exception, err:
        traceback.print_exc()
        err_msg = get_error_message(err)
        create_messages_file(None, (err_msg, ), output_dir)
        return 1

if __name__ == '__main__':
    sys.exit(main())

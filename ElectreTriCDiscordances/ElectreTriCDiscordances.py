#!/usr/bin/env python

"""
ElectreTriCDiscordances - computes partial (i.e. per-criterion) discordances as
in Electre Tri-C method.

It uses the same procedure as in ElectreTriDiscordances - only the input files
are slightly different (central reference actions instead boundary actions)

Usage:
    ElectreTriCDiscordances.py -i DIR -o DIR

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

    def _get_advantage(performance_a, performance_b, pref_direction):
        if pref_direction == 'max':
            advantage = performance_a - performance_b
        elif pref_direction == 'min':
            advantage = performance_b - performance_a
        else:
            raise RuntimeError('No valid preference direction specified.')
        return advantage

    def _get_d(advantage, p_threshold, v_threshold):
        if advantage >= -p_threshold:
            d = 0.0
        elif -v_threshold <= advantage < -p_threshold:
            d = (advantage + p_threshold) / (p_threshold - v_threshold)
        elif advantage < -v_threshold:
            d = 1.0
        return d

    discordances_ap = OrderedDict()
    discordances_pa = OrderedDict()
    for a in alternatives:
        p_dict_ap = OrderedDict()
        p_dict_pa = OrderedDict()
        for p in categories_profiles:
            d_dict_ap = OrderedDict()
            d_dict_pa = OrderedDict()
            for criterion in criteria:
                if not thresholds[criterion].get('veto'):
                    d_dict_ap.update({criterion: 0.0})
                    d_dict_pa.update({criterion: 0.0})
                    continue
                p_threshold = thresholds[criterion]['preference']
                v_threshold = thresholds[criterion]['veto']
                a_perf = performances[a][criterion]
                p_perf = profiles_performance_table[p][criterion]
                advantage_ap = _get_advantage(a_perf, p_perf, pref_directions[criterion])
                advantage_pa = _get_advantage(p_perf, a_perf, pref_directions[criterion])
                d_ap = _get_d(advantage_ap, p_threshold, v_threshold)
                d_pa = _get_d(advantage_pa, p_threshold, v_threshold)
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
        'categoriesProfiles.xml',
        'criteria.xml',
        'performanceTable.xml',
        'profilesPerformanceTable.xml',
    )
    trees = get_trees(input_dir, file_names)

    alternatives = px.getAlternativesID(trees['alternatives'])
    criteria = px.getCriteriaID(trees['criteria'])
    pref_directions = px.getCriteriaPreferenceDirections(trees['criteria'], criteria)
    thresholds = px.getConstantThresholds(trees['criteria'], criteria)
    performances = px.getPerformanceTable(trees['performanceTable'], None, None)
    categories_profiles = get_categories_profiles_central(trees['categoriesProfiles'])
    profiles_performance_table = px.getPerformanceTable(
        trees['profilesPerformanceTable'], None, None
    )

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

#!/usr/bin/env python

"""
ElectreCriteriaInteractionsConcordance - computes concordance matrix taking
into account interactions between criteria. Possible interactions are:
'strengthening', 'weakening' and 'antagonistic'.

Please note that in its current version, this module doesn't allow to compute
concordance for methods belonging to Electre TRI family (i.e. the ones where we
have alternatives vs profiles comparisons).

Usage:
    ElectreCriteriaInteractionsConcordance.py -i DIR -o DIR

Options:
    -i DIR     Specify input directory. It should contain following files
               (otherwise program will throw an error):
                   alternatives.xml
                   criteria.xml
                   method_parameters.xml
                   performance_table.xml
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
from itertools import chain
import os
import sys
import traceback

from docopt import docopt
import PyXMCDA as px

from common import (
    comparisons_to_xmcda,
    create_messages_file,
    get_dirs,
    get_error_message,
    get_trees,
    write_xmcda,
)

__version__ = '0.1.0'

def get_criteria_interactions(xmltree, criteria_allowed):
    # in returned dict 'interactions', the most outer key designates direction
    # of the interaction effect (i.e. which criterion is affected), which is
    # significant in case of 'antagonistic' interaction
    interaction_types_allowed = ['strengthening', 'weakening', 'antagonistic']
    path = 'criteriaValues[@mcdaConcept="criteriaInteractions"]/criterionValue'
    interactions = {}
    cvs = xmltree.xpath(path)
    if not cvs:
        raise RuntimeError("Wrong or missing definitions for criteria interactions.")
    for cv in cvs:
        interaction_type = cv.attrib.get('mcdaConcept')
        if interaction_type not in interaction_types_allowed:
            raise RuntimeError("Wrong interaction type '{}'.".format(interaction_type))
        criteria_involved = cv.xpath('.//criterionID/text()')
        if len(criteria_involved) != 2:
            raise RuntimeError("Wrong number of criteria for '{}' interaction.".format(interaction_type))
        for criterion in criteria_involved:
            if criterion not in criteria_allowed:
                raise RuntimeError("Unknown criterion '{}' for '{}' interaction.".format(criterion, interaction_type))
        interaction_value = float(cv.find('./value//').text)
        if ((interaction_value > 0 and interaction_type == 'weakening') or
                (interaction_value < 0 and interaction_type in ('strengthening', 'antagonistic')) or
                (interaction_value == 0)):
            raise RuntimeError("Wrong value for '{}' interaction.".format(interaction_type))
        if interaction_type == 'strengthening' and 'weakening' in interactions.keys():
            for i in interactions['weakening']:
                if set(i[:2]) == set(criteria_involved):
                    raise RuntimeError("'strengthening' and 'weakening' interactions are mutually exclusive.")
        elif interaction_type == 'weakening' and 'strengthening' in interactions.keys():
            for i in interactions['strengthening']:
                if set(i[:2]) == set(criteria_involved):
                    raise RuntimeError("'strengthening' and 'weakening' interactions are mutually exclusive.")
        c1, c2 = criteria_involved
        try:
            interactions[interaction_type].append((c1, c2, interaction_value))
        except KeyError:
            interactions.update({interaction_type: [(c1, c2, interaction_value)]})
    return interactions


def check_net_balance(interactions, weights):
    criteria_affected = set([i[0] for i in chain(interactions.get('weakening', []), interactions.get('antagonistic', []))])
    for criterion in criteria_affected:
        weakening_sum = sum([abs(i[2]) for i in interactions.get('weakening', []) if i[0] == criterion])
        antagonistic_sum = sum([i[2] for i in interactions.get('antagonistic', []) if i[0] == criterion])
        net_balance = weights[criterion] - (weakening_sum + antagonistic_sum)
        if net_balance <= 0:
            raise RuntimeError("Positive net balance condition not fulfilled for criterion '{}'.".format(criterion))


def get_input_data(input_dir):
    file_names = (
        'alternatives.xml',
        'criteria.xml',
        'method_parameters.xml',
        'performance_table.xml',
        'weights.xml',
        'interactions.xml',
    )
    trees = get_trees(input_dir, file_names)

    alternatives = px.getAlternativesID(trees['alternatives'])
    criteria = px.getCriteriaID(trees['criteria'])
    pref_directions = px.getCriteriaPreferenceDirections(trees['criteria'], criteria)
    thresholds = px.getConstantThresholds(trees['criteria'], criteria)
    weights = px.getCriterionValue(trees['weights'], criteria)
    performances = px.getPerformanceTable(trees['performance_table'], 1, 1)
    interactions = get_criteria_interactions(trees['interactions'], criteria)

    check_net_balance(interactions, weights)
    z_function = px.getParameterByName(trees['method_parameters'], 'z_function')

    ret = {
        'alternatives': alternatives,
        'criteria': criteria,
        'interactions': interactions,
        'performances': performances,
        'pref_directions': pref_directions,
        'thresholds': thresholds,
        'weights': weights,
        'z_function': z_function,
    }
    return ret


def get_concordance(alternatives, performances, criteria, thresholds,
                    pref_directions, weights, interactions, z_function):

    if z_function == 'multiplication':
        Z = lambda x, y: x * y
    elif z_function == 'minimum':
        Z = lambda x, y: min(x, y)
    else:
        raise RuntimeError("Invalid Z function: '{}'.".format(z_function))

    def _omega(x, y):
        # 'x' and 'y' to keep it as general as possible
        if pref_directions[criterion] == 'max':
            return x - y
        if pref_directions[criterion] == 'min':
            return y - x

    def _get_partial_concordance(x, y, criterion):
        p = thresholds[criterion].get('preference')
        q = thresholds[criterion].get('indifference')
        if _omega(x, y) < -p:
            return float(0)
        elif _omega(x, y) >= -q:
            return float(1)
        else:
            return (_omega(x, y) + p) / (p - q)

    partial_concordances = {}
    for a in alternatives:
        p_dict = {}
        for b in alternatives:
            c_dict = {}
            for criterion in criteria:
                c = _get_partial_concordance(performances[a][criterion],
                                             performances[b][criterion], criterion)
                c_dict.update({criterion: c})
            p_dict.update({b: c_dict})
        partial_concordances.update({a: p_dict})

    # aggregate partial concordances (taking criteria interactions into account)
    aggregated_concordances = OrderedDict()
    for a in alternatives:
        row = OrderedDict()
        for b in alternatives:
            if a == b:
                C = 1.0
            else:
                sum_cki = sum([partial_concordances[a][b][c] * weights[c] for c in criteria])
                sum_kij = float(0)
                for interaction_name in ('strengthening', 'weakening'):
                    for interaction in interactions.get(interaction_name, []):
                        ci = partial_concordances[a][b][interaction[0]]
                        cj = partial_concordances[a][b][interaction[1]]
                        sum_kij += Z(ci, cj) * interaction[2]
                sum_kih = float(0)
                for interaction in interactions.get('antagonistic', []):
                    ci = partial_concordances[a][b][interaction[0]]
                    ch = partial_concordances[b][a][interaction[1]]
                    sum_kih += Z(ci, ch) * interaction[2]
                sum_ki = sum(weights.values())  # this is only for K
                K = sum_ki + sum_kij - sum_kih
                C = (sum_cki + sum_kij - sum_kih) / K
            row.update({b: C})
        aggregated_concordances.update({a: row})

    # # aggregate partial concordances ('normal' aggregation, w/o taking into accout
    # # criteria interactions - I left it here for testing purposes)
    # aggregated_concordances = OrderedDict()
    # sum_of_weights = sum([weights[criterion] for criterion in criteria])
    # for a in alternatives:
    #     p_dict = OrderedDict()
    #     for b in alternatives:
    #         # 'C' - aggregated, 'c' - partial
    #         C = sum([weights[criterion] * partial_concordances[a][b][criterion]
    #                  for criterion in criteria]) / sum_of_weights
    #         p_dict.update({b: C})
    #     aggregated_concordances.update({a: p_dict})

    return aggregated_concordances


def main():
    try:
        args = docopt(__doc__, version=__version__)
        input_dir, output_dir = get_dirs(args)
        input_data = get_input_data(input_dir)

        alternatives = input_data['alternatives']
        performances = input_data['performances']
        criteria = input_data['criteria']
        interactions = input_data['interactions']
        pref_directions = input_data['pref_directions']
        thresholds = input_data['thresholds']
        weights = input_data['weights']
        z_function = input_data['z_function']

        concordance = get_concordance(alternatives, performances, criteria, thresholds,
                                      pref_directions, weights, interactions, z_function)

        xmcda = comparisons_to_xmcda(concordance)
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

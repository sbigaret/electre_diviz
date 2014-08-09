#!/usr/bin/env python

"""
ElectreTri-CClassAssignments - computes class assignments according to the
Electre TRI-C method.

This method uses central reference actions (profiles) instead of boundary
actions known from Electre TRI.

Usage:
    ElectreTri-CClassAssignments.py -i DIR -o DIR

Options:
    -i DIR     Specify input directory. It should contain the following files:
                   alternatives.xml
                   classes.xml
                   classes_profiles.xml
                   credibility.xml
                   outranking.xml
    -o DIR     Specify output directory. Files generated as output:
                   assignments.xml
                   messages.xml
    --version  Show version.
    -h --help  Show this screen.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys
import traceback

from docopt import docopt

from common import assignments_as_intervals_to_xmcda, create_messages_file, \
    get_dirs, get_error_message, get_input_data, get_relation_type, write_xmcda

__version__ = '0.2.0'


def assign_class(alternatives, categories_rank, categories_profiles,
                 outranking, credibility):
    # sort categories by their rank, but we want the worst one on the 'left'
    # - hence 'reverse=True'
    categories = [i[0] for i in sorted(categories_rank.items(),
                                       key=lambda x: x[1], reverse=True)]
    # get a list of profiles sorted accordingly to the above
    profiles = [i[0] for i in sorted(categories_profiles.items(),
                                     key=lambda x: categories.index(x[1]))]
    assignments_descending = []; assignments_ascending = []
    for a in alternatives:
        # direction: rank n <--- rank 1 (from the most to the least preferred)
        found_descending = False
        for p in profiles[len(profiles) - 2:: -1]:
            p_next = profiles[profiles.index(p) + 1]
            relation_ap = get_relation_type(a, p, outranking)
            relation_apn = get_relation_type(a, p_next, outranking)
            if (relation_ap == 'preference' and
                    (credibility[a][p_next] > credibility[p][a] or
                        credibility[a][p_next] >= credibility[p][a] and
                        relation_apn == 'incomparability')):
                category = categories_profiles.get(p_next)
                assignments_descending.append((a, category))
                found_descending = True
                break
        if not found_descending:
            # formally, here we make comparison with the 'worst' profile,
            # but since that always returns True, we just assign to C_h+1
            # (similar situation below - 'if not found_ascending...')
            assignments_descending.append((a, categories[0]))
        # direction: rank n ---> rank 1 (from the least to the most preferred)
        found_ascending = False
        for p in profiles[1:]:
            p_prev = profiles[profiles.index(p) - 1]
            relation_pa = get_relation_type(p, a, outranking)
            relation_app = get_relation_type(a, p_prev, outranking)
            if (relation_pa == 'preference' and
                    (credibility[p_prev][a] > credibility[a][p] or
                        credibility[p_prev][a] >= credibility[a][p] and
                        relation_app == 'incomparability')):
                category = categories_profiles.get(p_prev)
                assignments_ascending.append((a, category))
                found_ascending = True
                break
        if not found_ascending:
            assignments_ascending.append((a, categories[-1]))
    assignments = {}
    for i in zip(assignments_descending, assignments_ascending):
        assignments[i[0][0]] = (i[0][1], i[1][1])
    return assignments


def main():
    try:
        args = docopt(__doc__, version=__version__)
        output_dir = None
        input_dir, output_dir = get_dirs(args)
        filenames = [
            # every tuple below == (filename, is_optional)
            ('alternatives.xml', False),
            ('classes.xml', False),
            ('classes_profiles.xml', False),
            ('credibility.xml', False),
            ('outranking.xml', False),
        ]
        params = [
            'alternatives',
            'categories_profiles',
            'categories_rank',
            'credibility',
            'outranking',
        ]
        d = get_input_data(input_dir, filenames, params,
                           comparison_with='central_profiles')

        assignments = assign_class(d.alternatives, d.categories_rank,
                                   d.categories_profiles, d.outranking,
                                   d.credibility)

        # serialization etc.
        xmcda_assign = assignments_as_intervals_to_xmcda(assignments)
        write_xmcda(xmcda_assign, os.path.join(output_dir, 'assignments.xml'))
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

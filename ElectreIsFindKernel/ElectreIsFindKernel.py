#!/usr/bin/env python

"""
ElectreIsFindKernel - finds kernel of a graph (i.e. subset of best
alternatives) according to the procedure used by the Electre Is method. The
graph is generated from the outranking matrix provided as one of the input
files.

This module provides two methods of cycle elimination: by cutting weakest edge
(i.e. with the lowest weight) or by aggregation of the nodes, which is the
default. In case of the former method, it is required to provide a credibility
matrix as an additional input, since weights are derived from credibility
indices. Please note that these two methods may give different results.

Usage:
    ElectreIsFindKernel.py -i DIR -o DIR

Options:
    -i DIR     Specify input directory. It should contain the following files:
                   alternatives.xml
                   credibility.xml (optional)
                   method_parameters.xml
                   outranking.xml
    -o DIR     Specify output directory. Files generated as output:
                   kernel.xml
                   messages.xml
    --version  Show version.
    -h --help  Show this screen.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from copy import deepcopy
import itertools as it
import os
import sys
import traceback

from docopt import docopt
from lxml import etree
from networkx import DiGraph
from networkx.algorithms.cycles import simple_cycles

from common import (
    get_dirs,
    get_error_message,
    get_input_data,
    create_messages_file,
    write_xmcda,
)

__version__ = '0.2.0'

def build_graph(alternatives, outranking, credibility=False):
    # There are some conventions to follow here:
    # 1. labels (i.e. alternatives' ids) are kept in graph's dictionary (see: graph.graph)
    # 2. aggregated nodes (only numbers, as list) are kept under 'aggr' key in node's
    #    dict (see: graph.nodes(data=True))
    # 3. weights on the edges are kept under 'weight' key in edge's dict - similarly as
    #    with nodes (see: graph.edges(data=True))
    graph = DiGraph()  # we need directed graph for this
    # creating nodes...
    for i, alternative in enumerate(alternatives):
        graph.add_node(i)
        graph.graph.update({i: alternative})
    # creating edges...
    for i, alternative in enumerate(alternatives):
        relations = outranking.get(alternative)
        if not relations:  # if graph is built from intersectionDistillation
            continue
        for relation in relations.items():
            if relation[1] == 1.0:
                weight = credibility[alternative][relation[0]] if credibility else None
                graph.add_edge(i, alternatives.index(relation[0]), weight=weight)
    return graph


def find_kernel(graph, eliminate_cycles_method):

    def _remove_selfloops(g):
        for edge in g.edges():
            if len(set(edge)) == 1:
                g.remove_edge(*edge)  # '*' unpacks 'edge' tuple
        return g

    def _find_cycles(g):
        # XXX this function needs some serious refactoring
        # (duplicated fragments of code, cryptic variables' names etc.)
        C = []
        cycle = []
        a = {node: g.successors(node) for node in g.nodes()}
        # removing self-loops (we may also try g.nodes_with_selfloops)
        for k, v in a.iteritems():
            if k in v:
                v.remove(k)
        len_old = len(a)
        while len(a) > 0:
            empty_rows = []
            nodes_to_remove = []
            for node, succ in a.iteritems():
                if len(succ) == 0:              # if there are no successors...
                    empty_rows.append(node)     # mark this node for removal...
                    for i, j in a.iteritems():  # and traverse remaining lists of successors...
                        if node in j:           # looking for previously marked node...
                            nodes_to_remove.append((i, node))
            # actual nodes' removal (maybe dict's viewitems would simplify this?)
            for l in nodes_to_remove:  # 'l' == (row, index to remove)
                a[l[0]].remove(l[1])
            for l in empty_rows:
                a.pop(l)
            if len(a) == len_old:  # if we run out of nodes to remove, then stop
                break
            else:
                len_old = len(a)
        if len(a) > 0:  # which means that there are cycles
            # check if sequence of removed indices creates a cycle
            cycles = filter(lambda x: len(x) > 1, [set(c) for c in simple_cycles(g)])
            # pick arbitrary row/element for removal (e.g. first one)
            len_old = len(a)
            while True:
                # check if any combination of C's elements creates cycle
                if len(C) > 1:
                    c = []
                    for m in range(2, len(C) + 1):
                        c += [comb for comb in it.combinations(C, m)]
                    for n in c:
                        if set(n) in cycles:
                            cycle = list(n)
                            break
                if cycle:
                    break
                empty_rows = []
                nodes_to_remove = []
                if len(a) == len_old:             # if we've just started or there are no changes...
                    if len(a) == 1:
                        # this shouldn't happen
                        return []
                    a.items()[0][1].pop()         # take the first element and remove it
                for node, succ in a.iteritems():  # check for empty rows and remove them
                    if len(succ) == 0:
                        empty_rows.append(node)
                        for i, j in a.iteritems():
                            if node in j:
                                nodes_to_remove.append((i, node))
                for l in nodes_to_remove:
                    a[l[0]].remove(l[1])
                for l in empty_rows:
                    C.append(l)
                    a.pop(l)
                    len_old = len(a)
        return cycle

    def _cut_weakest(g, cycle):
        candidates = []
        for e in g.edges(data=True):
            if e[0] in cycle and e[1] in cycle:
                candidates.append(e)
        candidates.sort(key=lambda c: c[2].get('weight'), reverse=True)  # sorting by weights
        e = candidates.pop()
        g.remove_edge(e[0], e[1])
        return g

    def _aggregate_nodes(graph, cycle):
        graph = deepcopy(graph)
        new_node = max(graph.nodes()) + 1
        node_to_update = None
        for i in cycle:
            aggr = graph.node[i].get('aggr')
            if aggr:
                node_to_update = (i, aggr)
        graph.add_node(new_node, aggr=cycle)
        for node in cycle:
            for pred in graph.predecessors(node):
                if pred not in cycle:
                    graph.add_edge(pred, new_node)
            for succ in graph.successors(node):
                if succ not in cycle:
                    graph.add_edge(new_node, succ)
            graph.remove_node(node)
        if node_to_update:
            graph.node[new_node]['aggr'].remove(node_to_update[0])
            graph.node[new_node]['aggr'] += node_to_update[1]
            graph.node[new_node]['aggr'].sort()
        return graph

    def _eliminate_cycles(g, eliminate_cycles_method):
        if eliminate_cycles_method == 'cut_weakest':
            # since 'weights' can be either on all edges or on none of them,
            # we are checking just the first one
            if not g.edges(data=True)[0][2].get('weight'):
                raise RuntimeError("Can't use 'cut_weakest' method because input graph has no weights.")
            eliminate_fun = _cut_weakest
        else:  # 'aggregate' method
            eliminate_fun = _aggregate_nodes
        cycle = _find_cycles(g)
        while cycle:
            g = eliminate_fun(g, cycle)
            cycle = _find_cycles(g)
        return g

    graph = deepcopy(graph)
    graph = _remove_selfloops(graph)
    graph = _eliminate_cycles(graph, eliminate_cycles_method)
    kernel = []
    # XXX yes, I don't like those names with underscore postfixes either
    predecessors_per_node = {node: graph.predecessors(node) for node in graph.nodes()}
    while len(predecessors_per_node) > 0:
        for node, predecessors in predecessors_per_node.iteritems():
            if len(predecessors) == 0:
                kernel.append(node)
                predecessors_per_node.pop(node)
                nodes_to_remove = []
                for node_, predecessors_ in predecessors_per_node.iteritems():
                    if node in predecessors_:
                        nodes_to_remove.append(node_)
                        for predecessors__ in predecessors_per_node.itervalues():
                            if node_ in predecessors__:
                                predecessors__.remove(node_)
                for node_to_remove in nodes_to_remove:  # remove nodes added to the kernel
                    predecessors_per_node.pop(node_to_remove)
                break
    return kernel, graph


def get_kernel_as_labels(kernel, g):
    # convert aggregated nodes to un-aggregated (i.e. list of alternatives'
    # labels) in order to export them to XMCDA format
    nodes_numbers = []
    for node in kernel:
        nodes_numbers.append(node)
        try:
            nodes_numbers.extend(g.node[node].get('aggr'))
        except TypeError:
            pass
    kernel_as_labels = [v for k, v in g.graph.iteritems() if k in nodes_numbers]
    return kernel_as_labels


def kernel_to_xmcda(kernel):
    xmcda = etree.Element('alternativesSet', mcdaConcept="kernel")
    for alternative in kernel:
        element = etree.SubElement(xmcda, 'element')
        alt_id = etree.SubElement(element, 'alternativeID')
        alt_id.text = alternative
    return xmcda


def main():
    try:
        args = docopt(__doc__, version=__version__)
        output_dir = None
        input_dir, output_dir = get_dirs(args)
        filenames = [
            # every tuple below == (filename, is_optional)
            ('alternatives.xml', False),
            ('credibility.xml', True),
            ('method_parameters.xml', False),
            ('outranking.xml', False),
        ]
        params = [
            'alternatives',
            'credibility',
            'eliminate_cycles_method',
            'outranking',
        ]
        d = get_input_data(input_dir, filenames, params)

        graph = build_graph(d.alternatives, d.outranking, d.credibility)
        # because of the 'eliminate_cycles' routine used by 'find_kernel, a graph
        # is returned with the kernel which allows for further examination
        kernel, graph_without_cycles = find_kernel(graph, d.eliminate_cycles_method)
        kernel_as_labels = get_kernel_as_labels(kernel, graph_without_cycles)
        xmcda = kernel_to_xmcda(kernel_as_labels)
        write_xmcda(xmcda, os.path.join(output_dir, 'kernel.xml'))
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

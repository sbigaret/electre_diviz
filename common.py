# -*- coding: utf-8 -*-

from collections import OrderedDict
import os
import re

import PyXMCDA as px

from lxml import etree


HEADER = ("<?xml version='1.0' encoding='UTF-8'?>\n"
          "<xmcda:XMCDA xmlns:xmcda='http://www.decision-deck.org/2012/XMCDA-2.2.0'\n"
          "  xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'\n"
          "  xsi:schemaLocation='http://www.decision-deck.org/2012/XMCDA-2.2.0 http://www.decision-deck.org/xmcda/_downloads/XMCDA-2.2.0.xsd'>\n")
FOOTER = "</xmcda:XMCDA>"


class Vividict(dict):
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value


class InputData(object):
    # same as: InputData = type('InputData', (object,), {})
    pass


def get_input_data(input_dir, filenames, params, **kwargs):
    # This functions is pretty big and ugly, but at least it's easier to maintain
    # since everything now is in one place instead of being scattered/duplicated
    # amongst many different modules.

    def _get_trees(input_dir, filenames):
        trees = {}
        for f, is_optional in filenames:
            file_name = os.path.join(input_dir, f)
            if not os.path.isfile(file_name):
                if is_optional:
                    continue
                else:
                    raise RuntimeError("Problem with input file: '{}'.".format(f))
            tree = None
            tree = px.parseValidate(file_name)
            if tree is None:
                raise RuntimeError("Validation error with file: '{}'.".format(f))
            trees.update({os.path.splitext(f)[0]: tree})
        return trees

    def _create_data_object(params):
        obj = InputData()
        for p in params:
            setattr(obj, p, None)
        return obj

    def _get_categories_profiles(tree, comparison_with):
        # XXX not sure if it's a good idea to return two different data types here, i.e.:
        # for boundary profiles: ['b1', 'b2', 'b3', 'b4']
        # for central profiles: {'b4': 'C4', 'b5': 'C5', 'b1': 'C1', 'b2': 'C2', 'b3': 'C3'}

        def _get_profiles_ordering(last_found, profiles):
            """Gets the ordering of categories profiles."""
            for i in categories_profiles_full.values():
                if i.get('lower') == last_found:
                    if i.get('upper') is None:
                        return
                    profiles.append(i.get('upper'))
                    last_found = profiles[-1]
                    break
            _get_profiles_ordering(last_found, profiles)

        if comparison_with == 'alternatives':
            categories_profiles = None
        elif comparison_with == 'boundary_profiles':
            # ####### different options which are available here:
            # ### categories_profiles e.g. ['pMG', 'pBM']
            # path = '//categoriesProfiles//alternativeID/text()'
            # categories_profiles = [profile for profile in tree.xpath(path)]
            # ### categories_names e.g. ['Bad', 'Medium', 'Good']
            # categories_names = list(set(tree.xpath('//categoriesProfiles//limits//categoryID/text()')))
            # ### categories_profiles_full e.g. {'Bad': {'upper': 'pBM'}, 'Medium': {'upper': 'pMG', 'lower': 'pBM'}, 'Good': {'lower': 'pMG'}}
            # categories_profiles_full = px.getCategoriesProfiles(tree, categories_names)  # tri class assign
            categories_names = list(set(tree.xpath('//categoriesProfiles//limits//categoryID/text()')))
            categories_profiles_full = px.getCategoriesProfiles(tree, categories_names)
            categories_profiles = []
            _get_profiles_ordering(None, categories_profiles)
        elif comparison_with == 'central_profiles':
            categories_profiles = {}
            for xmlprofile in tree.findall(".//categoryProfile"):
                try:
                    profile_id = xmlprofile.find("alternativeID").text
                    category = xmlprofile.find("central/categoryID").text
                    categories_profiles[profile_id] = category
                except:
                    categories_profiles = {}
                    break
        else:
            raise RuntimeError("Wrong comparison type ('{}') specified.".format(comparison_with))
        return categories_profiles

    def _get_criteria_interactions(xmltree, criteria_allowed):
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


    trees = _get_trees(input_dir, filenames)
    d = _create_data_object(params)
    for p in params:
        if p == 'alternatives':
            d.alternatives = px.getAlternativesID(trees['alternatives'])

        elif p == 'categories_profiles':
            comparison_with = kwargs.get('comparison_with')
            if comparison_with is None:
                comparison_with = px.getParameterByName(trees['method_parameters'], 'comparison_with')
            d.categories_profiles = _get_categories_profiles(trees.get('categories_profiles'),
                                                             comparison_with)

        elif p == 'categories_rank':
            categories = px.getCategoriesID(trees['categories'])
            d.categories_rank = px.getCategoriesRank(trees['categories'], categories)

        elif p == 'comparison_with':
            d.comparison_with = px.getParameterByName(trees['method_parameters'], 'comparison_with')

        elif p == 'concordance':
            alternatives = px.getAlternativesID(trees['alternatives'])
            comparison_with = px.getParameterByName(trees['method_parameters'], 'comparison_with')
            if comparison_with in ('boundary_profiles', 'central_profiles'):
                categories_profiles = _get_categories_profiles(trees['categories_profiles'],
                                                               comparison_with)
                d.concordance = get_alternatives_comparisons(trees['concordance'], alternatives,
                                                             categories_profiles)
            else:
                d.concordance = px.getAlternativesComparisons(trees['concordance'], alternatives)

        elif p == 'credibility':  # XXX dependence on method?
            alternatives = px.getAlternativesID(trees['alternatives'])
            comparison_with = kwargs.get('comparison_with')
            if not comparison_with:
                comparison_with = px.getParameterByName(trees['method_parameters'], 'comparison_with')
            if comparison_with in ('boundary_profiles', 'central_profiles'):
                categories_profiles = _get_categories_profiles(trees['categories_profiles'],
                                                            comparison_with)
            else:
                categories_profiles = None
            d.credibility = get_alternatives_comparisons(trees.get('credibility'), alternatives,
                                                         categories_profiles=categories_profiles)

        elif p == 'criteria':
            d.criteria = px.getCriteriaID(trees['criteria'])

        elif p == 'cut_threshold':  # XXX check
            d.cut_threshold = px.getParameterByName(trees['method_parameters'], 'cut_threshold')

        elif p == 'discordance':  # XXX dependence on method?
            alternatives = px.getAlternativesID(trees['alternatives'])
            comparison_with = px.getParameterByName(trees['method_parameters'], 'comparison_with')
            parameter = px.getParameterByName(trees['method_parameters'], 'use_partials')
            use_partials = True if parameter == 'true' else False
            if comparison_with in ('boundary_profiles', 'central_profiles'):
                categories_profiles = _get_categories_profiles(trees['categories_profiles'],
                                                               comparison_with)
            else:
                categories_profiles = None
            d.discordance = get_alternatives_comparisons(trees['discordance'], alternatives,
                                                         categories_profiles=categories_profiles,
                                                         use_partials=use_partials)

        elif p == 'eliminate_cycles_method':
            d.eliminate_cycles_method = px.getParameterByName(trees['method_parameters'],
                                                              'eliminate_cycles_method')

        elif p == 'interactions':  # XXX check
            criteria = px.getCriteriaID(trees['criteria'])
            d.interactions = _get_criteria_interactions(trees['interactions'], criteria)

        elif p == 'outranking':
            # XXX I don't really like how 'cutRelationCrisp' case is handled here
            alternatives = px.getAlternativesID(trees['alternatives'])
            outranking = get_intersection_distillation(trees['outranking'], alternatives)
            if outranking == None:
                outranking = px.getAlternativesComparisons(trees['outranking'], alternatives)
            if outranking == {}:  # XXX for cutRelationCrisp (alternativesComparisons with strings as values)
                comparison_with = kwargs.get('comparison_with')
                categories_profiles = _get_categories_profiles(trees.get('categories_profiles'),
                                                               comparison_with)
                outranking = get_alternatives_comparisons(trees['outranking'], alternatives,
                                                          categories_profiles=categories_profiles)
            d.outranking = outranking

        elif p == 'performances':
            d.performances = px.getPerformanceTable(trees['performance_table'], None, None)

        elif p == 'pref_directions':
            criteria = px.getCriteriaID(trees['criteria'])
            d.pref_directions = px.getCriteriaPreferenceDirections(trees['criteria'], criteria)

        elif p == 'profiles_performance_table':
            if comparison_with in ('boundary_profiles', 'central_profiles'):
                d.profiles_performance_table = px.getPerformanceTable(
                    trees['profiles_performance_table'], None, None)
            else:
                d.profiles_performance_table = None

        elif p == 'thresholds':
            criteria = px.getCriteriaID(trees['criteria'])
            d.thresholds = px.getConstantThresholds(trees['criteria'], criteria)

        elif p == 'weights':
            criteria = px.getCriteriaID(trees['criteria'])
            d.weights = px.getCriterionValue(trees['weights'], criteria)

        elif p == 'z_function':
            d.z_function = px.getParameterByName(trees['method_parameters'], 'z_function')

        elif p == 'use_1_minus_C':
            parameter = px.getParameterByName(trees['method_parameters'], 'use_1_minus_C')
            d.use_1_minus_C = True if parameter == 'true' else False

        elif p == 'use_partials':
            parameter = px.getParameterByName(trees['method_parameters'], 'use_partials')
            d.use_partials = True if parameter == 'true' else False

        else:
            raise RuntimeError("Unknown parameter '{}' specified.".format(p))

    return d


def get_dirs(args):
    input_dir = args.get('-i')
    output_dir = args.get('-o')
    for d in (input_dir, output_dir):
        if not os.path.isdir(output_dir):
            raise RuntimeError("Directory '{}' doesn't exist. Aborting.".format(d))
    return input_dir, output_dir

def comparisons_to_xmcda(comparisons, comparables, use_partials=False, mcda_concept=None):
    # 'comparables' should be a tuple e.g. (('a01', 'a02', 'a03', 'a04'), ('b01', 'b02')).
    # The order of nodes in xml file will be derived from its content.
    # All the sorting should be done here (i.e. just before serialization), I think.

    # XXX maybe it's better to get/set those types globally (i.e. for the whole file)?
    def _get_value_type(value):
        if type(value) == float:
            value_type = 'real'
        elif type(value) == int:
            value_type = 'integer'
        elif type(value) in (str, unicode):
            value_type = 'label'
        else:
            raise RuntimeError("Unknown type '{}'.".format(type(value)))
        return value_type

    if len(comparables) != 2:
        raise RuntimeError("Too many nesting levels '({})' for this serialization function.".format(len(ordering)))
    elif comparables[0] == comparables[1]:  # alternatives vs alternatives
        ordering = [(a, b) for a in comparables[0] for b in comparables[0]]
    else:  # alternatives vs profiles
        ordering = []
        for a in comparables[0]:
            for b in comparables[1]:
                ordering.append((a, b))
        for b in comparables[1]:
            for a in comparables[0]:
                ordering.append((b, a))
    if not mcda_concept:
        xmcda = etree.Element('alternativesComparisons')
    else:
        xmcda = etree.Element('alternativesComparisons', mcdaConcept=mcda_concept)
    pairs = etree.SubElement(xmcda, 'pairs')
    for alt1, alt2 in ordering:
        pair = etree.SubElement(pairs, 'pair')
        initial = etree.SubElement(pair, 'initial')
        alt_id = etree.SubElement(initial, 'alternativeID')
        alt_id.text = alt1
        terminal = etree.SubElement(pair, 'terminal')
        alt_id = etree.SubElement(terminal, 'alternativeID')
        alt_id.text = alt2
        if not use_partials:
            value_type = _get_value_type(comparisons[alt1][alt2])
            value_node = etree.SubElement(pair, 'value')
            v = etree.SubElement(value_node, value_type)
            v.text = str(comparisons[alt1][alt2])
        else:
            values = etree.SubElement(pair, 'values')
            items = comparisons[alt1][alt2].items()
            items.sort(key=lambda x: x[0])  # XXX until I find better solution
            for i in items:
                value_type = _get_value_type(i[1])
                value_node = etree.SubElement(values, 'value', id=i[0])
                v = etree.SubElement(value_node, value_type)
                v.text = str(i[1])
    return xmcda


def assignments_to_xmcda(assignments):
    # XXX maybe passing alternatives as a second argument and using them for sorting would be a good idea here?
    xmcda = etree.Element('alternativesAffectations')  # XXX affectations..?
    for assignment in sorted(assignments.items(), key=lambda x: x[0]):  # XXX same as in comparisons_to_xmcda
        alternative_assignment = etree.SubElement(xmcda, 'alternativeAffectation')
        alternative_id = etree.SubElement(alternative_assignment, 'alternativeID')
        alternative_id.text = assignment[0]
        category_id = etree.SubElement(alternative_assignment, 'categoryID')
        category_id.text = assignment[1]
    return xmcda


def assignments_as_intervals_to_xmcda(assignments):
    # XXX maybe passing alternatives as a second argument and using them for sorting would be a good idea here?
    xmcda = etree.Element('alternativesAffectations')  # XXX affectations..?
    for assignment in sorted(assignments.items(), key=lambda x: x[0]):  # XXX same as in comparisons_to_xmcda
        alternative_assignment = etree.SubElement(xmcda, 'alternativeAffectation')
        alternative_id = etree.SubElement(alternative_assignment, 'alternativeID')
        alternative_id.text = assignment[0]
        categories_interval = etree.SubElement(alternative_assignment, 'categoriesInterval')
        lower_bound = etree.SubElement(categories_interval, 'lowerBound')
        category_id = etree.SubElement(lower_bound, 'categoryID')
        category_id.text = assignment[1][0]  # 'descending', 'pessimistic', 'conjunctive'
        upper_bound = etree.SubElement(categories_interval, 'upperBound')
        category_id = etree.SubElement(upper_bound, 'categoryID')
        category_id.text = assignment[1][1]  # 'ascending', 'optimistic', 'disjunctive'
    return xmcda


def get_alternatives_comparisons(xmltree, alternatives, categories_profiles=None,
                                 use_partials=False, mcda_concept=None) :
    # 'use_partials' parameter designates whether the input contains 'partial'
    # (i.e. per-criterion) comparisons.

    def _get_value(value_node):
        if value_node.find('integer') is not None:
            value = int(value_node.find('integer').text)
        elif value_node.find('real') is not None:
            value = float(value_node.find('real').text)
        elif value_node.find('label') is not None:
            value = value_node.find('label').text
        else:
            value = None
        return value

    if xmltree is None:
        return None
    if mcda_concept == None :
        str_search = ".//alternativesComparisons"
    else :
        str_search = ".//alternativesComparisons[@mcdaConcept=\'" + mcda_concept + "\']"
    comparisons = xmltree.xpath(str_search)[0]
    if comparisons == None:
        return {}
    else:
        ret = Vividict()
        for pair in comparisons.findall("pairs/pair"):
            initial = pair.find("initial/alternativeID").text
            terminal = pair.find("terminal/alternativeID").text
            if not use_partials:
                value_node = pair.find("value")
                if value_node is None:
                    f = os.path.split(xmltree.base)[-1]
                    raise RuntimeError("Corrupted '{}' file or wrong value of 'use_partials' parameter.".format(f))
                value = _get_value(value_node)
            else:
                value_nodes = pair.find("values")
                if value_nodes is None:
                    f = os.path.split(xmltree.base)[-1]
                    raise RuntimeError("Corrupted '{}' file or wrong value of 'use_partials' parameter.".format(f))
                values = Vividict()
                for value_node in value_nodes:
                    value_node_id = value_node.get("id")
                    values[value_node_id] = _get_value(value_node)
            if initial in alternatives or initial in categories_profiles:
                if terminal in alternatives or terminal in categories_profiles:
                    if initial not in ret:
                        ret[initial] = Vividict()
                    ret[initial][terminal] = values if use_partials else value
        return ret


def write_xmcda(xmcda, filename):
    et = etree.ElementTree(xmcda)
    try:
        with open(filename, 'w') as f:
            f.write(HEADER)
            et.write(f, pretty_print=True, encoding='UTF-8')
            f.write(FOOTER)
    except IOError as e:
        raise IOError("{}: '{}'".format(e.strerror, e.filename))  # XXX IOError..?


def print_xmcda(xmcda):
    """Takes etree.Element as 'xmcda' and pretty-prints it."""
    print(etree.tostring(xmcda, pretty_print=True))


def create_messages_file(log_msg, err_msg, out_dir):
    with open(os.path.join(out_dir, 'messages.xml'), 'w') as f:
        px.writeHeader(f)
        if err_msg:
            px.writeErrorMessages(f, err_msg)
        elif log_msg:
            px.writeLogMessages(f, log_msg)
        else:
            px.writeErrorMessages(f, ('Neither log nor error messages have been supplied.',))
        px.writeFooter(f)


def get_intersection_distillation(xmltree, altId):
    """
    Allows for using intersectionDistillation.xml instead of outranking.xml.
    """
    mcdaConcept = 'Intersection of upwards and downwards distillation'
    strSearch = ".//alternativesComparisons[@mcdaConcept=\'" + mcdaConcept + "\']"
    comparisons = xmltree.xpath(strSearch)
    if comparisons == []:
        return
    else :
        comparisons = comparisons[0]
        datas = {}
        for pair in comparisons.findall ("pairs/pair") :
            init = pair.find("initial/alternativeID").text
            term = pair.find("terminal/alternativeID").text
            if altId.count(init) > 0 :
                if altId.count(term) > 0 :
                    if not(datas.has_key(init)) :
                        datas[init] = {}
                    datas[init][term] = 1.0
        return datas


def check_cut_threshold(threshold):
    if not 0.0 <= threshold <= 1.0:
        raise RuntimeError("Cut threshold should be in range <0.0, 1.0>.")


def get_error_message(err):
    exception = re.findall("\.([a-zA-Z]+)'", str(type(err)))[0]
    err_msg = ': '.join((exception, str(err)))
    return err_msg

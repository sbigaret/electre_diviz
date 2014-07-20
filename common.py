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


def get_input_data(input_dir, filenames, params):

    def _get_trees(input_dir, filenames):
        trees = {}
        for f, is_optional in filenames:
            file_name = os.path.join(input_dir, f)
            if not os.path.isfile(file_name) and not is_optional:
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
        if comparison_with == 'boundary_profiles':
            # # categories_profiles e.g. ['pMG', 'pBM']
            path = '//categoriesProfiles//alternativeID/text()'
            categories_profiles = [profile for profile in tree.xpath(path)]
            # # categories_names e.g. ['Bad', 'Medium', 'Good']
            # categories_names = list(set(tree.xpath('//categoriesProfiles//limits//categoryID/text()')))
            # # categories_profiles_full e.g. {'Bad': {'upper': 'pBM'}, 'Medium': {'upper': 'pMG', 'lower': 'pBM'}, 'Good': {'lower': 'pMG'}}
            # categories_profiles_full = px.getCategoriesProfiles(tree, categories_names)  # tri class assign
        elif comparison_with == 'central_profiles':
            categories_profiles = get_categories_profiles_central(tree)
        else:
            raise RuntimeError("Wrong comparison type ('{}') specified.".format(comparison_with))
        return categories_profiles

    trees = _get_trees(input_dir, filenames)
    d = _create_data_object(params)
    for p in params:
        if p == 'alternatives':
            d.alternatives = px.getAlternativesID(trees['alternatives'])
        elif p == 'categories_profiles':
            comparison_with = px.getParameterByName(trees['method_parameters'], 'comparison_with')
            d.categories_profiles = _get_categories_profiles(trees['categoriesProfiles'],
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
                categories_profiles = _get_categories_profiles(trees['categoriesProfiles'],
                                                               comparison_with)
                d.concordance = getAlternativesComparisons(trees['concordance'], alternatives,
                                                           categories_profiles)
            else:
                d.concordance = px.getAlternativesComparisons(trees['concordance'], alternatives)
        elif p == 'credibility':  # XXX dependence on method?
            alternatives = px.getAlternativesID(trees['alternatives'])
            comparison_with = px.getParameterByName(trees['method_parameters'], 'comparison_with')
            categories_profiles = _get_categories_profiles(trees['categoriesProfiles'],
                                                           comparison_with)
            d.credibility = getAlternativesComparisons(trees['credibility'], alternatives,
                                                       categories_profiles)
        elif p == 'criteria':
            d.criteria = px.getCriteriaID(trees['criteria'])
        elif p == 'cut_threshold':  # XXX check
            d.cut_threshold = px.getParameterByName(trees['method_parameters'], 'cut_threshold')
        elif p == 'discordances':  # XXX dependence on method?
            alternatives = px.getAlternativesID(trees['alternatives'])
            comparison_with = px.getParameterByName(trees['method_parameters'], 'comparison_with')
            categories_profiles = _get_categories_profiles(trees['categoriesProfiles'],
                                                           comparison_with)
            d.discordances = getAlternativesComparisons(trees['discordances'], alternatives,
                                                        categories_profiles, partials=True)
        elif p == 'discordance_binary':
            alternatives = px.getAlternativesID(trees['alternatives'])
            d.discordance_binary = px.getAlternativesComparisons(trees['discordance_binary'],
                                                                 alternatives)
        elif p == 'eliminate_cycles_method':
            d.eliminate_cycles_method = px.getParameterByName(trees['method_parameters'],
                                                              'eliminate_cycles_method')
        elif p == 'interactions':  # XXX check / get_criteria_interactions should be here
            criteria = px.getCriteriaID(trees['criteria'])
            d.interactions = get_criteria_interactions(trees['interactions'], criteria)
        elif p == 'outranking':
            alternatives = px.getAlternativesID(trees['alternatives'])
            outranking = get_intersection_distillation(trees['outranking'], alternatives)
            if outranking == None:
                outranking = px.getAlternativesComparisons(trees['outranking'], alternatives)
            d.outranking = outranking
        elif p == 'performances':
            d.performances = px.getPerformanceTable(trees['performanceTable'], None, None)
        elif p == 'pref_directions':
            criteria = px.getCriteriaID(trees['criteria'])
            d.pref_directions = px.getCriteriaPreferenceDirections(trees['criteria'], criteria)
        elif p == 'profiles_performance_table':
            d.profiles_performance_table = px.getPerformanceTable(trees['profilesPerformanceTable'],
                                                                  None, None)
        elif p == 'thresholds':
            criteria = px.getCriteriaID(trees['criteria'])
            d.thresholds = px.getConstantThresholds(trees['criteria'], criteria)
        elif p == 'weights':
            criteria = px.getCriteriaID(trees['criteria'])
            d.weights = px.getCriterionValue(trees['weights'], criteria)
        elif p == 'z_function':
            d.z_function = px.getParameterByName(trees['method_parameters'], 'z_function')
        else:
            raise RuntimeError("Unknown parameter '{}' specified.".format(p))
    return d


def DivizError(Error):  # XXX not used anywhere
    pass


def get_dirs(args):
    input_dir = args.get('-i')
    output_dir = args.get('-o')
    for d in (input_dir, output_dir):
        if not os.path.isdir(output_dir):
            raise RuntimeError("Directory '{}' doesn't exist. Aborting.".format(d))
    return input_dir, output_dir

def comparisons_to_xmcda(comparisons, comparables, partials=False, mcda_concept=None):
    # 'comparables' should be a tuple e.g. (('a01', 'a02', 'a03', 'a04'), ('b01', 'b02')).
    # The order of nodes in xml file will be derived from its content.
    if len(comparables) == 2:
        ordering = []  # all the sorting should be done just before serialization, I think
        for a in comparables[0]:
            for b in comparables[1]:
                ordering.append((a, b))
        for b in comparables[1]:
            for a in comparables[0]:
                ordering.append((b, a))
    elif len(comparables) == 1:
        ordering = [(a, b) for a in comparables[0] for b in comparables[0]]
    else:
        raise RuntimeError("Too many nesting levels '({})' for this serialization function.".format(len(ordering)))
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
        if not partials:
            value = etree.SubElement(pair, 'value')
            v = etree.SubElement(value, 'real')
            v.text = str(comparisons[alt1][alt2])
        else:
            values = etree.SubElement(pair, 'values')
            for i in comparisons[alt1][alt2].iteritems():
                value = etree.SubElement(values, 'value', id=i[0])
                v = etree.SubElement(value, 'real')
                v.text = str(i[1])
    return xmcda


def affectations_to_xmcda(affectations):
    xmcda = etree.Element('alternativesAffectations')
    for affectation in affectations.items():
        alternativeAffectation = etree.SubElement(xmcda, 'alternativeAffectation')
        alternativeID = etree.SubElement(alternativeAffectation, 'alternativeID')
        alternativeID.text = affectation[0]
        categoriesInterval = etree.SubElement(alternativeAffectation, 'categoriesInterval')
        lowerBound = etree.SubElement(categoriesInterval, 'lowerBound')
        categoryID = etree.SubElement(lowerBound, 'categoryID')
        categoryID.text = affectation[1][0]  # 'descending', 'pessimistic', 'conjunctive'
        upperBound = etree.SubElement(categoriesInterval, 'upperBound')
        categoryID = etree.SubElement(upperBound, 'categoryID')
        categoryID.text = affectation[1][1]  # 'ascending', 'optimistic', 'disjunctive'
    return xmcda


def get_categories_profiles_central(categories_profiles_tree):
    categoriesProfiles = OrderedDict()
    for xmlprofile in categories_profiles_tree.findall(".//categoryProfile"):
        try:
            profile_id = xmlprofile.find("alternativeID").text
            category = xmlprofile.find("central/categoryID").text
            categoriesProfiles[profile_id] = category
        except:
            return {}
    return categoriesProfiles


def getAlternativesComparisons(xmltree, alternatives, categoriesProfiles,
                               partials=False, mcdaConcept=None) :
    # XXX explain what 'partials' is
    if mcdaConcept == None :
        strSearch = ".//alternativesComparisons"
    else :
        strSearch = ".//alternativesComparisons[@mcdaConcept=\'" + mcdaConcept + "\']"
    comparisons = xmltree.xpath(strSearch)[0]
    if comparisons == None:
        return {}
    else:
        ret = OrderedDict()
        for pair in comparisons.findall ("pairs/pair"):
            init = pair.find("initial/alternativeID").text
            term = pair.find("terminal/alternativeID").text
            if not partials:
                val = getNumericValue(pair.find("value"))
            else:
                val = OrderedDict()
                for value in pair.find("values"):
                    valueID = value.get("id")
                    numVal = getNumericValue(value)
                    val[valueID] = numVal
            if init in alternatives or init in categoriesProfiles:
                if term in alternatives or term in categoriesProfiles:
                    if init not in ret:
                        ret[init] = OrderedDict()
                    ret[init][term] = val
        return ret


def getNumericValue(xmltree) :
    # changed from PyXMCDA's original in order to handle both concordance
    # and discordances

    # Only returns value if it is numeric
    try :
        if xmltree.find("integer") != None :
            val = int(xmltree.find("integer").text)
        elif xmltree.find("real") != None :
            val = float(xmltree.find("real").text)
        elif xmltree.find("rational") != None :
            val = float(xmltree.find("rational/numerator").text) / float(xmltree.find("rational/denominator").text)
        elif xmltree.find("NA") != None :
            val = "NA"
        else :
            val = None
    except :
        val = None
    return val


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

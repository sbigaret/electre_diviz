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


def DivizError(Error):  # XXX not used anywhere
    pass


def get_dirs(args):
    input_dir = args.get('-i')
    output_dir = args.get('-o')
    for d in (input_dir, output_dir):
        if not os.path.isdir(output_dir):
            raise RuntimeError("Directory '{}' doesn't exist. Aborting.".format(d))
    return input_dir, output_dir


def comparisons_to_xmcda(comparisons, partials=False, mcdaConcept=None):
    if not mcdaConcept:
        xmcda = etree.Element('alternativesComparisons')
    else:
        xmcda = etree.Element('alternativesComparisons', mcdaConcept=mcdaConcept)
    pairs = etree.SubElement(xmcda, 'pairs')
    for alt1 in comparisons.iterkeys():
        for alt2 in comparisons[alt1]:
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


def get_trees(input_dir, file_names):
    trees = {}
    for f in file_names:
        file_name = os.path.join(input_dir, f)
        if not os.path.isfile(file_name):
            raise RuntimeError("Problem with input file: '{}'.".format(f))
        tree = None
        tree = px.parseValidate(file_name)
        if tree is None:
            raise RuntimeError("Validation error with file: '{}'.".format(f))
        trees.update({os.path.splitext(f)[0]: tree})
    return trees


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


# Basically, this reversing/unreversing below applies only to the methods from
# Electre TRI family, i.e. where you compare alternatives with profiles, not
# alternatives with alternatives. In the former scenario you get comparisons
# resembling rectangular matrices (n x m) instead of square ones (n x n). But
# in our case, when this data is kept as dictionaries, it is more convenient to
# always access them with alternatives as the outermost indices. Threrefore, to
# serialize them in XMCDA format, we need to 'reverse' them, i.e. make profiles
# the outermost indices (and similarly when deserializing - hence 'unreverse').
#
# And since our dicts are always in form of e.g. d[alternative][profile], which
# is enough when we want to store the result of alternative-profile comparison,
# we need a way to store the results of profile-alternative comparisons as well
# - and that's exactly what all those '_ap' and '_pa' prefixes are for. So, for
# example:
#
#   concordance_ap['a01']['p01'] is for c(a01, p01)
#   concordance_pa['a01']['p01'] is for c(p01, a01)
#
# When we compare alternatives with alternatives (n x n matrices), such
# separation is not necessary, since everything is kept in the same dict, e.g.:
#
#   concordance['a01']['a02'] is for c(a01, a02)
#   concordance['a02']['a01'] is for c(a02, a01)

def reverseAltComparisons(comparisons_ap, comparisons_pa, alternatives, categoriesProfiles):
    comparisons_pa_reversed = OrderedDict()
    for p in categoriesProfiles:
        comparisons_pa_reversed.update({p: OrderedDict([(a, None) for a in alternatives])})
    for a in comparisons_pa:
        for p in comparisons_pa[a]:
            comparisons_pa_reversed[p][a] = comparisons_pa[a][p]
    comparisons_rev = OrderedDict()
    comparisons_rev.update(comparisons_ap)
    comparisons_rev.update(comparisons_pa_reversed)
    return comparisons_rev


def unreverseAltComparisons(comparisons, alternatives, categoriesProfiles):
    comparisons_ap = OrderedDict()
    comparisons_pa = OrderedDict()
    comparisons_pa_reversed = OrderedDict()
    for a in alternatives:
        comparisons_ap[a] = comparisons[a]
    for p in categoriesProfiles:
        comparisons_pa_reversed[p] = comparisons[p]
    for p in categoriesProfiles:
        for a in alternatives:
            if a not in comparisons_pa:
                comparisons_pa[a] = OrderedDict()
            comparisons_pa[a][p] = comparisons_pa_reversed[p][a]
    return comparisons_ap, comparisons_pa


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


def get_concordance(alternatives, categories_profiles, performances,
                    profiles_performance_table, criteria, thresholds,
                    pref_directions, weights):

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
            return 0
        elif _omega(x, y) >= -q:
            return 1
        else:
            return (_omega(x, y) + p) / (p - q)

    # compute partial concordances
    partial_concordances_ap = {}
    partial_concordances_pa = {}
    for a in alternatives:
        p_dict_ap = {}
        p_dict_pa = {}
        for p in categories_profiles:
            c_dict_ap = {}
            c_dict_pa = {}
            for criterion in criteria:
                # compare alternatives with profiles
                x = performances[a][criterion]
                y = profiles_performance_table[p][criterion]
                c_ap = _get_partial_concordance(x, y, criterion)
                # compare profiles with alternatives
                x = profiles_performance_table[p][criterion]
                y = performances[a][criterion]
                c_pa = _get_partial_concordance(x, y, criterion)
                c_dict_ap.update({criterion: c_ap})
                c_dict_pa.update({criterion: c_pa})
            p_dict_ap.update({p: c_dict_ap})
            p_dict_pa.update({p: c_dict_pa})
        partial_concordances_ap.update({a: p_dict_ap})
        partial_concordances_pa.update({a: p_dict_pa})

    # aggregate partial concordances
    aggregated_concordances_ap = OrderedDict()
    aggregated_concordances_pa = OrderedDict()
    sum_of_weights = sum([weights[criterion] for criterion in criteria])
    for a in alternatives:
        p_dict_ap = OrderedDict()
        p_dict_pa = OrderedDict()
        for p in categories_profiles:
            # 'C' - aggregated, 'c' - partial
            C_ap = sum([weights[criterion] * partial_concordances_ap[a][p][criterion]
                        for criterion in criteria]) / sum_of_weights
            C_pa = sum([weights[criterion] * partial_concordances_pa[a][p][criterion]
                        for criterion in criteria]) / sum_of_weights
            p_dict_ap.update({p: C_ap})
            p_dict_pa.update({p: C_pa})
        aggregated_concordances_ap.update({a: p_dict_ap})
        aggregated_concordances_pa.update({a: p_dict_pa})

    ret = reverseAltComparisons(
        aggregated_concordances_ap,
        aggregated_concordances_pa,
        alternatives,
        categories_profiles,
    )
    return ret


def check_cut_threshold(threshold):
    if not 0.0 <= threshold <= 1.0:
        raise RuntimeError("Cut threshold should be in range <0.0, 1.0>.")


def get_error_message(err):
    exception = re.findall("\.([a-zA-Z]+)'", str(type(err)))[0]
    err_msg = ': '.join((exception, str(err)))
    return err_msg

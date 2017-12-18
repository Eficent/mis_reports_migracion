# -*- coding: utf-8 -*-
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
#                <contact@eficent.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl
# pylint: disable=skip-file
# pylint: disable-all
import xml.etree.cElementTree as ET
import xml.etree.ElementTree as xml
from xml.etree import ElementTree
from xml.dom import minidom
import re


def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def parseXML(old_xml_file=None, new_xml_file=None, template_name=None,
             suffix=None, auto_expand_accounts=False):
    """
    Parse XML with ElementTree
    """
    tree = ET.ElementTree(file=old_xml_file)
    root = tree.getroot()
    new_root = xml.Element("odoo")
    new_data = xml.Element("data")
    new_root.append(new_data)
    sequence = 10
    new_report_id = ''
    debit_move_domain = "[('debit', '>', 0.0)]"
    credit_move_domain = "[('credit', '>', 0.0)]"
    if 'pyg' in new_xml_file:
        prefix = 'balp'
        # move_domain = "[('move_id.closing_type', '=', 'none')]"
        # debit_move_domain = "[('move_id.closing_type', '=', 'none'), " \
        #                     "('debit', '>', 0.0)]"
    else:
        prefix = 'bale'
        #move_domain = "[('move_id.closing_type', 'not in', ('closing', " \
        #              "'opening'))]"
        #debit_move_domain = "[('move_id.closing_type', 'not in', " \
        #                    "('closing', 'opening')),('debit', '>', 0.0)]"
        #credit_move_domain = "[('move_id.closing_type', 'not in', " \

    balance_model = 'debit-credit'
    for child in root:
        if child.tag == "record":
            new_record = xml.SubElement(new_data, "record")
            if 'model' in child.attrib.keys() and child.attrib['model'] == \
                    'account.balance.reporting.template':
                balance_model_elem = child.find(
                    './/field[@name="balance_mode"]')
                if balance_model_elem is not None:
                    if balance_model_elem.text == '2':
                        balance_model = 'credit-debit'
                old_id = child.attrib['id']
                new_report_id = 'mis_report_%s_%s' % (old_id, suffix)
                new_record.set('id', new_report_id)
                new_record.set('model', 'mis.report')
                new_field = xml.SubElement(new_record, "field")
                new_field.set('name', 'name')
                new_field.text = template_name
                new_field = xml.SubElement(new_record, "field")
                new_field.set('name', 'style_id')
                new_field.set('ref', 'mis_report_style_l10n_es_base')
            if 'model' in child.attrib.keys() and child.attrib['model'] == \
                    'account.balance.reporting.template.line':
                old_id = child.attrib['id']
                new_id = 'mis_report_kpi_%s_%s' % (old_id, suffix)
                new_record.set('id', new_id)
                new_record.set('model', 'mis.report.kpi')
                new_field = xml.SubElement(new_record, "field")
                new_field.set('name', 'report_id')
                new_field.set('ref', new_report_id)
                new_field = xml.SubElement(new_record, "field")
                new_field.set('name', 'type')
                new_field.text = 'num'
                new_field = xml.SubElement(new_record, "field")
                new_field.set('name', 'compare_method')
                new_field.text = 'pct'
                new_field = xml.SubElement(new_record, "field")
                new_field.set('name', 'sequence')
                new_field.text = str(sequence)
                sequence += 10
            for step_child in child:
                if step_child.tag == "field":
                    if ('model' in child.attrib.keys() and
                        child.attrib['model'] ==
                            'account.balance.reporting.template'):
                        continue
                    if ('name' in step_child.attrib.keys() and
                            step_child.attrib['name'] == 'code'):
                        new_field = xml.SubElement(new_record, "field")
                        new_code = 'es%s' % step_child.text
                        new_field.set('name', 'name')
                        new_field.text = new_code
                    elif ('name' in step_child.attrib.keys() and
                            step_child.attrib['name'] == 'name'):
                        new_field = xml.SubElement(new_record, "field")
                        new_field.set('name', 'description')
                        new_field.text = step_child.text
                    elif ('name' in step_child.attrib.keys() and
                            step_child.attrib['name'] == 'current_value'):

                        if balance_model == 'debit-credit':
                            operator = '+'
                        else:
                            operator = '-'
                        # Try to find the parent and figure out if it is a
                        # negate
                        path = './/record[@id="%s"]/field[@name="negate"]' % \
                            child.attrib['id']
                        record_code = root.find(path)
                        if record_code is not None:
                            operator = '+'

                        expr = ''
                        if step_child.text:
                            expr = step_child.text.replace("*", "")
                        sep = ';'
                        expr = expr.split(sep, 1)[0]
                        totalization = False
                        if '+' in expr:
                            totalization = True
                        codes = re.split(r'[,+]+', expr)
                        new_expr = ''
                        for code in codes:
                            code.lstrip()
                            if not code:
                                codes.remove(code)
                        if codes:
                            new_field = xml.SubElement(new_record, "field")
                            new_field.set('name', 'expression')
                            if totalization:
                                for code in codes:
                                    code.rstrip()
                                    if totalization:
                                        new_expr += '+es%s' % code.lstrip()
                                new_field.text = new_expr.replace(" ", "")
                            else:
                                debit_codes = []
                                credit_codes = []
                                normal_codes = []
                                for code in codes:
                                    bad_chars = '()'
                                    rgx = re.compile('[%s]' % bad_chars)
                                    if 'debit' in code:
                                        code = code.replace('debit', '')
                                        code = rgx.sub('', code)
                                        debit_codes.append(code)
                                    elif 'credit' in code:
                                        code = code.replace('credit', '')
                                        code = rgx.sub('', code)
                                        credit_codes.append(code)
                                    else:
                                        normal_codes.append(code)
                                if normal_codes:
                                    codes = map(lambda x: x + '%',
                                                normal_codes)
                                    codes_string = ','.join(map(str, codes))
                                    new_expr = '%s%s[%s] ' \
                                               % (operator,
                                                   prefix,
                                                   codes_string.lstrip())
                                    new_field.text = new_expr.replace(" ", "")
                                if debit_codes:
                                    codes = map(lambda x: x + '%',
                                                debit_codes)
                                    codes_string = ','.join(map(str, codes))
                                    new_expr = '%s%s[%s] ' \
                                               % (operator,
                                                   prefix,
                                                   codes_string.lstrip())
                                    new_expr = new_expr.replace(" ", "")
                                    new_field.text += '%s%s' % (
                                        new_expr, debit_move_domain)
                                if credit_codes:
                                    codes = map(lambda x: x + '%',
                                                credit_codes)
                                    codes_string = ','.join(map(str, codes))
                                    new_expr = '%s%s[%s] ' \
                                                % (operator,
                                                   prefix,
                                                   codes_string.lstrip())
                                    new_expr = new_expr.replace(" ", "")
                                    new_field.text += '%s%s' % (
                                        new_expr, credit_move_domain)
                        else:
                            path = \
                                './/record[@id="%s"]/field[@name="code"]' % \
                                child.attrib['id']
                            record_code = root.find(path)
                            if record_code is not None:
                                new_field = xml.SubElement(new_record, "field")
                                new_field.set('name', 'expression')
                                new_expr += '%s%s[%s%%] ' % \
                                            (operator, prefix,
                                             record_code.text.lstrip())
                                new_expr.lstrip()
                                new_field.text = new_expr.replace(" ", "")
                        if auto_expand_accounts:
                            new_field = xml.SubElement(new_record, "field")
                            new_field.set('name', 'auto_expand_accounts')
                            new_field.text = 'True'
                            elem_css_class = child.find(
                                './/field[@name="css_class"]')
                            new_field = xml.SubElement(new_record, "field")
                            new_field.set('name',
                                          'auto_expand_accounts_style_id')
                            new_field.set(
                                'ref',
                                'mis_report_style_l10n_es_%si' %
                                elem_css_class.text)

                    elif ('name' in step_child.attrib.keys() and
                            step_child.attrib['name'] == 'parent_id'):
                        # Try to find the parent and add to it this reference
                        new_id = 'mis_report_kpi_%s_%s' % (step_child.attrib[
                            'ref'], suffix)
                        path = './/record[@id="%s"]' % new_id
                        elem = new_root.find(path)
                        elem_expression = elem.find(
                            './/field[@name="expression"]')
                        name = child.find('.//field[@name="code"]')
                        if elem_expression is not None:
                            new_code = ' +es%s ' % name.text
                            elem_expression.text += new_code.rstrip()
                        else:
                            path = './/record[@id="%s"]' % new_id
                            elem = new_root.find(path)
                            if elem is None:
                                continue
                            new_field = xml.SubElement(elem, "field")
                            new_field.set('name', 'expression')
                            new_field.text = ' +es%s' % name.text
                    elif ('name' in step_child.attrib.keys() and
                            step_child.attrib['name'] == 'css_class'):
                        new_field = xml.SubElement(new_record, "field")
                        new_field.set('name', 'style_id')
                        new_style_ref = 'mis_report_style_l10n_es_%s' % \
                                        step_child.text
                        new_field.set('ref', new_style_ref)
    for child in new_root:
        elems = child.findall(
            './/field[@name="expression"]')
        for elem in elems:
            if '-bale[129%,6%,7%]' in elem.text:
                elem.text += """-balu[6%,7%]"""

    xmlstr = minidom.parseString(ET.tostring(new_root)).toprettyxml(
        indent="   ", encoding='utf-8')

    with open(new_xml_file, "w") as fh:
        fh.write(xmlstr)


if __name__ == "__main__":

    template = u'Balance completo (PGCE 2008)'
    print 'Processing %s' % template
    parseXML(
        old_xml_file=
        "../l10n_es_account_balance_report/data/balance_normal.xml",
        new_xml_file='data/mis_report_balance_normal_summary.xml',
        template_name=template,
        suffix='summary', auto_expand_accounts=False)

    template = u'Balance completo (PGCE 2008) - Expandido'
    print 'Processing %s' % template
    parseXML(
        old_xml_file=
        "../l10n_es_account_balance_report/data/balance_normal.xml",
        new_xml_file='data/mis_report_balance_normal_expanded.xml',
        template_name=template,
        suffix='expanded', auto_expand_accounts=True)

    template = u'Balance abreviado (PGCE 2008)'
    print 'Processing %s' % template
    parseXML(
        old_xml_file=
        "../l10n_es_account_balance_report/data/balance_abreviado.xml",
        new_xml_file='data/mis_report_balance_abreviated_summary.xml',
        template_name=template,
        suffix='summary', auto_expand_accounts=False)

    template = u'Balance abreviado (PGCE 2008) - Expandido'
    print 'Processing %s' % template
    parseXML(
        old_xml_file=
        "../l10n_es_account_balance_report/data/balance_abreviado.xml",
        new_xml_file='data/mis_report_balance_abreviated_expanded.xml',
        template_name=template,
        suffix='expanded', auto_expand_accounts=True)

    template = u'Balance PYMEs (PGCE 2008)'
    print 'Processing %s' % template
    parseXML(
        old_xml_file=
        "../l10n_es_account_balance_report/data/balance_pymes.xml",
        new_xml_file='data/mis_report_balance_sme_summary.xml',
        template_name=template,
        suffix='summary', auto_expand_accounts=False)

    template = u'Balance PYMEs (PGCE 2008) - Expandido'
    print 'Processing %s' % template
    parseXML(
        old_xml_file=
        "../l10n_es_account_balance_report/data/balance_pymes.xml",
        new_xml_file='data/mis_report_balance_sme_expanded.xml',
        template_name=template,
        suffix='expanded', auto_expand_accounts=True)

    template = u'Pérdidas y ganancias completo (PGCE 2008)'
    print 'Processing %s' % template
    parseXML(
        old_xml_file=
        "../l10n_es_account_balance_report/data/pyg_normal.xml",
        new_xml_file='data/mis_report_pyg_normal_summary.xml',
        template_name=template,
        suffix='summary', auto_expand_accounts=False)

    template = u'Pérdidas y ganancias completo (PGCE 2008) - Expandido'
    print 'Processing %s' % template
    parseXML(
        old_xml_file=
        "../l10n_es_account_balance_report/data/pyg_normal.xml",
        new_xml_file='data/mis_report_pyg_normal_expanded.xml',
        template_name=template,
        suffix='expanded', auto_expand_accounts=True)

    template = u'Pérdidas y ganancias abreviado (PGCE 2008)'
    print 'Processing %s' % template
    parseXML(
        old_xml_file=
        "../l10n_es_account_balance_report/data/pyg_abreviado.xml",
        new_xml_file='data/mis_report_pyg_abreviated_summary.xml',
        template_name=template,
        suffix='summary', auto_expand_accounts=False)

    template = u'Pérdidas y ganancias abreviado (PGCE 2008) - Expandido'
    print 'Processing %s' % template
    parseXML(
        old_xml_file=
        "../l10n_es_account_balance_report/data/pyg_abreviado.xml",
        new_xml_file='data/mis_report_pyg_abreviated_expanded.xml',
        template_name=template,
        suffix='expanded', auto_expand_accounts=True)

    template = u'Pérdidas y ganancias PYMEs (PGCE 2008)'
    print 'Processing %s' % template
    parseXML(
        old_xml_file=
        "../l10n_es_account_balance_report/data/pyg_pymes.xml",
        new_xml_file='data/mis_report_pyg_sme_summary.xml',
        template_name=template,
        suffix='summary', auto_expand_accounts=False)

    template = u'Pérdidas y ganancias PYMEs (PGCE 2008) - Expandido'
    print 'Processing %s' % template
    parseXML(
        old_xml_file=
        "../l10n_es_account_balance_report/data/pyg_pymes.xml",
        new_xml_file='data/mis_report_pyg_sme_expanded.xml',
        template_name=template,
        suffix='expanded', auto_expand_accounts=True)

    template = u'Estado de ingresos y gastos reconocidos (PGCE 2008)'
    print 'Processing %s' % template
    parseXML(
        old_xml_file=
        "../l10n_es_account_balance_report/data/estado_ingresos_gastos_normal"
        ".xml",
        new_xml_file='data/mis_report_revenues_expenses_normal_summary.xml',
        template_name=template,
        suffix='summary', auto_expand_accounts=False)

    template = \
        u'Estado de ingresos y gastos reconocidos (PGCE 2008) - Expandido'
    print 'Processing %s' % template
    parseXML(
        old_xml_file=
        "../l10n_es_account_balance_report/data/"
        "estado_ingresos_gastos_normal.xml",
        new_xml_file='data/mis_report_revenues_expenses_normal_expanded.xml',
        template_name=template,
        suffix='expanded', auto_expand_accounts=True)

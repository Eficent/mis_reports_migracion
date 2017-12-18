# -*- coding: utf-8 -*-
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
#                <contact@eficent.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl
# pylint: disable=skip-file
# pylint: disable-all
import urllib2
from lxml import etree
import lxml.etree as ET


def create_kpi_expressions(expr, name, description, consolidated_root,
                           new_data, parent, template_name, suffix, field,
                           new_record_id):

        # Create sub-KPI expressions
        subkpi_expression_record = etree.SubElement(new_data, "record")
        subkpi_expression_record_id = \
            '%s_subkpi_expression_%s_%s_%s' % (
                template_name, expr, parent.attrib['id'], suffix)
        subkpi_expression_record.set('id', subkpi_expression_record_id)
        subkpi_expression_record.set('model',
                                     'mis.report.kpi.expression')
        new_field = etree.SubElement(subkpi_expression_record, "field")
        new_field.set('name', 'name')
        new_field.text = '%s[%s%%]' % (expr, field.text)
        new_field = etree.SubElement(subkpi_expression_record, "field")
        new_field.set('name', 'kpi_id')
        new_field.set('ref', new_record_id)
        new_field = etree.SubElement(subkpi_expression_record, "field")
        new_field.set('name', 'subkpi_id')
        ref_id = '%s_%s_subkpi_%s' % (template_name, suffix, expr)
        new_field.set('ref', ref_id)


def create_records_by_ref(consolidated_root, kpi_data, subkpi_data,
                          ref_id, template_name, suffix, current_ref,
                          auto_expand_accounts):
    path = './/field[@ref="%s"]' % current_ref
    for elem in consolidated_root.findall(path):
        is_leaf = False
        parent = elem.getparent()
        # If it is not a view, get rid of it.
        path = './/field[@name="type"]'
        type = parent.find(path)
        if type is not None and type.text != 'view':
            continue
        # Check if it has children
        path = './/field[@ref="%s"]' % parent.attrib['id']
        child = consolidated_root.find(path)
        if child is not None:
            parent_2 = child.getparent()
            path = './/field[@name="type"]'
            type = parent_2.find(path)
            if type is not None and type.text != 'view':
                is_leaf = True
        new_record = etree.SubElement(kpi_data, "record")
        new_record_id = '%s_kpi_%s_%s' % (template_name, parent.attrib['id'],
                                          suffix)
        new_record.set('id', new_record_id)
        new_record.set('model', 'mis.report.kpi')

        for field in parent:
            if 'name' in field.attrib and field.attrib['name'] == 'code':
                new_field = etree.SubElement(new_record, "field")
                new_field.set('name', 'name')
                new_field.text = 'es%s' % field.text
                if is_leaf:
                    new_field = etree.SubElement(new_record, "field")
                    new_field.set('name', 'multi')
                    new_field.text = 'True'
                    if auto_expand_accounts:
                        new_field = etree.SubElement(new_record, "field")
                        new_field.set('name', 'auto_expand_accounts')
                        new_field.text = 'True'
                        new_field = etree.SubElement(new_record, "field")
                        new_field.set('name',
                                      'auto_expand_accounts_style_id')
                        new_field.set(
                            'ref',
                            'mis_report_style_l10n_es_l%si' % len(field.text))
                else:
                    new_field = etree.SubElement(new_record, "field")
                    new_field.set('name', 'expression')
                    new_field.text = ''
                    # Find immediate children in hierarchy
                    path = './/field[@ref="%s"]' % parent.attrib['id']
                    for child in consolidated_root.findall(path):
                        parent_2 = child.getparent()
                        path = './/field[@name="code"]'
                        code_elem = parent_2.find(path)
                        if code_elem is not None and code_elem.text.lstrip():
                            if code_elem.text != field.text:
                                new_code = ' +es%s ' % code_elem.text
                                new_field.text += new_code.rstrip()

                new_field = etree.SubElement(new_record, "field")
                new_field.set('name', 'style_id')
                new_style_ref = 'mis_report_style_l10n_es_l%s' % \
                    len(field.text)
                new_field.set('ref', new_style_ref)
                new_field = etree.SubElement(new_record, "field")
                new_field.set('name', 'report_id')
                new_field.set('ref', ref_id)
                new_field = etree.SubElement(new_record, "field")
                new_field.set('name', 'type')
                new_field.text = 'num'
                new_field = etree.SubElement(new_record, "field")
                new_field.set('name', 'compare_method')
                new_field.text = 'pct'

                if is_leaf:
                    # Create sub-KPI's
                    expr = 'bali'
                    create_kpi_expressions(
                        expr, 'saldo_inicial', u'Saldo Inicial',
                        consolidated_root, subkpi_data, parent,
                        template_name, suffix,
                        field, new_record_id)
                    expr = 'debp'
                    create_kpi_expressions(
                        expr, 'movimientos_debe', u'Movimientos (Debe)',
                        consolidated_root, subkpi_data, parent,
                        template_name, suffix, field, new_record_id)
                    expr = 'crdp'
                    create_kpi_expressions(
                        expr, 'movimientos_haber', u'Movimientos (Haber)',
                        consolidated_root, subkpi_data, parent,
                        template_name, suffix, field, new_record_id)
                    expr = 'bale'
                    create_kpi_expressions(
                        expr, 'saldo_final', u'Saldo Final',
                        consolidated_root, subkpi_data, parent,
                        template_name, suffix, field, new_record_id)
                    expr = 'balp'
                    create_kpi_expressions(
                        expr, 'variacion', u'Variación',
                        consolidated_root, subkpi_data, parent,
                        template_name, suffix, field, new_record_id)

            elif 'name' in field.attrib and field.attrib['name'] == 'name':
                parent = field.getparent()
                path = './/field[@name="code"]'
                code_elem = parent.find(path)
                description = False
                if code_elem is not None and code_elem.text:
                    description = code_elem.text
                new_field = etree.SubElement(new_record, "field")
                new_field.set('name', 'description')
                if description:
                    description += ' - %s' % field.text
                else:
                    description = field.text
                new_field.text = description

        new_ref_elem = parent.find('.//field[@name="parent_id"]')
        if new_ref_elem is not None:
            create_records_by_ref(consolidated_root, kpi_data, subkpi_data,
                                  ref_id, template_name, suffix,
                                  parent.attrib['id'], auto_expand_accounts)


def create_subkpi_records(elem, expr_code, expr_name, template_name, suffix,
                          ref_id):
    new_ref_id = '%s_subkpi_%s' % (ref_id, expr_code)
    new_record = etree.Element("record")
    new_record.set('id', new_ref_id)
    new_record.set('model', 'mis.report.subkpi')
    new_field = etree.SubElement(new_record, "field")
    new_field.set('name', 'name')
    new_field.text = expr_code
    new_field = etree.SubElement(new_record, "field")
    new_field.set('name', 'description')
    new_field.text = expr_name
    new_field = etree.SubElement(new_record, "field")
    new_field.set('name', 'report_id')
    new_field.set('ref', ref_id)
    elem.append(new_record)


def parseXML(xml_path=None, kpi_xml_file=None, subkpi_xml_file=None,
             template_name=None, template_description=None,
             suffix=None, auto_expand_accounts=False):

    # Fetch common chart of account elements from 8.0 branch, where there was
    #  still the full CoA hierarchy.
    common_xmlpath = \
        'https://raw.githubusercontent.com/OCA/l10n-spain/' \
        '8.0/l10n_es/data/account_account_common.xml'

    common_tree = ET.parse(urllib2.urlopen(common_xmlpath))
    coa_tree = ET.parse(urllib2.urlopen(xml_path))

    common_root = common_tree.getroot()

    coa_root = coa_tree.getroot()

    consolidated_root = etree.Element("odoo")

    for datas in coa_root:
        for record in datas:
            if record.tag == "record":
                consolidated_root.append(record)

    for datas in common_root:
        for record in datas:
            if record.tag == "record":
                consolidated_root.append(record)

    mis_report_kpi_root = etree.Element("odoo")
    mis_report_kpi_data = etree.Element("data")
    mis_report_kpi_root.append(mis_report_kpi_data)

    mis_report_subkpi_root = etree.Element("odoo")
    mis_report_subkpi_data = etree.Element("data")
    mis_report_subkpi_root.append(mis_report_subkpi_data)
    ref_id = '%s_%s' % (template_name, suffix)

    for expr in [['bali', u'Saldo Inicial'], ['debp', u'Movimientos (Debe)'],
                 ['crdp', u'Movimientos (Haber)'], ['bale', u'Saldo Final'],
                 ['balp', u'Variación']]:
        create_subkpi_records(mis_report_subkpi_data, expr[0], expr[1],
                              template_name,
                              suffix, ref_id)

    current_ref = 'pgc_0'
    new_record = etree.Element("record")
    new_record.set('id', ref_id)
    new_record.set('model', 'mis.report')
    new_field = etree.Element("field")
    new_field.set('name', 'name')
    new_field.text = template_description
    new_record.append(new_field)
    new_field = etree.Element("field")
    new_field.set('name', 'style_id')
    new_field.set('ref', 'mis_report_style_l10n_es_base')
    mis_report_kpi_data.append(new_record)
    create_records_by_ref(consolidated_root, mis_report_kpi_data,
                          mis_report_subkpi_data, ref_id, template_name,
                          suffix, current_ref, auto_expand_accounts)

    data = []
    for record in mis_report_kpi_data:
        path = './/field[@name="name"]'
        code_elem = record.find(path)
        if code_elem is None:
            key = '00000'
        else:
            try:
                key = str(int(code_elem.text.replace('es', '')))
                key = key.ljust(6, '0')
            except ValueError:
                key = '00000'
        key = ".".join(key)

        data.append((key, record))

    data = sorted(data, key=lambda x: [int(i) for i in
                                       x[0].rstrip(".").split(".")])
    # insert the last item from each tuple
    sequence = 0
    for item in data:
        if item[-1].tag == 'record':
            if item[-1].attrib['model'] == 'mis.report':
                continue
            sequence += 10
            new_field = etree.SubElement(item[-1], "field")
            new_field.set('name', 'sequence')
            new_field.text = '%s' % sequence

    mis_report_kpi_data[:] = [item[-1] for item in data]

    xmlstr = etree.tostring(mis_report_kpi_root, pretty_print=True,
                            encoding='utf-8', xml_declaration=True)

    with open(kpi_xml_file, "w") as fh:
        fh.write(xmlstr)

    xmlstr = etree.tostring(mis_report_subkpi_root, pretty_print=True,
                            encoding='utf-8', xml_declaration=True)
    with open(subkpi_xml_file, "w") as fh:
        fh.write(xmlstr)


if __name__ == "__main__":

    # Balance Normal
    template = u'Balance de Sumas y Saldos normal (PGCE 2008)'
    print 'Processing %s' % template
    parseXML(xml_path='https://raw.githubusercontent.com/OCA/l10n-spain/'
                      '8.0/l10n_es/data/account_account_full.xml',
             kpi_xml_file=
             'data/mis_report_trial_balance_full_summary.xml',
             subkpi_xml_file=
             'data/mis_report_trial_balance_full_summary_subkpi.xml',
             suffix='summary',
             template_name='mis_report_trial_balance_full',
             template_description=template,
             auto_expand_accounts=False)

    template = u'Balance de Sumas y Saldos normal (PGCE 2008) - Expandido'
    print 'Processing %s' % template
    parseXML(xml_path='https://raw.githubusercontent.com/OCA/l10n-spain/'
                      '8.0/l10n_es/data/account_account_full.xml',
             kpi_xml_file=
             'data/mis_report_trial_balance_full_expanded.xml',
             subkpi_xml_file=
             'data/mis_report_trial_balance_full_expanded_subkpi.xml',
             suffix='expanded',
             template_name='mis_report_trial_balance_full',
             template_description=template,
             auto_expand_accounts=True)

    # Balance PYMES
    template = u'Balance de Sumas y Saldos PYMEs (PGCE 2008)'
    print 'Processing %s' % template
    parseXML(xml_path='https://raw.githubusercontent.com/OCA/l10n-spain/'
                      '8.0/l10n_es/data/account_account_pymes.xml',
             kpi_xml_file=
             'data/mis_report_trial_balance_pymes_summary.xml',
             subkpi_xml_file=
             'data/mis_report_trial_balance_pymes_summary_subkpi.xml',
             suffix='summary',
             template_name='mis_report_trial_balance_pymes',
             template_description=template,
             auto_expand_accounts=False)

    template = u'Balance de Sumas y Saldos PYMEs (PGCE 2008) - Expandido'
    print 'Processing %s' % template
    parseXML(xml_path='https://raw.githubusercontent.com/OCA/l10n-spain/'
                      '8.0/l10n_es/data/account_account_pymes.xml',
             kpi_xml_file=
             'data/mis_report_trial_balance_pymes_expanded.xml',
             subkpi_xml_file=
             'data/mis_report_trial_balance_pymes_expanded_subkpi.xml',
             suffix='expanded',
             template_name='mis_report_trial_balance_pymes',
             template_description=template,
             auto_expand_accounts=True)

    # Balance Asociaciones
    template = u'Balance de Sumas y Saldos asociaciones (PGCE 2008)'
    print 'Processing %s' % template
    parseXML(xml_path='https://raw.githubusercontent.com/OCA/l10n-spain/'
                      '8.0/l10n_es/data/account_account_assoc.xml',
             kpi_xml_file=
             'data/mis_report_trial_balance_asoc_summary.xml',
             subkpi_xml_file=
             'data/mis_report_trial_balance_asoc_summary_subkpi.xml',
             suffix='summary',
             template_name='mis_report_trial_balance_asoc',
             template_description=template,
             auto_expand_accounts=False)

    template = \
        u'Balance de Sumas y Saldos asociaciones (PGCE 2008) - Expandido'
    print 'Processing %s' % template
    parseXML(xml_path='https://raw.githubusercontent.com/OCA/l10n-spain/'
                      '8.0/l10n_es/data/account_account_assoc.xml',
             kpi_xml_file=
             'data/mis_report_trial_balance_asoc_expanded.xml',
             subkpi_xml_file=
             'data/mis_report_trial_balance_asoc_expanded_subkpi.xml',
             suffix='expanded',
             template_name='mis_report_trial_balance_asoc',
             template_description=template,
             auto_expand_accounts=True)

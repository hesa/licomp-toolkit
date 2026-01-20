# SPDX-FileCopyrightText: 2025 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

import json
import yaml

class LicompToolkitFormatter():

    @staticmethod
    def formatter(fmt):
        if fmt.lower() == 'json':
            return JsonLicompToolkitFormatter()
        if fmt.lower() == 'text':
            return TextLicompToolkitFormatter()
        if fmt.lower() == 'yaml' or fmt.lower() == 'yml':
            return YamlLicompToolkitFormatter()
        if fmt.lower() == 'dot':
            return DotLicompToolkitFormatter()

    def format_compatibilities(self, compat):
        raise Exception(f'{self.__class__.__name__} cannot format compatibilities.')

    def _pre_format_display_compatibilities(self, compats):
        licenses = list(compats.keys())
        finished = {}
        for outbound in licenses:
            finished[outbound] = {}
            for inbound in licenses:
                finished[outbound][inbound] = False

        for outbound in licenses:
            for inbound in licenses:
                if finished[outbound][inbound] and finished[inbound][outbound]:
                    continue
                if outbound == inbound:
                    finished[outbound][inbound] = ['yes']
                    finished[inbound][outbound] = ['yes']
                else:
                    outbound_compat = compats[outbound][inbound]['summary']['compatibility_statuses']
                    inbound_compat = compats[inbound][outbound]['summary']['compatibility_statuses']
                    finished[outbound][inbound] = list(outbound_compat.keys())
                    finished[inbound][outbound] = list(inbound_compat.keys())

        return finished

    def format_licomp_resources(self, licomp_resources):
        raise Exception(f'{self.__class__.__name__} cannot format licomp resources.')

    def format_licomp_licenses(self, licomp_licenses):
        raise Exception(f'{self.__class__.__name__} cannot format licomp licenses.')

    def format_licomp_versions(self, licomp_versions):
        raise Exception(f'{self.__class__.__name__} cannot format licomp versions.')

class JsonLicompToolkitFormatter(LicompToolkitFormatter):

    def format_compatibilities(self, compat):
        return json.dumps(compat, indent=4)

    def format_licomp_resources(self, licomp_resources):
        return json.dumps(licomp_resources, indent=4)

    def format_licomp_licenses(self, licomp_licenses):
        return json.dumps(licomp_licenses, indent=4)

    def format_licomp_versions(self, licomp_versions):
        return json.dumps(licomp_versions, indent=4)

    def format_display_compatibilities(self, compats, settings={}):
        # settings
        #  discard_unsupported: True - will remove unsupported licenses from the output
        display_compats = self._pre_format_display_compatibilities(compats)
        return json.dumps(display_compats, indent=4)

    def format_policy_report(self, report):
        return json.dumps(report, indent=4)
        
class YamlLicompToolkitFormatter(LicompToolkitFormatter):

    def format_compatibilities(self, compat):
        return yaml.safe_dump(compat, indent=4)

    def format_licomp_resources(self, licomp_resources):
        return yaml.safe_dump(licomp_resources, indent=4)

    def format_licomp_licenses(self, licomp_licenses):
        return yaml.safe_dump(licomp_licenses, indent=4)

    def format_licomp_versions(self, licomp_versions):
        return yaml.safe_dump(licomp_versions, indent=4)

    def format_display_compatibilities(self, compats, settings={}):
        display_compats = self._pre_format_display_compatibilities(compats)
        return yaml.safe_dump(display_compats, indent=4)

class TextLicompToolkitFormatter(LicompToolkitFormatter):

    def _format_licomp_resource(self, licomp_resource):
        name = licomp_resource['name']
        version = licomp_resource['version']
        usecases = ','.join(licomp_resource['usecases'])
        provisionings = ','.join(licomp_resource['provisionings'])
        resource_type = licomp_resource['type']
        return f'{name}:{version}:{usecases}:{provisionings}:{resource_type}'

    def format_licomp_resources(self, licomp_resources):
        return '\n'.join([self._format_licomp_resource(x) for x in licomp_resources])

    def format_licomp_licenses(self, licomp_licenses):
        return '\n'.join(licomp_licenses)

    def __get_responses(self, results, indent=''):
        output = []
        for res in ['yes', 'no', 'schneben']:
            result = results.get(res)
            if not result:
                count = 0
            else:
                count = result['count']
            output.append(f'{indent}{res}: {count}')

        return output

    def __compatibility_statuses(self, statuses, indent=''):
        output = []
        for status, values in statuses.items():
            resources = []
            for value_object in values:
                resources.append(value_object['resource_name'])
            output.append(f'{indent}{status}: {", ".join(resources)}')

        return output

    def __statuses(self, statuses, indent=''):
        output = []
        for status, values in statuses.items():
            resources = []
            for value_object in values:
                resources.append(value_object['resource_name'])
            output.append(f'{indent}{status}: {", ".join(resources)}')

        return output

    def _format_compat_pref(self, compat, pref_lic=None):
        PAREN_OPEN = '('
        PAREN_CLOSE = ')'
        if compat == 'yes':
            compat_string = 'compatible'
        else:
            compat_string = 'incompatible'

        if pref_lic:
            return f'{PAREN_OPEN}{compat_string}, {pref_lic}{PAREN_CLOSE}'
        else:
            return f'{PAREN_OPEN}{compat_string}{PAREN_CLOSE}'

    def format_compatibilities_general(self, compat_object, indent='', policy_report=False, preferred_license=False, least_preferred_license=False):
        compatibility_check = compat_object["compatibility_check"]
        output = []

        if compatibility_check == "outbound-license -> inbound-license":
            compat_object = compat_object
            details = compat_object["compatibility_details"]
            summary = details["summary"]
            preferred_info = 'no'
            least_preferred_info = 'no'
            if policy_report and preferred_license:
                preferred_info = 'yes'
            if policy_report and least_preferred_license:
                least_preferred_info = 'yes'
            output.append(f'{indent}{compat_object["outbound_license"]} -> {compat_object["inbound_license"]} {self._format_compat_pref(compat_object["compatibility"])}')
            if policy_report:
                output.append(f'{indent}  preferred license:       {preferred_info}')
                output.append(f'{indent}  least preferred license: {least_preferred_info}')
            output.append(f'{indent}  compatibility:           {compat_object["compatibility"]}')
            output.append(f'{indent}  compatibility details:   ')
            output += self.__compatibility_statuses(summary['compatibility_statuses'], f'{indent}    ')

        if compatibility_check == "outbound-license -> inbound-expression":
            operator = compat_object["operator"]
            inner_output = []
            if policy_report:
                if len(compat_object['policy_check']['inbound_licenses']) > 0:
                    preferred_license = compat_object['policy_check']['inbound_licenses'][0]['inbound_license']
                    least_preferred_license = compat_object['policy_check']['inbound_licenses'][-1]['inbound_license']
            for operand in compat_object["operands"]:
                preferred = False
                least_preferred = False
                if policy_report:
                    operand_license = operand['compatibility_object']['inbound_license']
                    if operand_license == preferred_license:
                        preferred = True
                    if operand_license == least_preferred_license:
                        least_preferred = True
                res = self.format_compatibilities_general(operand['compatibility_object'], indent=f'{indent}  ', policy_report=policy_report, preferred_license=preferred, least_preferred_license=least_preferred)
                #inner_output.append(f'{indent}  allowed licenses:        {", ".join([x["inbound_license"] for x in compat_object["policy_check"]["inbound_licenses"]])}')
                inner_output.append(res)
            if policy_report:
                if len(compat_object['policy_check']['inbound_list']) > 0:
                    if operator == 'OR':
                        pref_lic = compat_object['policy_check']['inbound_licenses'][0]['inbound_license']
                    elif operator == 'AND':
                        pref_lic = ' AND '.join([x['inbound_license'] for x in compat_object['policy_check']['inbound_licenses']])
                else:
                    pref_lic = ''
                output.append(f'{indent}{operator} {self._format_compat_pref(compat_object["compatibility"], pref_lic)}')
                output += inner_output
        if compatibility_check == "outbound-expression -> inbound-license":
            operator = compat_object["operator"]
            output.append(f'{indent}{operator} {self._format_compat_pref(compat_object["compatibility"])}')
            for operand in compat_object["operands"]:
                res = self.format_compatibilities_general(operand['compatibility_object'], indent=f'{indent}  ', policy_report=policy_report)
                output.append(res)
        if compatibility_check == "outbound-expression -> inbound-expression":
            operator = compat_object["operator"]
            compat = compat_object["compatibility"]
            output.append(f'{indent}{operator} {self._format_compat_pref(compat)}')
            for operand in compat_object['operands']:
                res = self.format_compatibilities_general(operand['compatibility_object'], indent=f'{indent}  ', policy_report=policy_report)
                output.append(f'{res}')

        return "\n".join(output)

    def format_compatibilities_object(self, compat_object):
        return self.format_compatibilities_general(compat_object, indent='')

    def format_policy_report(self, report):
        output = []
        preferred_inbound = ''
        print("keys: " + str(report["compatibility_report"].keys()))
        if report["compatibility_report"]["policy_check"]['inbound_license_type'] == 'license':
            preferred_inbound = report["compatibility_report"]["policy_check"]["inbound_license"]
        elif report["compatibility_report"]["policy_check"]['inbound_license_type'] == 'license-expression':
            if len(report["compatibility_report"]["policy_check"]["inbound_licenses"]) > 0:
                preferred_inbound = report["compatibility_report"]["policy_check"]["inbound_licenses"][0]['inbound_license']
                
        output.append(f'outbound:          {report["outbound"]}')
        output.append(f'inbound:           {report["inbound"]}')
        output.append(f'resources:         {", ".join(report["resources"])}')
        output.append(f'provisioning:      {report["provisioning"]}')
        output.append(f'usecase:           {report["usecase"]}')
        output.append(f'compatibility:     {report["compatibility"]}')
        output.append(f'preferred inbound: {preferred_inbound}')
        if report["meta"]["policy_type"] == 'default':
            policy_string = 'default'
        else:
            policy_string = report["meta"]["policy_file"]
        output.append(f'policy:            {policy_string}')
        output.append('report:')
        output.append(self.format_compatibilities_general(report["compatibility_report"], indent='  ', policy_report=True))
        return "\n".join(output)
        
    def format_compatibilities(self, compat):
        output = []
        output.append(f'outbound:      {compat["outbound"]}')
        output.append(f'inbound:       {compat["inbound"]}')
        output.append(f'resources:     {", ".join(compat["resources"])}')
        output.append(f'provisioning:  {compat["provisioning"]}')
        output.append(f'usecase:       {compat["usecase"]}')
        output.append(f'compatibility: {compat["compatibility"]}')
        output.append('report:')
        output.append(self.format_compatibilities_general(compat["compatibility_report"], '  ', policy_report=False))

        return "\n".join(output)

    def format_licomp_versions(self, licomp_versions):
        lt = 'licomp-toolkit'
        res = [f'{lt}: {licomp_versions[lt]}']
        for k, v in licomp_versions['licomp-resources'].items():
            res.append(f'{k}: {v}')
        return '\n'.join(res)

    def format_display_compatibilities(self, compats):
        # possible compats are:
        # no (red)
        # yes (green)
        # depends (yellow)
        # unsupported (yellow)
        # unknown (yellow)
        # mixed (yellow)
        display_compats = self._pre_format_display_compatibilities(compats)
        licenses = list(display_compats.keys())

        lines = []
        for outbound in licenses:
            for inbound in licenses:
                lines.append(f'{outbound:30s} {"---->":10s} {inbound:30s}: {", ".join(display_compats[outbound][inbound])}')
        return '\n'.join(lines)

class DotLicompToolkitFormatter(LicompToolkitFormatter):

    def _compat_line_color(self, compats):
        _line_map = {
            'unknown': 'style="dotted"',
            'depends': 'style="dotted"',
            'unsupported': 'style="dotted"',
            'mixed': 'style="dotted"',
        }
        _color_map = {
            'yes': 'darkgreen',
            'no': 'darkred'
        }
        same = True
        value = None
        for compat in compats:
            if compat == 'unsupported':
                continue
            if not value:
                value = compat
            else:
                if compat != value:
                    same = False

        if same:
            line = _line_map.get(value, '')
            color = _color_map.get(value, 'yellow')
        else:
            line = _line_map['mixed']
            color = 'darkblue'

        return line, color

    def _license_license_compat(self, outbound, inbound, outbound_compat, inbound_compat):
        out_line, out_color = self._compat_line_color(outbound_compat)
        in_line, in_color = self._compat_line_color(inbound_compat)
        if out_line == in_line and out_color == in_color:
            return (f'    "{outbound}" -> "{inbound}" [dir="both" color="{out_color}" {out_line}]')
        else:
            return '\n'.join([f'    "{outbound}" -> "{inbound}" [color="{out_color}" {out_line}]',
                              f'    "{inbound}" -> "{outbound}" [color="{in_color}" {in_line}]'])

    def format_display_compatibilities(self, compats, settings={}):
        # possible compats are:
        # no (red)
        # yes (green)
        # depends (yellow)
        # unsupported (yellow)
        # unknown (yellow)
        # mixed (yellow)
        display_compats = self._pre_format_display_compatibilities(compats)
        licenses = list(display_compats.keys())

        discard_unsupported = settings.get('discard_unsupported')

        lines = []
        finished = {}
        usecase = compats[licenses[0]][licenses[0]]['compatibilities'][0]['usecase']
        lines.append('digraph depends {')
        lines.append(f'    graph [label="License Compatibility Graph ({usecase})" labelloc=t]')
        lines.append('    node [shape=plaintext]')
        for outbound in licenses:
            finished[outbound] = {}
            for inbound in licenses:
                if inbound not in finished:
                    finished[inbound] = {}
                if inbound == outbound:
                    continue

                if display_compats[outbound][inbound] == []:
                    if discard_unsupported:
                        continue
                if display_compats[inbound][outbound] == []:
                    if discard_unsupported:
                        continue

                if finished[outbound].get(inbound, False):
                    continue
                elif finished[inbound].get(outbound, False):
                    continue

                lines.append(self._license_license_compat(outbound, inbound, display_compats[outbound][inbound], display_compats[inbound][outbound]))
                finished[outbound][inbound] = True
                finished[inbound][outbound] = True

        lines.append('}')
        return '\n'.join(lines)

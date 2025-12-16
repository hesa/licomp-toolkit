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
                
        lines = {}
        
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

    def format_display_compatibilities(self, compats):
        display_compats = self._pre_format_display_compatibilities(compats)
        return json.dumps(display_compats, indent=4)

class YamlLicompToolkitFormatter(LicompToolkitFormatter):

    def format_compatibilities(self, compat):
        return yaml.safe_dump(compat, indent=4)

    def format_licomp_resources(self, licomp_resources):
        return yaml.safe_dump(licomp_resources, indent=4)

    def format_licomp_licenses(self, licomp_licenses):
        return yaml.safe_dump(licomp_licenses, indent=4)

    def format_licomp_versions(self, licomp_versions):
        return yaml.safe_dump(licomp_versions, indent=4)

    def format_display_compatibilities(self, compats):
        display_compats = self._pre_format_display_compatibilities(compats)
        return yaml.safe_dump(display_compats, indent=4)

class TextLicompToolkitFormatter(LicompToolkitFormatter):

    def format_licomp_resources(self, licomp_resources):
        return "\n".join(licomp_resources)

    def format_licomp_licenses(self, licomp_licenses):
        return "\n".join(licomp_licenses)

    def __get_responses(self, results, indent=""):
        output = []
        for res in ['yes', 'no', 'schneben']:
            result = results.get(res)
            if not result:
                count = 0
            else:
                count = result["count"]
            output.append(f'{indent}{res}: {count}')

        return output

    def __compatibility_statuses(self, statuses, indent=""):
        output = []
        for status, values in statuses.items():
            resources = []
            for value_object in values:
                resources.append(value_object['resource_name'])
            output.append(f'{indent}{status}: {", ".join(resources)}')

        return output

    def __statuses(self, statuses, indent=""):
        output = []
        for status, values in statuses.items():
            resources = []
            for value_object in values:
                resources.append(value_object['resource_name'])
            output.append(f'{indent}{status}: {", ".join(resources)}')

        return output

    def _format_compat(self, compat):
        PAREN_OPEN = '('
        PAREN_START = ')'
        return f'{PAREN_OPEN}{compat}{PAREN_START}'

    def format_compatibilities_object(self, compat_object, indent=''):
        compatibility_check = compat_object["compatibility_check"]
        output = []

        if compatibility_check == "outbound-license -> inbound-license":
            if not compat_object["compatibility_object"]:
                pass
            else:
                compat_object = compat_object["compatibility_object"]
            details = compat_object["compatibility_details"]
            summary = details["summary"]

            output.append(f'{indent}{compat_object["outbound_license"]} -> {compat_object["inbound_license"]} {self._format_compat(compat_object["compatibility"])}')
            output.append(f'{indent}  compatibility: {compat_object["compatibility"]}')
            output.append(f'{indent}  compatibility details:')
            output += self.__compatibility_statuses(summary['compatibility_statuses'], f'{indent}  ')
        if compatibility_check == "outbound-license -> inbound-expression":
            operator = compat_object["compatibility_object"]["operator"]
            output.append(f'{indent}{operator} {self._format_compat(compat_object["compatibility"])}')
            for operand in compat_object["compatibility_object"]["operands"]:
                res = self.format_compatibilities_object(operand['compatibility_object'], indent=f'{indent}  ')
                output.append(res)

        if compatibility_check == "outbound-expression -> inbound-license":
            operator = compat_object["operator"]
            output.append(f'{indent}{operator} {self._format_compat(compat_object["compatibility"])}')
            for operand in compat_object["operands"]:
                res = self.format_compatibilities_object(operand['compatibility_object'], indent=f'{indent}  ')
                output.append(res)
        if compatibility_check == "outbound-expression -> inbound-expression":
            operator = compat_object["operator"]
            compat = compat_object["compatibility"]
            output.append(f'{indent}{operator} {self._format_compat(compat)}')
            for operand in compat_object['operands']:
                res = self.format_compatibilities_object(operand['compatibility_object'], indent=f'{indent}  ')
                output.append(f'{res}')

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
        output.append(self.format_compatibilities_object(compat["compatibility_report"], '  '))

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
            #print(compat)
            if not value:
                value = compat
            else:
                if compat != value:
                    same = False

        if same:
            line = _line_map.get(value, '')
            color = _color_map.get(value, 'darkblue')
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
        finished = {}
        usecase = compats[licenses[0]][licenses[0]]['compatibilities'][0]['usecase']
        lines.append('digraph depends {')
        lines.append(f'    graph [label="License Compatibility Graph ({usecase})" labelloc=t]')
        lines.append('    node [shape=plaintext]')
        for outbound in licenses:
            finished[outbound] = {}
            for inbound in licenses:
                if inbound == outbound:
                    continue
                if not display_compats[outbound][inbound]:
                    #print("skip.... since " + str(display_compats[outbound][inbound]))
                    continue

                #print(f'{outbound} ---> {inbound}')
                lines.append(self._license_license_compat(outbound, inbound, display_compats[outbound][inbound], display_compats[inbound][outbound]))
                display_compats[outbound][inbound] = False
                display_compats[inbound][outbound] = False

        lines.append('}')
        return '\n'.join(lines)

# SPDX-FileCopyrightText: 2025 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

import json

class LicompToolkitFormatter():

    @staticmethod
    def formatter(fmt):
        if fmt.lower() == 'json':
            return JsonLicompToolkitFormatter()
        if fmt.lower() == 'text':
            return TextLicompToolkitFormatter()

    def format_compatibilities(self, compat):
        return None

    def format_licomp_resources(self, licomp_resources):
        return None

    def format_licomp_licenses(self, licomp_licenses):
        return None

    def format_licomp_versions(self, licomp_versions):
        return None

class JsonLicompToolkitFormatter():

    def format_compatibilities(self, compat):
        return json.dumps(compat, indent=4)

    def format_licomp_resources(self, licomp_resources):
        return json.dumps(licomp_resources, indent=4)

    def format_licomp_licenses(self, licomp_licenses):
        return json.dumps(licomp_licenses, indent=4)

    def format_licomp_versions(self, licomp_versions):
        return json.dumps(licomp_versions, indent=4)

class TextLicompToolkitFormatter():

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

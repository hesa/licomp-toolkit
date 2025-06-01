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

    def format_compatibilities(self, compat):
        summary = compat['summary']
        output = []
        nr_valid = summary['results']['nr_valid']
        output.append(f'{nr_valid} succesfull response(s)')
        if int(nr_valid) > 0:
            output.append('Results:')
            statuses = summary['compatibility_statuses']
            for status in statuses.keys():
                output.append(f'   {status}: {", ".join(statuses[status])}')
        return "\n".join(output)

    def format_licomp_versions(self, licomp_versions):
        lt = 'licomp-toolkit'
        res = [f'{lt}: {licomp_versions[lt]}']
        for k, v in licomp_versions['licomp-resources'].items():
            res.append(f'{k}: {v}')
        return '\n'.join(res)

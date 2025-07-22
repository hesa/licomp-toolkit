# SPDX-FileCopyrightText: 2024 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

from licomp.interface import Licomp
from licomp.interface import UseCase
from licomp.interface import Provisioning
from licomp.interface import LicompException
from licomp.return_codes import ReturnCodes
from licomp.interface import CompatibilityStatus

from licomp_osadl.osadl import LicompOsadl
from licomp_reclicense.reclicense import LicompReclicense
from licomp_proprietary.proprietary import LicompProprietary
from licomp_dwheeler.dwheeler import LicompDw
from licomp_hermione.hermione import LicompHermione
from licomp_gnuguide.gnuguide import GnuQuickGuideLicense

from licomp_toolkit.config import disclaimer
from licomp_toolkit.config import licomp_toolkit_version
from licomp_toolkit.config import cli_name

from licomp_toolkit.expr_parser import LicenseExpressionParser
from licomp_toolkit.expr_parser import COMPATIBILITY_TYPE
from licomp_toolkit.expr_parser import AND
from licomp_toolkit.expr_parser import OR

from licomp_toolkit.config import my_supported_api_version

class LicompToolkit(Licomp):
    """A class implementing Licomp, but for a misc Licomp resources
    and packaging the responses into a new reply
    (licomp_toolkit/reply_schema.json).

    LicompToolkit can check a single license agaisnt another for
    compatibility, but not license expressions.
    """

    def __init__(self):
        Licomp.__init__(self)
        self.LICOMP_RESOURCES = {}
        self.LICOMP_RESOURCE_NAMES = {
            "osadl": {
                "package": "licomp_osadl.osadl",
                "class": "LicompOsadl",
            },
            "reclicense": {
                "package": "licomp_reclicense.reclicense",
                "class": "LicompReclicense",
            },
            "hermione": {
                "package": "licomp_hermione.hermione",
                "class": "LicompHermione",
            },
            "dwheeler": {
                "package": "licomp_dwheeler.dwheeler",
                "class": "LicompDw",
            },
        }

    def supported_api_version(self):
        return my_supported_api_version

    def __add_to_list(self, store, data, name):
        if not data:
            return
        if data not in store:
            store[data] = []
        store[data].append(name)

    def __add_meta(self, compatibilities):
        compatibilities["meta"] = {}
        compatibilities["meta"]['disclaimer'] = disclaimer

    def licomp_resources(self):
        if not self.LICOMP_RESOURCES:
            for licomp in [LicompReclicense, LicompOsadl, LicompHermione, LicompProprietary, LicompDw, GnuQuickGuideLicense]:
                licomp_instance = licomp()
                self.LICOMP_RESOURCES[licomp_instance.name()] = licomp_instance
        return self.LICOMP_RESOURCES

    def __summarize_compatibility(self, compatibilities, outbound, inbound, usecase, provisioning, resources):
        compatibilities["summary"] = {}
        statuses = {}
        compats = {}
        compatibilities['nr_licomp'] = len(resources)
        #        for resource_name in self.licomp_resources():
        for compat in compatibilities["compatibilities"]:
            logging.debug(f': {compat}')
            logging.debug(f': {compat["resource_name"]}')
            self.__add_to_list(statuses, compat['status'], compat)
            self.__add_to_list(compats, compat['compatibility_status'], compat)
        compatibilities["summary"]["resources"] = [f'{x.name()}:{x.version()}' for x in self.licomp_resources().values()]
        compatibilities["summary"]["outbound"] = outbound
        compatibilities["summary"]["inbound"] = inbound
        compatibilities["summary"]["usecase"] = UseCase.usecase_to_string(usecase)
        compatibilities["summary"]["provisioning"] = Provisioning.provisioning_to_string(provisioning)
        compatibilities["summary"]["statuses"] = statuses
        compatibilities["summary"]["compatibility_statuses"] = compats

        compat_number = len(compatibilities["summary"]["statuses"].get("success", []))
        logging.debug(f': {compatibilities["summary"]["statuses"]}')
        results = {}
        results['nr_valid'] = f'{compat_number}'
        for key, value in compatibilities["summary"]["compatibility_statuses"].items():
            logging.debug(f': {len(value)}/{compat_number}')
            if compat_number == 0:
                continue
            else:
                if key == 'unsupported':
                    continue
                else:
                    count = len(value)
                    perc = len(value) / compat_number * 100
            results[key] = {
                'count': count,
                'percent': perc,
            }
        compatibilities['summary']['results'] = results

    # override top class
    def outbound_inbound_compatibility(self, outbound, inbound, usecase, provisioning, resources=None):
        logging.debug(f'{inbound} {outbound} ')

        compatibilities = {}
        compatibilities['compatibilities'] = []

        if not resources:
            resources = self.licomp_resources().keys()

        for resource_name in resources:
            resource = self.licomp_resources()[resource_name]
            logging.debug(f'-- resource: {resource.name()}')

            compat = resource.outbound_inbound_compatibility(outbound, inbound, usecase, provisioning=provisioning)
            compatibilities['compatibilities'].append(compat)

        self.__summarize_compatibility(compatibilities, outbound, inbound, usecase, provisioning, resources)
        self.__add_meta(compatibilities)

        return compatibilities

    def supported_licenses(self):
        licenses = set()
        for resource in self.licomp_resources().values():
            licenses.update(set(resource.supported_licenses()))
        licenses = list(licenses)
        licenses.sort()
        return licenses

    def supported_provisionings(self):
        provisionings = set()
        for resource in self.licomp_resources().values():
            provisionings.update(set(resource.supported_provisionings()))
        return list(provisionings)

    def supported_usecases(self):
        usecases = set()
        for resource in self.licomp_resources().values():
            usecases.update(set(resource.supported_usecases()))
        return list(usecases)

    def disclaimer(self):
        return disclaimer

    def version(self, verbose=False):
        return licomp_toolkit_version

    def versions(self, verbose=False):
        resources = {}
        for resource in self.licomp_resources().values():
            resources[resource.name()] = resource.version()
        return {
            self.name(): self.version(),
            'licomp-resources': resources,
        }

    def name(self):
        return cli_name

class LicenseExpressionChecker():
    """This class can check compatibility between a single outbound
    license (e.g GPL-2.0-only) against an inbound license expression
    (e.g. MIT OR X11)
    """

    def __init__(self):
        self.le_parser = LicenseExpressionParser()
        self.licomp_toolkit = LicompToolkit()

    def __compatibility_status(self, compatibility):
        status = compatibility['summary']['results']
        rets = []
        for ret in status:
            if ret == 'nr_valid':
                continue
            elif not ret:
                pass
            elif ret == CompatibilityStatus.compat_status_to_string(CompatibilityStatus.UNSUPPORTED):
                pass
            else:
                rets.append(ret)

        if len(rets) == 0:
            return CompatibilityStatus.compat_status_to_string(CompatibilityStatus.UNSUPPORTED)

        if len(rets) == 1:
            return rets[0]

        return CompatibilityStatus.compat_status_to_string(CompatibilityStatus.MIXED)

    def check_compatibility(self,
                            outbound,
                            parsed_expression,
                            usecase,
                            provisioning,
                            resources,
                            detailed_report=True):

        compat_object = {
            COMPATIBILITY_TYPE: parsed_expression[COMPATIBILITY_TYPE],
            'compatibility_check': 'outbound-expression -> inbound-license',
        }

        if parsed_expression[COMPATIBILITY_TYPE] == 'license':
            compat_object['compatibility_check'] = 'outbound-license -> inbound-license'
            lic = parsed_expression['license']
            compat = self.licomp_toolkit.outbound_inbound_compatibility(outbound,
                                                                        lic,
                                                                        usecase,
                                                                        provisioning,
                                                                        resources)
            compat_object['compatibility'] = self.__compatibility_status(compat)
            if detailed_report:
                compat_object['compatibility_details'] = compat
            else:
                compat_object['compatibility_details'] = None
            compat_object['inbound_license'] = lic
            compat_object['outbound_license'] = outbound
            compat_object['compatibility_object'] = {}

        else:
            operator = parsed_expression['operator']
            operands = parsed_expression['operands']
            compat_object['operator'] = operator

            compat_object['inbound_license'] = self.le_parser.to_string(parsed_expression)
            compat_object['outbound_license'] = outbound
            compat_object['compatibility_details'] = None
            operands_object = []
            for operand in operands:
                operand_compat = self.check_compatibility(outbound, operand, usecase, provisioning, resources, detailed_report=detailed_report)
                operand_object = {
                    'compatibility_object': operand_compat,
                    'compatibility': operand_compat['compatibility'],
                }
                operands_object.append(operand_object)

            compat_object['compatibility'] = self.summarise_compatibilities(operator, operands_object)
            compat_object['operands'] = operands_object

        return compat_object

    def __init_summary(self, operands):
        summary = {
            "yes": 0,
            "no": 0,
            "depends": 0,
            "unknown": 0,
            "unsupported": 0,
            "mixed": 0,
        }
        for operand in operands:
            compat = operand['compatibility']
            summary[compat] = summary[compat] + 1
        return summary

    def __summarise_compatibilities_and(self, operands):
        nr_operands = len(operands)
        summary = self.__init_summary(operands)

        if summary['no'] != 0:
            return 'no'

        if summary['yes'] == nr_operands:
            return "yes"

        return "no"

    def __summarise_compatibilities_or(self, operands):
        summary = self.__init_summary(operands)

        if summary['yes'] != 0:
            return 'yes'

        return "no"

    def summarise_compatibilities(self, operator, operands):
        return {
            AND: self.__summarise_compatibilities_and,
            OR: self.__summarise_compatibilities_or,
        }[operator](operands)


class ExpressionExpressionChecker():
    """
    This class can check, for compatibility;
    * inbound license expression (e.g. MIT OR Apache-2.0)
    * against outbound license expression (e.g. GPL-2.0-only OR BSD-2-Clause)
    """

    def __init__(self):
        self.le_checker = LicenseExpressionChecker()
        self.le_parser = LicenseExpressionParser()
        self.licomp_toolkit = LicompToolkit()

    def __parsed_expression_to_name(self, parsed_expression):
        return parsed_expression[parsed_expression[COMPATIBILITY_TYPE]]

    def check_compatibility(self, outbound, inbound, usecase, provisioning, resources=None, detailed_report=True):

        # Check usecase
        try:
            usecase_obj = UseCase.string_to_usecase(usecase)
        except KeyError:
            raise LicompException(f'Usecase {usecase} not supported.', ReturnCodes.LICOMP_UNSUPPORTED_USECASE)

        # Check provisioning
        try:
            provisioning_obj = Provisioning.string_to_provisioning(provisioning)
        except KeyError:
            raise LicompException(f'Provisioning {provisioning} not supported.', ReturnCodes.LICOMP_UNSUPPORTED_PROVISIONING)

        licomp_resources = list(self.licomp_toolkit.licomp_resources().keys())
        if not resources:
            resources = licomp_resources
        else:
            resources = resources

        unavailable_resources = []

        for resource in resources:
            resource_object = self.licomp_toolkit.licomp_resources()[resource]
            unavailable_reasons = []

            # is usecase supported by resource
            if not resource_object.usecase_supported(UseCase.string_to_usecase(usecase)):
                unavailable_reasons.append(f'Usecase "{usecase}" not supported')

            # is prov case supported by resource
            if not resource_object.provisioning_supported(Provisioning.string_to_provisioning(provisioning)):
                unavailable_reasons.append(f'Provisioning case "{provisioning}" not supported')

            if unavailable_reasons:
                unavailable_resources.append({
                    "resource": resource,
                    'reasons': ", ".join(unavailable_reasons),
                })

        unavailable_resource_keys = [resource['resource'] for resource in unavailable_resources]
        available_resources = [resource for resource in resources if resource not in unavailable_resource_keys]

        inbound_parsed = self.le_parser.parse_license_expression(inbound)
        outbound_parsed = self.le_parser.parse_license_expression(outbound)

        compatibility_object = self.__check_compatibility(outbound_parsed,
                                                          inbound_parsed,
                                                          usecase_obj,
                                                          provisioning_obj,
                                                          resources,
                                                          detailed_report)
        return {
            'inbound': inbound,
            'outbound': outbound,
            'usecase': usecase,
            'resources': resources,
            'provisioning': provisioning,
            'compatibility': compatibility_object['compatibility'],
            'compatibility_report': compatibility_object,
            'unavailable_resources': unavailable_resources,
            'available_resources': available_resources,
        }

    def __check_compatibility(self,
                              outbound_parsed,
                              inbound_parsed,
                              usecase,
                              provisioning,
                              resources,
                              detailed_report=True):

        outbound_type = outbound_parsed[COMPATIBILITY_TYPE]
        compat_object = {
            COMPATIBILITY_TYPE: outbound_type,
            'inbound_license': self.le_parser.to_string(inbound_parsed),
            'outbound_license': self.le_parser.to_string(outbound_parsed),
        }

        if outbound_type == 'license':
            compat_object['compatibility_check'] = f'outbound-license -> inbound-{inbound_parsed["compatibility_type"]}'
            outbound_parsed_license = outbound_parsed['license']
            # Check if:
            #    outbound license
            #    is compatible with
            #    inbound license
            compat = self.le_checker.check_compatibility(outbound_parsed_license,
                                                         inbound_parsed,
                                                         usecase,
                                                         provisioning,
                                                         resources,
                                                         detailed_report)
            compat_object['compatibility'] = compat['compatibility']
            compat_object['compatibility_object'] = compat
            compat_object['compatibility_details'] = None

        elif outbound_type == 'expression':
            compat_object['compatibility_details'] = None
            compat_object['compatibility_check'] = f'outbound-expression -> inbound-{inbound_parsed["compatibility_type"]}'
            operator = outbound_parsed['operator']
            operands = outbound_parsed['operands']

            compat_object['operator'] = operator

            operands_object = []
            for operand in operands:
                # Check if:
                #    operand from outbound license
                #    is compatible with
                #    inbound license
                operand_compat = self.__check_compatibility(operand,
                                                            inbound_parsed,
                                                            usecase,
                                                            provisioning,
                                                            resources,
                                                            detailed_report)
                operand_object = {
                    'compatibility_object': operand_compat,
                    'compatibility': operand_compat['compatibility'],
                }
                operands_object.append(operand_object)

            compat_object['compatibility'] = self.le_checker.summarise_compatibilities(operator, operands_object)
            compat_object['operands'] = operands_object

        return compat_object

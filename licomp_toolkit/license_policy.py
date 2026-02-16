# SPDX-FileCopyrightText: 2024 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

from collections import OrderedDict

from functools import cmp_to_key
import json
import logging

from licomp_toolkit.toolkit import LicompToolkit
from licomp.interface import UseCase
from licomp.interface import Provisioning
from licomp.interface import Modification

class LicensePolicyException(Exception):

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class LicensePolicy:

    def __init__(self, policy_file):
        data = self._read_json_file(policy_file)
        self.policy_meta = data['meta']
        self.policy = data['policy']

    def _read_json_data(self, data):
        return json.load(data)

    def _read_json_file(self, file_name):
        with open(file_name) as fp:
            return self._read_json_data(fp)

    def allowed(self):
        return self.policy['allowed']

    def avoided(self):
        return self.policy['avoided']

    def denied(self):
        return self.policy['denied']

    def meta(self):
        return self.policy_meta

    def list_presence(self, lic, ignore_missing=False):

        if lic in self.allowed():
            return 1, self.allowed().index(lic)
        if lic in self.avoided():
            return 2, self.avoided().index(lic)
        if lic in self.denied():
            return 3, self.denied().index(lic)

        if ignore_missing:
            return None, None
        raise LicensePolicyException(f'License "{lic}" is not present in any of the policy\'s lists. Licenses: {self.allowed()}, {self.avoided()} ')

    def list_nr_to_name(self, nr):
        return {
            1: 'allowed',
            2: 'avoided',
            3: 'denied'}.get(nr, '')

    def list_name_to_nr(self, nr):
        return {
            'allowed': 1,
            'avoided': 2,
            'denied': 3}.get(nr, None)

    def compare_preferences(self, lic1, lic2, ignore_missing=False):
        return self.compare_preferences_general(lic1, lic2, ignore_missing=ignore_missing)

    def compare_preferences_expressions(self, lic1, lic2, key, ignore_missing=False):
        return self.compare_preferences_general(lic1, lic2, key, ignore_missing=ignore_missing)

    def compare_preferences_general(self, lic1, lic2, key=None, ignore_missing=False):
        """

        returns
        * negative if lic1 is more preferred than lic2
        * None if both licenses are denied
        raises
        * LicensePolicyException if at least one license is not listed (if ignore_missing, then both licenses need to be not listed to raise exception)
        """
        logging.debug(f'compare_preferences {lic1}, {lic2}, {key}, {ignore_missing}')
        if key:
            list_key = key.replace('_license', '')
            lic1_name = lic1[list_key]['license']
            lic2_name = lic2[list_key]['license']
            if lic1[list_key]['type'] == 'license':
                lic1_list, lic1_index = self.list_presence(lic1[list_key]['license'], ignore_missing=False)
            else:
                lic1_list_name = lic1[list_key]['preferences']['license_list']
                lic1_list = self.list_name_to_nr(lic1_list_name)
                lic1_index = lic1[list_key]['preferences']['license_index']

            if lic2[list_key]['type'] == 'license':
                lic2_list, lic2_index = self.list_presence(lic2[list_key]['license'], ignore_missing=False)
            else: # license-expression
                lic2_list_name = lic2[list_key]['preferences']['license_list']
                lic2_list = self.list_name_to_nr(lic2_list_name)
                lic2_index = lic2[list_key]['preferences']['license_index']
        else:
            lic1_name = lic1
            lic2_name = lic2
            lic1_list, lic1_index = self.list_presence(lic1, ignore_missing=ignore_missing)
            lic2_list, lic2_index = self.list_presence(lic2, ignore_missing=ignore_missing)

        logging.debug(f'compare_preferences:   "{lic1_list}", "{lic1_index}" "{lic2_list}", "{lic2_index}"')

        if (not lic1_list) and (not lic2_list):
            if ignore_missing:
                logging.debug(f'compare_preferences({lic1_name}, {lic2_name}, {ignore_missing}): ignore since both None')
                return None

            raise LicensePolicyException(f'License "{lic1_name}" and/or "{lic2_name}" is not present in any of the policy\'s lists.')

        if lic1_list == lic2_list:
            # if both are denied, return None to indicate "error"
            if lic1_list == 3:
                return None
            return lic1_index - lic2_index

        if not lic1_list:
            return 1
        if not lic2_list:
            return -1

        return lic1_list - lic2_list

    def most_preferred(self, lic1, lic2, ignore_missing=False):
        pref = self.compare_preferences(lic1, lic2, ignore_missing)
        if pref is None:
            return None
        if pref < 0:
            return lic1
        return lic2

    def OBSOLETE_preferred_score_ignore_missing(self, lic1, lic2):
        pref = self.compare_preferences(lic1, lic2, ignore_missing=True)
        if pref is None:
            return 10000
        if pref < 0:
            return -1
        if lic1 == lic2:
            return 0
        return 1

    def preferred_score_licenses(self, lic1, lic2, key):
        logging.debug(f'preferred_score_licenses {lic1}, {lic2}, {key}')
        pref = self.compare_preferences_expressions(lic1, lic2, key)
        if pref < 0:
            return -1
        if lic1 == lic2:
            return 0
        return 1

    def preferred_score_inbounds(self, lic1, lic2):
        logging.debug(f'preferred_score_inbounds {lic1}, {lic2}')
        return self.preferred_score_licenses(lic1, lic2, 'inbound_license')

    def preferred_score_outbounds(self, lic1, lic2):
        logging.debug(f'preferred_score_outbounds {lic1}, {lic2}')
        return self.preferred_score_licenses(lic1, lic2, 'outbound_license')

    def least_preferred(self, lic1, lic2, ignore_missing=False):
        most_preferred = self.most_preferred(lic1, lic2, ignore_missing)
        if most_preferred == lic1:
            return lic2
        return lic1

class DefaultLicensePolicy(LicensePolicy):

    def __init__(self, resources, usecase, provisioning):
        self.lt = LicompToolkit()
        self.__licenses(resources, usecase, provisioning)
        license_order = self.__order(resources, usecase, provisioning)
        self.policy_meta = {}
        self.policy = {
            'allowed': license_order,
            'avoided': [],
            'denied': [],
        }

    def __order(self, resources, usecase, provisioning):
        scores = {}
        for lic in self.licenses:
            scores[lic] = 0
        for out_license in self.licenses:
            for in_license in self.licenses:
                for resource in self.resources:
                    compat = resource.outbound_inbound_compatibility(out_license,
                                                                     in_license,
                                                                     UseCase.string_to_usecase(usecase),
                                                                     Provisioning.string_to_provisioning(provisioning),
                                                                     Modification.UNMODIFIED)
                    if compat['compatibility_status'] == 'yes':
                        scores[in_license] += 1

        scores_dict = OrderedDict(sorted(scores.items(), key=lambda x: x[1], reverse=True))
        return [x for (x, y) in scores_dict.items()]

    def __licenses(self, resources, usecase, provisioning):
        self.resources = []
        self.licenses = []

        logging.debug(f'__licenses {resources}, {usecase}, {provisioning}')
        for resource in resources:
            for licomp_resource in self.lt.licomp_resources():
                if resource == licomp_resource:
                    self.licenses += self.lt.licomp_resources()[licomp_resource].supported_licenses()
                    self.resources.append(self.lt.licomp_resources()[licomp_resource])
        logging.debug(f'__licenses {resources}, {usecase}, {provisioning} ==> {self.licenses}')


class LicensePolicyHandler:

    def __init__(self, policy_file=None, resources=None, usecase=None, provisioning=None):
        logging.debug("LicensePolicyHandler()")
        if policy_file:
            self.policy = LicensePolicy(policy_file)
            self.policy_type = 'policy_file'
            self.policy_file = policy_file
        else:
            self.policy = DefaultLicensePolicy(resources, usecase, provisioning)
            self.policy_type = 'default'
            self.policy_file = None

    def __is_license_expression(self, lic):
        CONTAINS_AND = 'AND' in lic
        CONTAINS_OR = 'OR' in lic
        return CONTAINS_AND or CONTAINS_OR

    def usable_license(self, lic, key):
        if key in lic:
            license_name = lic[key]['license']
        else:
            license_name = lic
        if self.__is_license_expression(license_name):
            # should have been checked already, so skip
            policy_ok = True
        else:
            policy_ok = license_name in (self.policy.allowed() + self.policy.avoided())
        compat_ok = lic['compatibility'] == 'yes'

        ret = policy_ok and compat_ok
        logging.debug(f'usable_license {lic} |  policy_ok: {policy_ok}, compat_ok: {compat_ok}  ===> {ret}')

        return ret

    def unusable_licenses(self, licenses, key):
        problematic_licenses = []
        for lic in licenses:
            license_name = lic[key]['license']
            if self.__is_license_expression(license_name):
                # should have been checked already, so skip
                policy_ok = True
            else:
                policy_ok = license_name in (self.policy.allowed() + self.policy.avoided())
            compat_ok = lic['compatibility'] == 'yes'

            ret = policy_ok and compat_ok
            logging.debug(f'unusable_license {lic} |  policy_ok: {policy_ok}, compat_ok: {compat_ok}  ===> {ret}')
            if not ret:
                problematic_licenses.append(lic)
        return len(problematic_licenses) > 0

    def scored_general(self, licenses, operator, key):
        compare_function = {
            'inbound': self.policy.preferred_score_inbounds,
            'outbound': self.policy.preferred_score_outbounds,
        }[key]
        if operator == "OR":
            logging.debug(f'preferred_licenses {licenses}, {operator}')
            filtered_licenses = []
            unusable_licenses = []
            for lic in licenses:
                if self.usable_license(lic, key):
                    filtered_licenses.append(lic)
                else:
                    print("UNUSABLE: " + str(key))
                    print("UNUSABLE: " + str(lic))
                    unusable_licenses.append(lic[key])
            sorted_licenses = sorted(filtered_licenses, key=cmp_to_key(compare_function))
            return sorted_licenses, unusable_licenses
        elif operator == "AND":
            if self.unusable_licenses(licenses, key):
                sorted_licenses = []
                unusable_licenses = [x[key] for x in licenses]
            else:
                sorted_licenses = sorted(licenses, key=cmp_to_key(compare_function))
                unusable_licenses = []

            return sorted_licenses, unusable_licenses
        else:
            raise Exception(f'scored_general got a bad operator "{operator}"')

    def scored_inbounds(self, inbounds, operator):
        return self.scored_general(inbounds, operator, 'inbound')

    def scored_outbounds(self, outbounds, operator):
        return self.scored_general(outbounds, operator, 'outbound')

    def __check_policy_check(self, reply):
        keys = [
            'license',
            'type',
            'preferences:license',
            'preferences:license_list',
            'preferences:license_index',
        ]
        for key in keys:
            in_value = reply['inbound']
            out_value = reply['outbound']
            for sub_key in key.split(':'):
                assert sub_key in in_value # noqa: S101
                assert sub_key in out_value # noqa: S101
                in_value = in_value[sub_key]
                out_value = out_value[sub_key]

        assert 'compatibility' in reply # noqa: S101
        assert 'unusable' in reply # noqa: S101

    def __pack_policy_check(self, outbound_pref, inbound_pref, compat, unusable):
        return {
            'outbound': outbound_pref,
            'inbound': inbound_pref,
            'compatibility': compat,
            'unusable': unusable,
        }

    def __pack_policy_unusable(self, unusables):
        return unusables

    def __pack_policy_preferences(self, license_string, license_list, license_index):
        return {
            'license': license_string,
            'license_list': license_list,
            'license_index': license_index,
        }

    def __pack_policy_check_license(self, license_name, license_type, pref_lic, pref_lic_list, pref_lic_idx):
        return {
            'license': license_name,
            'type': license_type,
            'preferences': {
                'license': pref_lic,
                'license_list': pref_lic_list,
                'license_index': pref_lic_idx,
            },
        }

    def __apply_to_compat_object(self, compat_object, ignore_missing=False, indent=0):
        """
        Specification of the policy_check format

        define license_data:

          license (str)
          license_type (str: license | license-expression)
          preferrences {
            license
            license_list
            license_index
          }

          unusable [
            { license (str),
              reason (str)
            }
          ]

        inbound (license_data)
        outbound (license_data)
        compatibility (str)

        """
        unusable = []
        if 'outbound-expression' in compat_object['compatibility_check']:
            operator = compat_object['operator']
            outbounds = []
            for operand in compat_object['operands']:
                operand['compatibility_object']['TEST'] = "Liverpool"
                self.__apply_to_compat_object(operand['compatibility_object'], indent + 4)
                self.__check_policy_check(operand['compatibility_object']['policy_check'])

                outbounds.append(operand['compatibility_object']['policy_check'])

            scored_outbounds, unusable = self.scored_outbounds(outbounds, operator)

            outbound_list = []
            outbound_list_index = -1
            preferred_inbound_license = None
            compatibility = 'no'

            if len(scored_outbounds) > 0:
                if operator == 'AND':
                    outbound_name = ' AND '.join([x['outbound']['preferences']['license'] for x in scored_outbounds])
                    outbound_pref = scored_outbounds[-1]
                else:
                    outbound_name = scored_outbounds[0]['outbound']['preferences']['license']
                    outbound_pref = scored_outbounds[0]

                outbound_list = outbound_pref['outbound']['preferences']['license_list']
                outbound_list_index = outbound_pref['outbound']['preferences']['license_index']
                inbound_prefs = outbound_pref['inbound']['preferences']
                preferred_inbound_license = inbound_prefs['license']
                preferred_inbound_license_list = inbound_prefs['license_list']
                preferred_inbound_license_index = inbound_prefs['license_index']

                compatibility = 'yes'
            else:
                outbound_name = None
                outbound_list = None
                outbound_list_index = None

                preferred_inbound_license = None
                preferred_inbound_license_list = None
                preferred_inbound_license_index = None

                compatibility = 'no'
            if 'inbound-expression' in compat_object['compatibility_check']:
                inbound_license_type = 'license-expression'
            else:
                inbound_license_type = 'license'

            policy_check_inbound_license = self.__pack_policy_check_license(
                compat_object['inbound_license'],
                inbound_license_type,
                preferred_inbound_license,
                preferred_inbound_license_list,
                preferred_inbound_license_index,
            )
            policy_check_outbound_license = self.__pack_policy_check_license(
                compat_object['outbound_license'],
                'license-expression',
                outbound_name,
                outbound_list,
                outbound_list_index,
            )
            unusable = self.__pack_policy_unusable(unusable)
            policy_license_object = self.__pack_policy_check(
                policy_check_outbound_license,
                policy_check_inbound_license,
                compatibility,
                unusable,
            )

            compat_object['policy_check'] = policy_license_object

        elif 'outbound-license' in compat_object['compatibility_check']:

            if 'inbound-expression' in compat_object['compatibility_check']:
                inner_compat_object = compat_object
                operator = inner_compat_object['operator']
                inbounds = []
                for operand in inner_compat_object['operands']:
                    self.__apply_to_compat_object(operand['compatibility_object'], indent + 4)
                    self.__check_policy_check(operand['compatibility_object']['policy_check'])
                    inbounds.append(operand['compatibility_object']['policy_check'])

                scored_inbounds, unusable = self.scored_inbounds(inbounds, operator)
                inbound_list = ''
                inbound_list_index = -1
                preferred_inbound_license = None

                if len(scored_inbounds) > 0:
                    if operator == 'AND':
                        # use last (least preferred) license
                        inbound_list = scored_inbounds[-1]['inbound']['preferences']['license_list']
                        inbound_list_index = scored_inbounds[-1]['inbound']['preferences']['license_index']
                        preferred_inbound_license = ' AND '.join([x['inbound']['preferences']['license'] for x in scored_inbounds])
                    else:
                        # use first (most preferred) license
                        inbound_list = scored_inbounds[0]['inbound']['preferences']['license_list']
                        inbound_list_index = scored_inbounds[0]['inbound']['preferences']['license_index']
                        preferred_inbound_license = scored_inbounds[0]['inbound']['preferences']['license']

                out_lic = inner_compat_object["outbound_license"]
                out_list_nr, out_index = self.policy.list_presence(out_lic, ignore_missing=True)
                out_list_name = self.policy.list_nr_to_name(out_list_nr)

                policy_check_inbound_license = self.__pack_policy_check_license(
                    inner_compat_object['inbound_license'],
                    'license-expression',
                    preferred_inbound_license,
                    inbound_list,
                    inbound_list_index,
                )
                policy_check_outbound_license = self.__pack_policy_check_license(
                    out_lic,
                    'license',
                    out_lic,
                    out_list_name,
                    out_index,
                )
                packed_unusable = self.__pack_policy_unusable(unusable)
                policy_license_object = self.__pack_policy_check(
                    policy_check_outbound_license,
                    policy_check_inbound_license,
                    compat_object['compatibility'],
                    packed_unusable)
                inner_compat_object['policy_check'] = policy_license_object

            if 'inbound-license' in compat_object['compatibility_check']:

                in_lic = compat_object['inbound_license']
                in_list_nr, in_list_index = self.policy.list_presence(in_lic, ignore_missing=True)
                in_list_name = self.policy.list_nr_to_name(in_list_nr)

                out_lic = compat_object["outbound_license"]
                out_list_nr, out_index = self.policy.list_presence(out_lic, ignore_missing=True)
                out_list_name = self.policy.list_nr_to_name(out_list_nr)

                policy_check_inbound_license = self.__pack_policy_check_license(
                    in_lic,
                    'license',
                    in_lic,
                    in_list_name,
                    in_list_index,
                )
                policy_check_outbound_license = self.__pack_policy_check_license(
                    out_lic,
                    'license',
                    out_lic,
                    out_list_name,
                    out_index,
                )
                packed_unusable = self.__pack_policy_unusable(unusable)
                policy_license_object = self.__pack_policy_check(
                    policy_check_outbound_license,
                    policy_check_inbound_license,
                    compat_object['compatibility'],
                    packed_unusable,
                )
                compat_object['policy_check'] = policy_license_object

        else:
            raise Exception("We should not be here")
        return None

    def apply_policy(self, compat_report, ignore_missing=False):
        if not self.policy:
            logging.debug('apply_policy, no policy. Creating default one')
            resources = compat_report['resources']
            usecase = compat_report['usecase']
            provisioning = compat_report['provisioning']
            self.policy = DefaultLicensePolicy(resources, usecase, provisioning)
            self.policy_type = 'default'
            self.policy_file = None

        top_object = compat_report['compatibility_report']
        logging.debug("apply_policy")
        self.__apply_to_compat_object(top_object,
                                      ignore_missing=ignore_missing)
        self.__check_policy_check(top_object['policy_check'])
        meta = compat_report['meta']
        meta['policy_type'] = self.policy_type
        meta['policy_file'] = self.policy_file
        return compat_report

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
        raise LicensePolicyException(f'License "{lic}" is not present in any of the policy\'s lists.')

    def list_nr_to_name(self, nr):
        return {
            1: 'allowed',
            2: 'avoided',
            3: 'denied'}.get(nr, -1)

    def compare_preferences(self, lic1, lic2, ignore_missing=False):
        """
        
        returns
        * negative if lic1 is more preferred than lic2
        * None if both licenses are denied
        raises
        * LicensePolicyException if at least one license is not listed (if ignore_missing, then both licenses need to be not listed to raise exception)
        """
        lic1_list, lic1_index = self.list_presence(lic1, ignore_missing)
        lic2_list, lic2_index = self.list_presence(lic2, ignore_missing)
        logging.debug(f'compare_preferences({lic1}, {lic2}, {ignore_missing})')
        logging.debug(f'compare_preferences:   "{lic1_list}", "{lic1_index}" "{lic2_list}", "{lic2_index}"')

        if (not lic1_list) and (not lic2_list):
            if ignore_missing:
                logging.debug(f'compare_preferences({lic1}, {lic2}, {ignore_missing}): ignore since both None')
                return None
            
            raise LicensePolicyException(f'License "{lic}" is not present in any of the policy\'s lists.')
        
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
        if pref == None:
            return None
        if pref < 0:
            return lic1
        return lic2
    
    def preferred_score_ignore_missing(self, lic1, lic2):
        pref = self.compare_preferences(lic1, lic2, ignore_missing=True)
        if pref == None:
            return 10000
        if pref < 0:
            return -1
        if lic1 == lic2:
            return 0
        return 1
    
    def preferred_score_licenses(self, lic1, lic2, key):
        logging.debug(f'preferred_score_licenses({lic1}, {lic2}, {key})')
        pref = self.compare_preferences(lic1[key], lic2[key])
        if pref < 0:
            return -1
        if lic1 == lic2:
            return 0
        return 1

    def preferred_score_inbounds(self, lic1, lic2):
        logging.debug(f'preferred_score_inbounds({lic1}, {lic2})')
        return self.preferred_score_licenses(lic1, lic2, 'inbound_license')
    
    def preferred_score_outbounds(self, lic1, lic2):
        logging.debug(f'preferred_score_inbounds({lic1}, {lic2})')
        return self.preferred_score_licenses(lic1, lic2, 'inbound_license')
    
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
            'denied': []
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
        return [x for (x,y) in scores_dict.items()]

    def __licenses(self, resources, usecase, provisioning):
        self.resources = []
        self.licenses = []        

        logging.debug(f'__licenses({resources}, {usecase}, {provisioning})')
        for resource in resources:
            for licomp_resource in self.lt.licomp_resources():
                if resource == licomp_resource:
                    self.licenses += self.lt.licomp_resources()[licomp_resource].supported_licenses()
                    self.resources.append(self.lt.licomp_resources()[licomp_resource])
        logging.debug(f'__licenses({resources}, {usecase}, {provisioning}) ==> {self.licenses}')

class LicensePolicyHandler:

    def __init__(self, policy_file=None):
        logging.debug("LicensePolicyHandler()")
        if policy_file:
            self.policy = LicensePolicy(policy_file)
            self.policy_type = 'policy_file'
            self.policy_file = policy_file
        else:
            self.policy = None
            self.policy_type = None
            self.policy_file = None

    def __is_license_expression(self, lic):
        CONTAINS_AND = 'AND' in lic
        CONTAINS_OR = 'OR' in lic
        return CONTAINS_AND or CONTAINS_OR
        
        
    def usable_license(self, lic):
        license_name =  lic['inbound_license']
        if self.__is_license_expression(license_name):
            # should have been checked already, so skip
            policy_ok = True
        else:
            policy_ok = license_name in (self.policy.allowed() + self.policy.avoided())
        compat_ok = lic['compatibility'] == 'yes'

        ret = policy_ok and compat_ok
        logging.debug(f'usable_license({lic}) |  policy_ok: {policy_ok}, compat_ok: {compat_ok}  ===> {ret}')

        return ret
            
    def scored_general(self, licenses, operator, key):
        if operator == "OR":
            logging.debug(f'preferred_licenses({licenses}, {operator})')
            filtered_licenses = [x for x in licenses if self.usable_license(x)]
            if key == 'inbound_license':
                sorted_licenses = sorted(filtered_licenses, key=cmp_to_key(self.policy.preferred_score_inbounds))
            elif key == 'outbound_license':
                sorted_licenses = sorted(filtered_licenses, key=cmp_to_key(self.policy.preferred_score_outbounds))
            logging.debug(f'sorted_licenses: {[x["inbound_license"] for x in sorted_licenses]})')
            return sorted_licenses
        elif operator == "AND":
            if key == 'inbound_license':
                sorted_licenses = sorted(licenses, key=cmp_to_key(self.policy.preferred_score_inbounds))
            elif key == 'outbound_license':
                sorted_licenses = sorted(licenses, key=cmp_to_key(self.policy.preferred_score_outbounds))
            return sorted_licenses
        else:
            raise Exception("TODO fix this")
        
    def scored_inbounds(self, inbounds, operator):
        return self.scored_general(inbounds, operator, 'inbound_license')
        
    def scored_outbounds(self, outbounds, operator):
        return self.scored_general(outbounds, operator, 'outbound_license')
        
    def __apply_to_compat_object(self, compat_object, ignore_missing=False, indent=0):
        if 'outbound-expression' in compat_object['compatibility_check']:
            operator = compat_object['operator']
            outbounds = []
            for operand in compat_object['operands']:
                self.__apply_to_compat_object(operand['compatibility_object'], indent+4)
                outbounds.append(operand['compatibility_object']['policy_check'])
                
            scored_outbounds = self.scored_outbounds(outbounds, operator)
            outbound_list = []
            outbound_list_index = -1
            if len(scored_outbounds) > 0:
                outbound_list = scored_outbounds[0]['outbound_list']
                outbound_list_index = scored_outbounds[0]['outbound_list_index']
            compat_object['policy_check'] = {
                'outbound_license': compat_object['outbound_license'],
                'outbound_license_type': 'license-expression',
                'outbound_licenses': scored_outbounds,
                'outbound_list': outbound_list,
                'outbound_list_index': outbound_list_index,
            }
        elif 'outbound-license' in compat_object['compatibility_check']:
            # Get outbound license (not expression) data
            out_lic = compat_object["outbound_license"]
            out_list_nr, out_index = self.policy.list_presence(out_lic, ignore_missing=ignore_missing)
            out_list_name = self.policy.list_nr_to_name(out_list_nr)
            compat_object['policy_check'] = {
                'outbound_license': compat_object['outbound_license'],
                'outbound_license_type': 'license',
                'outbound_list': out_list_name,
                'outbound_list_index': out_index,
            }

            if 'inbound-expression' in compat_object['compatibility_check']:
                inner_compat_object = compat_object
                operator = inner_compat_object['operator']
                inbounds = []
                for operand in inner_compat_object['operands']:
                    self.__apply_to_compat_object(operand['compatibility_object'], indent+4)
                    inbounds.append(operand['compatibility_object']['policy_check'])
                scored_inbounds = self.scored_inbounds(inbounds, operator)
                inbound_list = []
                inbound_list_index = -1
                if len(scored_inbounds) > 0:
                    inbound_list = scored_inbounds[0]['inbound_list']
                    inbound_list_index = scored_inbounds[0]['inbound_list_index']

                inner_compat_object['policy_check'] = {
                    'check_type': 'inbound',
                    'inbound_license': inner_compat_object['inbound_license'],
                    'outbound_license': inner_compat_object['outbound_license'],
                    'inbound_license_type': 'license-expression',
                    'outbound_license_type': 'license',
                    'compatibility': compat_object['compatibility'],
                    'inbound_licenses': scored_inbounds,
                    'inbound_list': inbound_list,
                    'inbound_list_index': inbound_list_index,
                }
            if 'inbound-license' in compat_object['compatibility_check']:
                pref = self.policy.most_preferred(compat_object['outbound_license'], compat_object['inbound_license'], ignore_missing=True)

                lic = compat_object["inbound_license"]
                list_nr, index = self.policy.list_presence(lic, ignore_missing=ignore_missing)
                list_name = self.policy.list_nr_to_name(list_nr)
                compat_object['policy_check'].update({
                    'check_type': 'inbound',
                    'inbound_license': compat_object['inbound_license'],
                    'outbound_license': compat_object['outbound_license'],
                    'inbound_license_type': 'license',
                    'outbound_license_type': 'license',
                    'compatibility': compat_object['compatibility'],
                    'inbound_list': list_name,
                    'inbound_list_index': index,
                })
            
        else:
            raise Exception("We should not be here")
        return None

    def apply_policy(self, compat_report, ignore_missing=False):
        if not self.policy:
            logging.debug(f'apply_policy, no policy. Creating default one')
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
        meta = compat_report['meta']
        meta['policy_type'] = self.policy_type
        meta['policy_file'] = self.policy_file
        return compat_report

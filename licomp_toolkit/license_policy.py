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
        if not (lic1_list and lic2_list):
            if ignore_missing:
                print("---------------------------------------------|||1 " + str(lic1))
                print("---------------------------------------------|||1 " + str(lic2))
                print("---------------------------------------------|||1 " + str(lic1_list) + " " + str(lic1_index))
                print("---------------------------------------------|||1 " + str(lic2_list) + " " + str(lic2_index))
                print("---------------------------------------------|||1 " + str(self.allowed()))
                print("---------------------------------------------|||1 " + str(self.avoided()))
                print("---------------------------------------------|||1 " + str(self.denied()))
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
    
    def preferred_score_inbounds(self, lic1, lic2):
        print(f'preferred_score_inbounds({lic1}, {lic2})')
        pref = self.compare_preferences(lic1['inbound_license'], lic2['inbound_license'])
        if pref < 0:
            return -1
        if lic1 == lic2:
            return 0
        return 1
    
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
        #print("Liverpool: " + str(self.policy))

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
        print("resources: " + str(self.lt.licomp_resources()))
        print("resources: " + str(resources))
        for resource in resources:
            for licomp_resource in self.lt.licomp_resources():
                #print("lr:" + str(licomp_resource))
                if resource == licomp_resource:
                    #print("Found: " + str(self.lt.licomp_resources()[licomp_resource]))
                    #print("Found: " + str(self.lt.licomp_resources()[licomp_resource].supported_licenses()))
                    self.licenses += self.lt.licomp_resources()[licomp_resource].supported_licenses()
                    self.resources.append(self.lt.licomp_resources()[licomp_resource])
                    print("licenses: " + str(self.licenses))

class LicensePolicyHandler:

    def __init__(self, policy_file=None, resources=None, usecase=None, provisioning=None):
        print("PolicyHandler()")
        if policy_file:
            self.policy = LicensePolicy(policy_file)
        else:
            self.policy = DefaultLicensePolicy(resources, usecase, provisioning)

    def _usable_license(self, lic):
        print()
        print()
        print("_usable_license " + str(lic))
        print(str(lic))
        print(str(lic.keys()))
        license_name =  lic['inbound_license']
        policy_ok = license_name in (self.policy.allowed() + self.policy.avoided())
        compat_ok = lic['compatibility'] == 'yes'

        ret = policy_ok and compat_ok
        print(f'_usable_license({lic}) |  policy_ok: {policy_ok}, compat_ok: {compat_ok}  ===> {ret}')

        return ret
            
    def __scored_inbounds(self, inbounds, operator):
        if operator == "OR":
            print(f'preferred_inbounds({inbounds}, {operator})')
            filtered_inbound_licenses = [x for x in inbounds if self._usable_license(x)]
            print(f'filtered_preferred_inbounds: {filtered_inbound_licenses}')
            sorted_inbounds = sorted(filtered_inbound_licenses, key=cmp_to_key(self.policy.preferred_score_inbounds))
            print(f'sorted_inbounds: {[x["inbound_license"] for x in sorted_inbounds]})')

            return sorted_inbounds
        elif operator == "AND":
            sorted_inbounds = sorted(inbounds, key=cmp_to_key(self.policy.preferred_score_inbounds))
            return sorted_inbounds
        else:
            raise Exception("TODO fix this")
        
    def OBSOLETE__summarize_inbounds(self, inbounds, operator):
        inbound_licenses = [x['inbound_license'] for x in inbounds]
        most_license = inbound_licenses[0]
        least_license = inbound_licenses[0]
        if operator == "OR":
            for inbound_license in inbound_licenses:
                most_license = self.policy.most_preferred(most_license, inbound_license, ignore_missing=True)
                least_license = self.policy.least_preferred(least_license, inbound_license, ignore_missing=True)
        elif operator == "AND":
            for inbound_license in inbound_licenses:
                most_license = self.policy.most_preferred(most_license, inbound_license, ignore_missing=True)
                least_license = most_license
        return {
            'most_preferred_license': most_license,
            'least_preferred_license': least_license,
        }

    def __apply_to_compat_object(self, compat_object, indent=0):
        print(" " * indent + "---------------------------")
        print(" " * indent + "apply type: " + str(compat_object['compatibility_check']))
        print(" " * indent + "apply out:  " + str(compat_object['outbound_license']))
        print(" " * indent + "apply in:   " + str(compat_object['inbound_license']))
        
        if 'outbound-expression' in compat_object['compatibility_check']:
            operator = compat_object['operator']
            print(" " * indent + "* operator: " + operator)
            #print("* out: "+ str(compat_object['outbound_license']) + "  not supported right now")
            for operand in compat_object['operands']:
                print(" " * indent + "* operand:  "+ str(operand['compatibility_object']['outbound_license']))
                self.__apply_to_compat_object(operand['compatibility_object'], indent+4)
        elif 'outbound-license' in compat_object['compatibility_check']:
            if 'inbound-expression' in compat_object['compatibility_check']:
                print("keys: " + str(compat_object.keys()))
                print("il:   " + str(compat_object['inbound_license']))
                print("ol:   " + str(compat_object['outbound_license']))
                print("type: " + str(compat_object.get('compatibility_type', None)))
                #print("co:   " + str(compat_object))
                print("co:   " + str(compat_object.get('compatibility_object', None)))
                print("keys: " + str(compat_object.keys()))
                print("il:   " + str(compat_object['inbound_license']))
                print("ol:   " + str(compat_object['outbound_license']))
                print("type: " + str(compat_object.get('compatibility_type', None)))
                print("op:   " + str(compat_object.get('operator', 'noop')))
                print("cc:   " + str(compat_object.get('compatibility_check', "nocheck")))
                #                inner_compat_object = compat_object['compatibility_object']
                inner_compat_object = compat_object
                operator = inner_compat_object['operator']
                print(" " * indent + "* operator:  " + operator)
                # BASED ON OPERATOR ... sum up operands
                inbounds = []
                for operand in inner_compat_object['operands']:
                    self.__apply_to_compat_object(operand['compatibility_object'], indent+4)
                    print(" " * indent + "  * operand:  "+ str(operand['compatibility_object']['inbound_license']) + " prefs: " + str(operand['compatibility_object']['policy_check']))
                    inbounds.append(operand['compatibility_object']['policy_check'])
                scored_inbounds = self.__scored_inbounds(inbounds, operator)
                print("0 preferred: " + str(len(scored_inbounds)))
                print("1 preferred: " + str(scored_inbounds))
                
                inner_compat_object['policy_check'] = {
                    'check_type': 'inbound',
                    'inbound_license': inner_compat_object['inbound_license'],
                    'outbound_license': inner_compat_object['outbound_license'],
                    'inbound_license_type': 'license-expression',
                    'outbound_license_type': 'license',
                    'compatibility': compat_object['compatibility'],
                    'inbound_licenses': scored_inbounds,
                    'inbound_list': scored_inbounds[0]['inbound_list'],
                    'inbound_list_index': scored_inbounds[0]['inbound_list_index'],
                }
                print("policy_check: HIGH: " + str(inner_compat_object['policy_check']))
            if 'inbound-license' in compat_object['compatibility_check']:
                pref = self.policy.most_preferred(compat_object['outbound_license'], compat_object['inbound_license'], ignore_missing=True)
                print(" " * indent + f'FIX ME: {compat_object["outbound_license"]} --> {compat_object["inbound_license"]} : {compat_object["compatibility"]}  --->  {pref}')

                lic = compat_object["inbound_license"]
                list_nr, index = self.policy.list_presence(lic)
                list_name = self.policy.list_nr_to_name(list_nr)
                compat_object['policy_check'] = {
                    'check_type': 'inbound',
                    'inbound_license': compat_object['inbound_license'],
                    'outbound_license': compat_object['outbound_license'],
                    'inbound_license_type': 'license',
                    'outbound_license_type': 'license',
                    'compatibility': compat_object['compatibility'],
                    'inbound_list': list_name,
                    'inbound_list_index': index,
                }
                #print(" " * indent + str(compat_object['policy_check']))
                pass
        else:
            raise Exception("We should not be here")
        return None

    def apply_policy(self, compat_report):
        top_object = compat_report['compatibility_report']
        print("Top object:")
        print(" * out:  " + str(top_object['outbound_license']))
        print(" * in:   " + str(top_object['inbound_license']))
        print(" * type: " + str(top_object['compatibility_check']))

        
        #compat_object = top_object['compatibility_object']        
        self.__apply_to_compat_object(top_object)
        #print("compt check: " + str(compat_object['compatibility_check']))

        print(json.dumps(top_object, indent=4))
        print("done....")
        import sys
        sys.exit(1)
        return None
        

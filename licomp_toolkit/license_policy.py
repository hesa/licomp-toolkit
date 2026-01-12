# SPDX-FileCopyrightText: 2024 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later


import json

from licomp_toolkit.toolkit import LicompToolkit
from licomp.interface import UseCase
from licomp.interface import Provisioning
from licomp.interface import Modification


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

    def avoid(self):
        return self.policy['avoid']
    
    def denied(self):
        return self.policy['denied']

    def meta(self):
        return self.policy_meta


class DefaultLicensePolicy(LicensePolicy):

    def __init__(self, resources, usecase, provisioning):
        self.lt = LicompToolkit()
        self.__licenses(resources, usecase, provisioning)
        self.__order(resources, usecase, provisioning)

    def __order(self, resources, usecase, provisioning):
        self.scores = {}
        print("order...")
        for out_license in self.licenses:
            print("  order...")
            for in_license in self.licenses:
                print("    order...")
                for resource in self.resources:
                    print("       order...")
                    compat = resource.outbound_inbound_compatibility(out_license,
                                                                     in_license,
                                                                     UseCase.string_to_usecase(usecase),
                                                                     Provisioning.string_to_provisioning(provisioning),
                                                                     Modification.UNMODIFIED)
                    print(str(compat['compatibility_status']))
                    if compat['compatibility_status'] == 'yes':
                        if in_license not in self.scores:
                            self.scores[in_license] = 0
                        self.scores[in_license] += 1
                            
        print("score: " + str(self.scores))
                
        
    def __licenses(self, resources, usecase, provisioning):
        self.licenses = []
        self.resources = []
        print(str(self.lt.licomp_resources()))
        for resource in resources:
            for licomp_resource in self.lt.licomp_resources():
                print("lr:" + str(licomp_resource))
                if resource == licomp_resource:
                    print("Found: " + str(self.lt.licomp_resources()[licomp_resource]))
                    print("Found: " + str(self.lt.licomp_resources()[licomp_resource].supported_licenses()))
                    self.licenses += self.lt.licomp_resources()[licomp_resource].supported_licenses()
                    self.resources.append(self.lt.licomp_resources()[licomp_resource])

class LicensePolicyHandler:

    def __init__(self, policy_file):
        print("PolicyHandler()")
        self.policy = LicensePolicy(policy_file)

    def __apply_to_compat_object(self, compat_object, indent=0):
        print("---------------------------")
        print("apply type: " + str(compat_object['compatibility_check']))
        print("apply out:  " + str(compat_object['outbound_license']))
        print("apply in:   " + str(compat_object['inbound_license']))
        
        if 'outbound-expression' in compat_object['compatibility_check']:
            operator = compat_object['operator']
            print(operator)
            #print("* out: "+ str(compat_object['outbound_license']) + "  not supported right now")
            for operand in compat_object['operands']:
                print(" " * indent + "* operand:  "+ str(operand['compatibility_object']['outbound_license']))
                self.__apply_to_compat_object(operand['compatibility_object'], indent=4)
        elif 'outbound-license' in compat_object['compatibility_check']:
            if 'inbound-expression' in compat_object['compatibility_check']:
                inner_compat_object = compat_object['compatibility_object']
                #print("ELSE " + str(inner_compat_object))    
                for operand in inner_compat_object['operands']:
                    self.__apply_to_compat_object(operand['compatibility_object'], indent=4)
            if 'inbound-expression' in compat_object['compatibility_check']:
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

        import sys
        sys.exit(1)
        return None
        

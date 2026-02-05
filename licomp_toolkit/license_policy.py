# SPDX-FileCopyrightText: 2024 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

from collections import OrderedDict

from functools import cmp_to_key
import json
import logging

from licomp_toolkit.toolkit import LicompToolkit
from licomp_toolkit.exception import LicompToolkitException
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
        print(f'list_presence({lic}, {ignore_missing}')
        print(f'list_presence({type(lic)}, {ignore_missing}')
        
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
        print(f'compare_preferences_general({lic1}, {lic2}, {key}, {ignore_missing})')
        logging.debug(f'compare_preferences({lic1}, {lic2}, {key}, {ignore_missing})')
        print("SCHNEEBLY1 1 " + str(lic1))
        print("SCHNEEBLY1 2 " + str(lic2))
        if key:
            list_key = key.replace('_license', '')
            print("SCHNEEBLY 1.0")
            print("SCHNEEBLY KEY:      " + key)
            print("SCHNEEBLY KEY key:  " + list_key)
            print("SCHNEEBLY KEY lic:  " + str(lic1))
            print("SCHNEEBLY KEY keys: " + str(lic1.keys()))
            print("SCHNEEBLY TYPE   :  " + str(lic1[list_key]['type']))
            print("SCHNEEBLY KEY sub:  " + str(lic1[list_key]))
            print("SCHNEEBLY KEY sub:  " + str(lic1[list_key].keys()))
            if lic1[list_key]['type'] == 'license':
                print("SCHNEEBLY 1.1")
                lic1_list, lic1_index = self.list_presence(lic1[list_key]['license'], ignore_missing)
                print("SCHNEEBLY 1.1 " + str(lic1_list))
                print("SCHNEEBLY 1.1 " + str(lic1_index))
            else:
                print("SCHNEEBLY 1.2 type " + str(lic1[list_key]['type']))
                print("SCHNEEBLY 1.2 " + str(list_key))
                print("SCHNEEBLY 1.2 " + str(lic1[list_key]))
                print("SCHNEEBLY 1.2 keys " + str(lic1[list_key].keys()))
                print("SCHNEEBLY 1.2 pref " + str(lic1[list_key]['preferences']))
                print("SCHNEEBLY 1.2 lic1 " + str(lic1))
                
                lic1_list = self.list_name_to_nr(lic1[list_key]['license'])
                print("lic1: " + str(lic1))
                print("lic1: " + str(list_key))
                print("lic1: " + str(lic1[list_key]))
                lic1_index = lic1[list_key]['preferences']['license_index']
            
            if lic2[list_key]['type'] == 'license':
                print("SCHNEEBLY 2.1")
                lic2_list, lic2_index = self.list_presence(lic2[list_key]['license'], ignore_missing)
            else: # license-expression
                print("SCHNEEBLY 2.1 lic:      " + str(lic2))
                print("SCHNEEBLY 2.1 lic:      " + str(list_key))
                print("SCHNEEBLY 2.1 lic_key:  " + str(lic2[list_key]))
                print("SCHNEEBLY 2.1 pref: " + str(lic2[list_key]['preferences']))
                print("SCHNEEBLY 2.1 lic: " + str(lic2[list_key]['license']))
                
                lic2_list = lic2[list_key]['preferences']['license_list']
                lic2_index = lic2[list_key]['preferences']['license_index']
        else:
                print("SCHNEEBLY 2.2 .... should list_key be selected as above???? " + str(lic1))
                lic1_list, lic1_index = self.list_presence(lic1, ignore_missing)
                lic2_list, lic2_index = self.list_presence(lic2, ignore_missing)
            
        print(f'compare_preferences:   "{lic1_list}", "{lic1_index}" "{lic2_list}", "{lic2_index}"')
        logging.debug(f'compare_preferences:   "{lic1_list}", "{lic1_index}" "{lic2_list}", "{lic2_index}"')

        if (not lic1_list) and (not lic2_list):
            if ignore_missing:
                logging.debug(f'compare_preferences({lic1[list_key]["license"]}, {lic2[list_key]["license"]}, {ignore_missing}): ignore since both None')
                return None
            
            raise LicensePolicyException(f'License "{lic1[list_key]["license"]}" and/or {lic2[list_key]["license"]} is not present in any of the policy\'s lists.')
        
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
    
    def OBSOLETE_preferred_score_ignore_missing(self, lic1, lic2):
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
        print(f'preferred_score_licenses({lic1}, {lic2}, {key})')
        pref = self.compare_preferences_expressions(lic1, lic2, key)
        if pref < 0:
            return -1
        if lic1 == lic2:
            return 0
        return 1

    def preferred_score_inbounds(self, lic1, lic2):
        logging.debug(f'preferred_score_inbounds({lic1}, {lic2})')
        print(f'preferred_score_inbounds({lic1}, {lic2})')
        return self.preferred_score_licenses(lic1, lic2, 'inbound_license')
    
    def preferred_score_outbounds(self, lic1, lic2):
        logging.debug(f'preferred_score_outbounds({lic1}, {lic2})')
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
        print("FALCAO1 usable_license keys: " + str(lic))
        print("FALCAO usable_license keys: " + str(lic['inbound']) + "  " + str(lic.keys()))
        # TODO: fix inbound to key
        license_name =  lic['inbound']['license']
        if self.__is_license_expression(license_name):
            # should have been checked already, so skip
            policy_ok = True
        else:
            
            print(f'FALCAO +++ -2 usable_license {self.policy}')
            print(f'FALCAO +++ -1 usable_license {license_name}')
            print(f'FALCAO +++ 0 usable_license {self.policy.allowed()}')
            print(f'FALCAO +++ 0 usable_license {self.policy.avoided()}')
            print(f'FALCAO +++ 1 usable_license {license_name in self.policy.allowed()}')
            print(f'FALCAO +++ 2 usable_license {license_name in self.policy.avoided()}')
            print(f'FALCAO +++ 3 usable_license {license_name in (self.policy.allowed() + self.policy.avoided())}')
            policy_ok = license_name in (self.policy.allowed() + self.policy.avoided())
        compat_ok = lic['compatibility'] == 'yes'

        ret = policy_ok and compat_ok
        logging.debug(f'usable_license({lic}) |  policy_ok: {policy_ok}, compat_ok: {compat_ok}  ===> {ret}')
        print(f'FALCAO +++ usable_license({lic}) |  policy_ok: {policy_ok}, compat_ok: {compat_ok}  ===> {ret}')

        return ret
            
    def unusable_licenses(self, licenses, key):
        print("UG " + str(licenses))
        problematic_licenses = []
        for lic in licenses:
            print("lic: " + str(lic.keys()))
            license_name =  lic[key]['license']
            if self.__is_license_expression(license_name):
                # should have been checked already, so skip
                policy_ok = True
            else:
                policy_ok = license_name in (self.policy.allowed() + self.policy.avoided())
            compat_ok = lic['compatibility'] == 'yes'

            ret = policy_ok and compat_ok
            logging.debug(f'usable_license({lic}) |  policy_ok: {policy_ok}, compat_ok: {compat_ok}  ===> {ret}')
            if not ret:
                problematic_licenses.append(lic)
        return len(problematic_licenses) > 0
            
    def scored_general(self, licenses, operator, key):
        print(f'scored_general({licenses}, {operator}, {key})')
        compare_function = {
            'inbound': self.policy.preferred_score_inbounds,
            'outbound': self.policy.preferred_score_outbounds,
        }[key]
        print("sgo: func= " + str(compare_function))
        if operator == "OR":
            print("FALCAO sg:  9: " + str(licenses))
            logging.debug(f'preferred_licenses({licenses}, {operator})')
            filtered_licenses = [x for x in licenses if self.usable_license(x)]
            print("FALCAO sg:  9.1: " + str(filtered_licenses))
            sorted_licenses = sorted(filtered_licenses, key=cmp_to_key(compare_function))
            print("FALCAO sg:  9.2: " + str(sorted_licenses))
            logging.debug(f'sorted_licenses: {[x[key]['license'] for x in sorted_licenses]})')
            return sorted_licenses
        elif operator == "AND":
            print("FALCAO sg:  10")
            if self.unusable_licenses(licenses, 'inbound'):
                print("FALCAO sg:  10.1")
                sorted_licenses = []
            else:
                sorted_licenses = sorted(licenses, key=cmp_to_key(compare_function))
            
            return sorted_licenses
        else:
            raise Exception("TODO fix this")
        
    def scored_inbounds(self, inbounds, operator):
        print(f'scored_inbounds({inbounds}, {operator})')
        return self.scored_general(inbounds, operator, 'inbound')
        
    def scored_outbounds(self, outbounds, operator):
        return self.scored_general(outbounds, operator, 'outbound')

    def __check_policy_check(self, reply):
        keys = [
            'license',
            'type',
            'preferences:license',
            'preferences:license_list',
            'preferences:license_index'
        ]
        print("reply: " + json.dumps(reply, indent=4))
        print("reply keys: " + str(reply.keys()))
        for key in keys:
            in_value = reply['inbound']
            out_value = reply['outbound']
            for sub_key in key.split(':'):
                assert sub_key in in_value
                print(str("  sub_key " + sub_key))
                assert sub_key in out_value
                in_value = in_value[sub_key]
                out_value = out_value[sub_key]

        assert 'compatibility' in reply
        assert 'unusable' in reply

    def __pack_policy_check(self, outbound_pref, inbound_pref, compat, unusable):
        return {
            'outbound': outbound_pref,
            'inbound': inbound_pref,
            'compatibility': compat,
            'unusable': unusable,
        }

    def __pack_policy_unusable(self, unusables):
        return {
            'unusable': unusables
        }

    def __pack_policy_preferences(self, license_string, license_list, license_index):
        return {
            'license': license_tring,
            'license_list': license_list,
            'license_index': license_index
        }

    def __pack_policy_check_license(self, license_name, license_type, pref_lic, pref_lic_list, pref_lic_idx):
        return {
            'license': license_name,
            'type': license_type,
            'preferences': {
                'license': pref_lic,
                'license_list': pref_lic_list,
                'license_index': pref_lic_idx
            }
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
        print("ATC")
        if 'outbound-expression' in compat_object['compatibility_check']:
            operator = compat_object['operator']
            outbounds = []
            print("LFC: " + str(compat_object.keys()))
            for operand in compat_object['operands']:
                operand['compatibility_object']['TEST'] = "Liverpool"
                print("sgo: operand: BEGIN ")
                print("sgo: operand: BEGIN " + str(operand['compatibility_object']['outbound_license']) + " " + str(operand['compatibility_object'].keys()))
                self.__apply_to_compat_object(operand['compatibility_object'], indent+4)
                self.__check_policy_check(operand['compatibility_object']['policy_check'])
                
                outbounds.append(operand['compatibility_object']['policy_check'])

                POL=operand['compatibility_object']['policy_check']
                print("sgo: operand: WATCH " + str(operand['compatibility_object']['policy_check']['outbound']) + " " + str(operand['compatibility_object']['policy_check'].keys()))
                print("sgo: operand: KEEP " + str(POL.keys()))
                #print("sgo: operand: KEEP " + str(POL['inbound_list']) + " " + str(POL['inbound_list_index']) + " " + str(POL['preferred_inbound_license']))
                print("sgo: operand: END " + str(operand['compatibility_object']['policy_check']['outbound']) + " " + str(operand['compatibility_object']['policy_check'].keys()))
            scored_outbounds = self.scored_outbounds(outbounds, operator)
            print("sgo: operands: HERE: " + str(outbounds[0]))
            print("sgo: operands: HERE: " + str(outbounds[0].keys()))


            outbound_list = []
            outbound_list_index = -1
            preferred_inbound_license = None
            compatibility = 'no'

            print("EDER: " + operator)
            print("EDER: " + str(len(scored_outbounds)))
            if len(scored_outbounds) > 0:
                print("EDER: OUTBONDS")
                if operator == 'AND':
                    outbound_name = ' AND '.join([x['outbound']['preferences']['license'] for x in scored_outbounds])
                    outbound_pref = scored_outbounds[-1]
                else:
                    outbound_name = scored_outbounds[0]['outbound']['preferences']['license']
                    outbound_pref = scored_outbounds[0]

                print("0 --------------- " + str(len(scored_outbounds)))
                print("2 --------------- " + str(scored_outbounds[0]))
                print("2 --------------- " + str(scored_outbounds[1]))
                outbound_list = outbound_pref['outbound']['preferences']['license_list']
                outbound_list_index = outbound_pref['outbound']['preferences']['license_index']
                inbound_prefs = outbound_pref['inbound']['preferences']
                print("inbound_prefs: " + str(inbound_prefs))
                preferred_inbound_license = inbound_prefs['license']
                preferred_inbound_license_list = inbound_prefs['license_list']
                preferred_inbound_license_index = inbound_prefs['license_index']

                compatibility = 'yes'
                
            else:
                print("EDER: NO outbonds")
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
                preferred_inbound_license_index
            )
            policy_check_outbound_license = self.__pack_policy_check_license(
                compat_object['outbound_license'],
                'license-expression',                
                outbound_name,
                outbound_list,
                outbound_list_index
            )
            # TODO: add identify and pass on unusable
            unusable = self.__pack_policy_unusable([])
            policy_license_object = self.__pack_policy_check(
                policy_check_outbound_license,
                policy_check_inbound_license,
                compatibility,
                unusable)
            import json,sys
            print("OP" + json.dumps(policy_license_object, indent=4))
                
            compat_object['policy_check'] = policy_license_object


            
            #compat_object['policy_check_OLD'] = {
            dummy = {
                'outbound_license': compat_object['outbound_license'],
                'outbound_license_type': 'license-expression',
                'outbound_licenses': scored_outbounds,
                'outbound_list': outbound_list,
                'outbound_list_index': outbound_list_index,
                
                'inbound_license': compat_object['inbound_license'],
                'inbound_license_type': inbound_license_type,
                'compatibility': compatibility,
#                'inbound_licenses': None,
                'inbound_list': None,
                'inbound_list_index': None,
                'preferred_outbound_license': outbound_name,
                'preferred_outbound_license_list': outbound_list,
                'preferred_outbound_license_index': outbound_list_index,
                'preferred_inbound_license': preferred_inbound_license,
                'preferred_inbound_license_list': preferred_inbound_license_list,
                'preferred_inbound_license_index': preferred_inbound_license_index,
                'HENRIK_OP': operator,
            }
            if operator == 'AND':
                compat_object['policy_check']['HENRIK_DIX'] = 'AND'
            else:
                compat_object['policy_check']['HENRIK_DIX'] = 'NOT NOT AND : ' + operator

        elif 'outbound-license' in compat_object['compatibility_check']:

            if 'inbound-expression' in compat_object['compatibility_check']:
                inner_compat_object = compat_object
                operator = inner_compat_object['operator']
                inbounds = []
                print("ZICO inbound:  " + compat_object['inbound_license'])
                print("ZICO operator: " + operator)
                for operand in inner_compat_object['operands']:
                    self.__apply_to_compat_object(operand['compatibility_object'], indent+4)
                    import json, sys
                    print(json.dumps(operand['compatibility_object']['policy_check'], indent=4))
                    print("    FALCAO operand " + str(operand['compatibility_object']['policy_check']))
                    #assert False
                    #sys.exit(1)
                    self.__check_policy_check(operand['compatibility_object']['policy_check'])
                    inbounds.append(operand['compatibility_object']['policy_check'])
                    print("ZICO operand: " + operand['compatibility_object']['inbound_license'])

                import json, sys
                print("FALCAO operands " + str(inbounds))
                scored_inbounds = self.scored_inbounds(inbounds, operator)
                print("FALCAO scored inbounds " + str(scored_inbounds))
                inbound_list = []
                inbound_list_index = -1
                preferred_inbound_license = None

                print("FALCAO inner:  " + str(inbounds))
                print("FALCAO scored: " + str(scored_inbounds))
                print("FALCAO oper:   " + str(operator))
#                sys.exit(1)
                if len(scored_inbounds) > 0:
                    print("REICH: " + str(scored_inbounds[0]))
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

                print("ZICO: " + str(compat_object['compatibility_check']) + ": " + str(len(scored_inbounds)))
                print("ZICO: " + str(compat_object['compatibility_check']) + ": " + str(preferred_inbound_license))
                print("ZICO: " + str(compat_object['compatibility_check']) + ": " + json.dumps(scored_inbounds, indent=4))
                print("ZICO: " + str(compat_object['compatibility_check']) + ": " + operator)
                print("ZICO: " + str(compat_object['compatibility_check']) + ": " + str(preferred_inbound_license))
#                sys.exit(1)
                if len(scored_inbounds) == 1:
                    #sys.exit(1)
                    pass
                out_lic = inner_compat_object["outbound_license"]
                out_list_nr, out_index = self.policy.list_presence(out_lic, ignore_missing=ignore_missing)
                out_list_name = self.policy.list_nr_to_name(out_list_nr)

                
                print("FALCAO inner: " + json.dumps(preferred_inbound_license, indent=4))
                policy_check_inbound_license = self.__pack_policy_check_license(
                    inner_compat_object['inbound_license'],
                    'license-expression',                
                    preferred_inbound_license,
                    inbound_list,
                    inbound_list_index
                )
                policy_check_outbound_license = self.__pack_policy_check_license(
                    out_lic,
                    'license',                
                    out_lic,
                    out_list_name,
                    out_index
                )
                # TODO: add identify and pass on unusable
                unusable = self.__pack_policy_unusable([])
                policy_license_object = self.__pack_policy_check(
                    policy_check_outbound_license,
                    policy_check_inbound_license,
                    compat_object['compatibility'],
                    unusable)
                inner_compat_object['policy_check'] = policy_license_object
                
                print("FALCAO: " + json.dumps(inner_compat_object['policy_check'], indent=4))
                print("FALCAO done")
#                sys.exit(1)
                      
                
                
#                inner_compat_object['policy_check_TMP'] = {
                dummy = {
                    'inbound_license': inner_compat_object['inbound_license'],
                    'outbound_license': inner_compat_object['outbound_license'],
                    'inbound_license_type': 'license-expression',
                    'outbound_license_type': 'license',
                    'compatibility': compat_object['compatibility'],
#                    'inbound_licenses': scored_inbounds,
                    'inbound_list': inbound_list,
                    'inbound_list_index': inbound_list_index,
                    'outbound_list': out_list_name,
                    'outbound_list_index': out_index,
                    'preferred_inbound_license': preferred_inbound_license,
                    'preferred_outbound_license': inner_compat_object['outbound_license'],
                }
            if 'inbound-license' in compat_object['compatibility_check']:
                #pref = self.policy.most_preferred(compat_object['outbound_license'], compat_object['inbound_license'], ignore_missing=True)

                out_lic = compat_object["outbound_license"]
                out_list_nr, out_index = self.policy.list_presence(out_lic, ignore_missing=ignore_missing)
                out_list_name = self.policy.list_nr_to_name(out_list_nr)
                
                in_lic = compat_object['inbound_license']
                in_list_nr, in_list_index = self.policy.list_presence(in_lic, ignore_missing=ignore_missing)
                in_list_name = self.policy.list_nr_to_name(in_list_nr)
                out_lic = compat_object["outbound_license"]
                out_list_nr, out_index = self.policy.list_presence(out_lic, ignore_missing=ignore_missing)
                out_list_name = self.policy.list_nr_to_name(out_list_nr)
                # TODO: fill in the below

                policy_check_inbound_license = self.__pack_policy_check_license(
                    in_lic,
                    'license',                
                    in_lic,
                    in_list_name,
                    in_list_index
                )
                policy_check_outbound_license = self.__pack_policy_check_license(
                    out_lic,
                    'license',                
                    out_lic,
                    out_list_name,
                    out_index,
                )
                # TODO: add identify and pass on unusable
                unusable = self.__pack_policy_unusable([])
                policy_license_object = self.__pack_policy_check(
                    policy_check_outbound_license,
                    policy_check_inbound_license,
                    compat_object['compatibility'],
                    unusable)
                compat_object['policy_check'] = policy_license_object
                # TODO: REMOVE
                if False:
                    compat_object['policy_check_TMP'] = {
                        'inbound_license': in_lic,
                        'outbound_license': out_lic,
                        'inbound_license_type': 'license',
                        'outbound_license_type': 'license',
                        'compatibility': compat_object['compatibility'],
                        'inbound_list': list_name,
                        'inbound_list_index': index,
                        'outbound_list': out_list_name,
                        'outbound_list_index': out_index,
                        'preferred_inbound_license': lic,
                        "HESA": "LIVEROPOPOL",
                    }
                    print("sgo: operand   outbound license: " + str(compat_object.keys()))
                #print("sgo: operand: ---> " + str(compat_object['policy_check']['outbound_license']) + " <--- " + str(compat_object['policy_check']['outbound_list'] + "   keys: " + str(compat_object['policy_check'].keys())))
            
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
        self.__check_policy_check(top_object['policy_check'])
        meta = compat_report['meta']
        meta['policy_type'] = self.policy_type
        meta['policy_file'] = self.policy_file
        return compat_report

# SPDX-FileCopyrightText: 2024 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

import importlib
import json
import logging

from licomp.interface import Licomp
from licomp.interface import UseCase
from licomp.interface import Provisioning
from licomp.interface import LicompException

from licomp_osadl.osadl import LicompOsadl
from licomp_reclicense.reclicense import LicompReclicense
from licomp_proprietary.proprietary import LicompProprietary
from licomp_dwheeler.dwheeler import LicompDw
from licomp_hermione.hermione import LicompHermione

from licomp_toolkit.config import disclaimer

class LicompToolkitFormatter():

    @staticmethod
    def formatter(fmt):
        if fmt.lower() == 'json':
            return JsonLicompToolkitFormatter()

    def format_compatibilities(self, compat):
        return None

class JsonLicompToolkitFormatter():

    def format_compatibilities(self, compat):
        return json.dumps(compat, indent=4)

class LicompToolkit(Licomp):

    def __init__(self):
        self.LICOMP_MODULES = {}
        self.LICOMP_MODULE_NAMES = {
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

    def __add_to_list(self, store, data, name):
        if not data:
            return
        if data not in store:
            store[data] = []
        store[data].append(name)

    def __add_meta(self, compatibilities):
        compatibilities["meta"] = {}
        compatibilities["meta"]['disclaimer'] = disclaimer

    def licomp_modules(self):
        if not self.LICOMP_MODULES:
            for licomp in [LicompReclicense, LicompOsadl, LicompHermione, LicompProprietary, LicompDw]: # , LicompDw
                licomp_instance = licomp()
                self.LICOMP_MODULES[licomp_instance.name()] = licomp_instance
        return self.LICOMP_MODULES

    def __summarize_compatibility(self, compatibilities, outbound, inbound, usecase, provisioning):
        compatibilities["summary"] = {}
        statuses = {}
        compats = {}
        compatibilities['nr_licomp'] = len(self.licomp_modules())
        for module_name in self.licomp_modules():
            compat = compatibilities["compatibilities"][module_name]
            logging.debug(f': {compat["resource_name"]}')
            self.__add_to_list(statuses, compat['status'], compat['resource_name'])
            self.__add_to_list(compats, compat['compatibility_status'], compat['resource_name'])
        compatibilities["summary"]["resources"] = [f'{x.name()}:{x.version()}' for x in self.licomp_modules().values()]
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
    def outbound_inbound_compatibility(self, outbound, inbound, usecase, provisioning):

        logging.debug(f'{inbound} {outbound} ')
        try:
            usecase = UseCase.string_to_usecase(usecase)
            provisioning = Provisioning.string_to_provisioning(provisioning)
        except KeyError:
            raise LicompException(f'Provisioning {provisioning} not supported.')
        compatibilities = {}
        compatibilities['compatibilities'] = {}

        for module_name in self.licomp_modules():
            module = self.licomp_modules()[module_name]
            logging.debug(f'-- module: {module.name()}')
            compat = module.outbound_inbound_compatibility(outbound, inbound, usecase, provisioning=provisioning)
            compatibilities['compatibilities'][compat['resource_name']] = compat

        self.__summarize_compatibility(compatibilities, outbound, inbound, usecase, provisioning)
        self.__add_meta(compatibilities)

        return compatibilities

    def supported_licenses(self):
        licenses = set()
        for module in self.licomp_modules().values():
            licenses.update(set(module.supported_licenses()))
        licenses = list(licenses)
        licenses.sort()
        return licenses

    def supported_provisionings(self):
        provisionings = set()
        for module in self.licomp_modules().values():
            provisionings.update(set(module.supported_provisionings()))
        return list(provisionings)

    def supported_usecases(self):
        usecases = set()
        for module in self.licomp_modules().values():
            usecases.update(set(module.supported_usecases()))
        return list(usecases)

    def disclaimer(self):
        return disclaimer

def __class_instance(package, class_name):
    licomp_module = importlib.import_module(f'{package}')
    licomp_class = getattr(licomp_module, class_name)
    return licomp_class()

def __check_api_version(subclass):
    licomp_api_version = Licomp.api_version()
    subclass_api_version = subclass.supported_api_version()
    logging.debug(f'{licomp_api_version} == {subclass_api_version} ???')

    licomp_api_version_major = licomp_api_version.split('.')[0]
    licomp_api_version_minor = licomp_api_version.split('.')[1]

    subclass_api_version_major = subclass_api_version.split('.')[0]
    subclass_api_version_minor = subclass_api_version.split('.')[1]
    assert licomp_api_version_major == subclass_api_version_major # noqa: S101
    assert licomp_api_version_minor == subclass_api_version_minor # noqa: S101

def _inc_map(_map, _name):
    curr = _map.get(_name, 0)
    new = curr + 1
    _map[_name] = new
    return _map

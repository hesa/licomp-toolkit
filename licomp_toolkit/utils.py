# SPDX-FileCopyrightText: 2025 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

import importlib
import logging

from licomp.interface import Licomp
from licomp_toolkit.toolkit import LicompToolkit
from licomp.return_codes import compatibility_status_to_returncode
from licomp.return_codes import ReturnCodes

def licomp_results_to_return_code(licomp_results):
    nr_results = len(licomp_results) - 1 # -1 since 'nr_valid' included in the results

    if nr_results == 0:
        return ReturnCodes.LICOMP_UNSUPPORTED_LICENSE.value

    if nr_results != 1:
        return ReturnCodes.LICOMP_INCONSISTENCY.value

    # we only have on result (apart from 'nr_valid')
    for result in licomp_results:
        if result == 'nr_valid':
            continue
        return compatibility_status_to_returncode(result)

    return ReturnCodes.LICOMP_INTERNAL_ERROR.value

def __class_instance(package, class_name):
    licomp_resource = importlib.import_resource(f'{package}')
    licomp_class = getattr(licomp_resource, class_name)
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

def resource_avilable(resource, licomp_toolkit):
    return resource in licomp_toolkit.licomp_resources().keys()

def resources_to_use(args):
    lt = LicompToolkit()
    resources = args.resources
    new_resources = []
    unsupported = []
    if args.resources == ['all']:
        new_resources = list(lt.licomp_resources().keys())
        return new_resources, []
    for resource in resources:
        if 'licomp' not in resource:
            resource = f'licomp_{resource}'
        else:
            resource = resource.replace('-', '_')

        if not resource_avilable(resource, lt):
            unsupported.append(resource)
        else:
            new_resources.append(resource)
    return new_resources, unsupported

#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: net_system
version_added: "2.4"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
short_description: Manage the system attributes on network devices
description:
  - This module provides declarative management of node system attributes
    on network devices.  It provides an option to configure host system
    parameters or remove those parameters from the device active
    configuration.
options:
  hostname:
    description:
      - Configure the device hostname parameter. This option takes an ASCII string value.
  domain_name:
    description:
      - Configure the IP domain name
        on the remote device to the provided value. Value
        should be in the dotted name form and will be
        appended to the C(hostname) to create a fully-qualified
        domain name.
  domain_search:
    description:
      - Provides the list of domain suffixes to
        append to the hostname for the purpose of doing name resolution.
        This argument accepts a list of names and will be reconciled
        with the current active configuration on the running node.
  lookup_source:
    description:
      - Provides one or more source
        interfaces to use for performing DNS lookups.  The interface
        provided in C(lookup_source) must be a valid interface configured
        on the device.
  name_servers:
    description:
      - List of DNS name servers by IP address to use to perform name resolution
        lookups.  This argument accepts either a list of DNS servers See
        examples.
  state:
    description:
      - State of the configuration
        values in the device's current active configuration.  When set
        to I(present), the values should be configured in the device active
        configuration and when set to I(absent) the values should not be
        in the device active configuration
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: configure system config object properties
  ansible.network.system:
    config:
      hostname: localhost
      domain_name: example.com
    operation: merge

- name: remove the system config object from the device
  ansible.network.system:
    operation: delete

- name: replace the curent system config properties
  ansible.network.system:
    config:
      domain_search:
        - ansible.com
        - redhat.com
    operation: replace
"""

RETURN = """
config:
  description: Returns the configuration object from the target device
  returned: always
  type: dict
  sample:
    hostname: localhost
    domain_name: example.com
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - hostname ios01
    - ip domain name test.example.com
"""
from ansible.module_utils.network.common.module import NetworkConfigModule
from ansible.module_utils.network.resources.dns import module_config
from ansible.module_utils.network.eos.providers.cli.config import dns


def main():
    """main entry point for module execution
    """

    module = NetworkConfigModule(module_config)
    return module.exit_json(**module.run())


if __name__ == '__main__':
    main()

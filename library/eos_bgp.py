#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: ios_bgp
version_added: "2.7"
author: "Peter Sprygada (@privateip)"
short_description: Configure global BGP protocol settings on Cisco IOS
description:
  - This module provides configuration management of global BGP parameters
    on devices running Cisco IOS.
notes:
  - Tested against IOS 4.15
options:
  bgp_as:
    description:
      - Specifies the BGP Autonomous System number to configure on the device
    type: int
    required: true
  router_id:
    description:
      - Configures the BGP routing process router-id value
    default: null
  maximum_paths:
    description:
      - Configures the maximum equal cost paths to install
    type: int
    default: null
  state:
    description:
      - Specifies the state of the BGP process configured  on the device
    default: present
    choices:
      - present
      - absent
"""

EXAMPLES = """
- name: configure global bgp as 65000
  ios_bgp:
    bgp_as: 65000
    router_id: 1.1.1.1
    state: present

- name: remove bgp as 65000 from config
  ios_bgp:
    bgp_as: 65000
    state: absent
"""

RETURN = """
"""
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.arista_eos.config.bgp.process import BgpProcess


def main():
    """ main entry point for module execution
    """
    module = AnsibleModule(argument_spec=BgpProcess.argument_spec,
                           supports_check_mode=True)

    connection = Connection(module._socket_path)
    config = connection.get('show running-config | section router bgp')

    result = {'changed': False}
    commands = list()

    match = re.search('^router bgp (\d+)', config, re.M)
    bgp_as = int(match.group(1)) if match else None

    if all((module.params['bgp_as'] is None, bgp_as is None)):
        module.fail_json(msg='missing required argument: bgp_as')
    elif module.params['bgp_as'] is None and bgp_as:
        module.params['bgp_as'] = bgp_as

    process = BgpProcess(**module.params)

    resp = process.render(config)
    if resp:
        commands.extend(resp)

    if commands:
        if not module.check_mode:
            connection.edit_config(commands)
        result['changed'] = True

    result['commands'] = commands

    module.exit_json(**result)

if __name__ == '__main__':
    main()

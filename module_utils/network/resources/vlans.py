#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


config_spec = {
    'vlan_id': dict(type='int', required=True),
    'name': dict(),
    'status': dict(choices=['active', 'suspend'])
}


argument_spec = {
    'config': dict(type='list', elements='dict', options=config_spec),
    'operation': dict(default='merge', choices=['merge', 'replace', 'delete', 'override'])
}


required_if = [
    ('state', 'merge', ['config']),
    ('state', 'replace', ['config'])
]


module_config = {
    'argument_spec': argument_spec,
    'required_if': required_if
}

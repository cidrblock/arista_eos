#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


network_spec = {
    'network': dict(required=True),
    'area': dict(required=True)
}


config_spec = {
    'process_id': dict(type='int', required=True),
    'router_id': dict(),
    'networks': dict(type='list', elements='dict', options=network_spec),
    'tags': dict(type='list')
}


argument_spec = {
    'config': dict(type='dict', elements='dict', options=config_spec),
    'operation': dict(default='merge', choices=['merge', 'replace', 'delete'])
}


required_if = [
    ('state', 'merge', ['config']),
    ('state', 'replace', ['config'])
]

module_config = {
    'argument_spec': argument_spec,
    'required_if': required_if
}

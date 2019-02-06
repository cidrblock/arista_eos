#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


config_spec = {
    'name': dict(required=True),
    'enabled': dict(type='bool'),
    'description': dict()
}


argument_spec = {
    'config': dict(type='list', elements='dict', options=config_spec),
    'operation': dict(default='merge', choices=['merge', 'replace', 'delete', 'override'])
}


required_if = [
    ('state', 'merge', ['config']),
    ('state', 'replace', ['config']),
    ('state', 'override', ['config'])
]


module_config = {
    'argument_spec': argument_spec,
    'required_if': required_if
}

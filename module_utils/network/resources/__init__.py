#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from collections import MutableMapping

from ansible.module_utils.network.common.utils import dict_merge

class ModuleConfig(MutableMapping):

    def __init__(self, **kwargs):
        self.items = {'supports_check_mode': True}
        self.items.update(kwargs)

    def __getitem__(self, key):
        return self.items[key]

    def __setitem__(self, key, value):
        self.items[key] = value

    def __delitem__(self, key):
        del self.items[key]

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)

    def serialize(self):
        return self.items

    def extend(self, obj):
        assert isinstance(obj, dict)
        self.items['argument_spec'] = dict_merge(self.items['argument_spec'], obj)



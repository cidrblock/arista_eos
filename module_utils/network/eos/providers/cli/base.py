from ansible.module_utils._text  import to_text

from ansible.module_utils.network.common.providers import CliProvider
from ansible.module_utils.network.common.providers import ProviderError


class EosCliProvider(CliProvider):

    def cli(self, command):
        resp = super(EosCliProvider, self).cli(command)
        if 'errors' in resp:
            message = '\n'.join(resp['errors'])
            raise ProviderError(message, command=command)
        return resp

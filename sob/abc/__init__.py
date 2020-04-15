from typing import List

from . import version
from . import types
from . import properties
from . import model
from . import meta

__all__: List[str] = ['model', 'properties', 'meta', 'types', 'version']

# For the backwards-compatibility of `oapi` generated modules
setattr(properties, 'types', types)

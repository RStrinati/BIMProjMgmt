# Constants package
from . import schema

# Create a schema object for easy access
class Schema:
    pass

# Import all classes from schema module
import sys
schema_module = sys.modules['constants.schema']
for name in dir(schema_module):
    if not name.startswith('_'):
        obj = getattr(schema_module, name)
        if hasattr(obj, 'TABLE'):  # It's a table class
            setattr(Schema, name, obj)

schema = Schema()
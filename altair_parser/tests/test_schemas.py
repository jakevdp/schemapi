"""Test ability to wrap schemas in the altair_parser/schemas directory"""

import os
import pytest
import json

import jsonschema
from jsonschema._utils import load_schema

from .. import JSONSchema
from ..utils import load_dynamic_module


SCHEMA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                          '..', 'schemas'))
LOADED_SCHEMAS = {filename: json.load(open(os.path.join(SCHEMA_DIR, filename)))
                  for filename in os.listdir(SCHEMA_DIR)}


@pytest.mark.parametrize('schema', LOADED_SCHEMAS)
def test_schema_jsonschema(schema):
    """Sanity check: test that the schema is a valid jsonschema"""
    schema = LOADED_SCHEMAS[schema]
    metaschema = load_schema('draft4')
    jsonschema.validate(schema, metaschema)


@pytest.mark.parametrize('schema', LOADED_SCHEMAS)
def test_parse_schema(schema):
    if schema == 'vega-lite-v2.0.0.json':
        pytest.xfail("Code currently fails for Vega-Lite due to raw $ref")
    schema = LOADED_SCHEMAS[schema]
    modulename = '_schema'
    traitlets_obj = JSONSchema(schema, module=modulename)
    load_dynamic_module(modulename, traitlets_obj.source_tree(),
                        reload_module=True)
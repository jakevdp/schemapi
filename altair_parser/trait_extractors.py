"""Extractors for trait codes"""
from .utils import construct_function_call, Variable


class TraitCodeExtractor(object):
    """Base class for trait code extractors.

    An ordered list of these is passed to JSONSchema, and they are used to
    extract appropriate trait codes.
    """
    def __init__(self, schema, typecode=None):
        self.schema = schema
        self.typecode = typecode or schema.type

    def check(self):
        raise NotImplementedError()

    def trait_code(self, **kwargs):
        raise NotImplementedError()


class SimpleTraitCode(TraitCodeExtractor):
    simple_types = ["boolean", "null", "number", "integer", "string"]
    classes = {'boolean': 'jst.JSONBoolean',
               'null': 'jst.JSONNull',
               'number': 'jst.JSONNumber',
               'integer': 'jst.JSONInteger',
               'string': 'jst.JSONString'}
    validation_keys = {'number': ['minimum', 'exclusiveMinimum',
                                  'maximum', 'exclusiveMaximum',
                                  'multipleOf'],
                       'integer': ['minimum', 'exclusiveMinimum',
                                   'maximum', 'exclusiveMaximum',
                                   'multipleOf']}

    def check(self):
        return self.typecode in self.simple_types

    def trait_code(self, **kwargs):
        cls = self.classes[self.typecode]
        keys = self.validation_keys.get(self.typecode, [])
        kwargs.update({key: self.schema[key] for key in keys
                       if key in self.schema})
        return construct_function_call(cls, **kwargs)


class CompoundTraitCode(TraitCodeExtractor):
    simple_types = SimpleTraitCode.simple_types

    def check(self):
        return (all(typ in self.simple_types for typ in self.typecode) and
                isinstance(self.typecode, list))

    def trait_code(self, **kwargs):
        if 'null' in self.typecode:
            kwargs['allow_none'] = True
        typecode = [typ for typ in self.typecode if typ != 'null']

        if len(typecode) == 1:
            return SimpleTraitCode(self.schema,
                                   typecode[0]).trait_code(**kwargs)
        else:
            item_kwargs = {key: val for key, val in kwargs.items()
                           if key not in ['allow_none', 'allow_undefined']}
            arg = "[{0}]".format(', '.join(SimpleTraitCode(self.schema, typ).trait_code(**item_kwargs)
                                           for typ in typecode))
            return construct_function_call('jst.JSONUnion', Variable(arg),
                                           **kwargs)


class RefTraitCode(TraitCodeExtractor):
    def check(self):
        return '$ref' in self.schema

    def trait_code(self, **kwargs):
        ref = self.schema.get_reference(self.schema['$ref'])
        if ref.is_object:
            return construct_function_call('jst.JSONInstance',
                                           Variable(ref.classname),
                                           **kwargs)
        else:
            ref = ref.copy()  # TODO: maybe can remove this?
            ref.metadata = self.schema.metadata
            return ref.trait_code


class EnumTraitCode(TraitCodeExtractor):
    def check(self):
        return 'enum' in self.schema

    def trait_code(self, **kwargs):
        return construct_function_call('jst.JSONEnum',
                                       self.schema["enum"],
                                       **kwargs)


class ArrayTraitCode(TraitCodeExtractor):
    def check(self):
        return self.schema.type == 'array'

    def trait_code(self, **kwargs):
        # TODO: implement items as list and additionalItems
        items = self.schema['items']
        if 'minItems' in self.schema:
            kwargs['minlen'] = self.schema['minItems']
        if 'maxItems' in self.schema:
            kwargs['maxlen'] = self.schema['maxItems']
        if 'uniqueItems' in self.schema:
            kwargs['uniqueItems'] = self.schema['uniqueItems']
        if isinstance(items, list):
            raise NotImplementedError("'items' keyword as list")
        else:
            itemtype = self.schema.make_child(items).trait_code
        return construct_function_call('jst.JSONArray', Variable(itemtype),
                                       **kwargs)


class AnyOfTraitCode(TraitCodeExtractor):
    def check(self):
        return 'anyOf' in self.schema

    def trait_code(self, **kwargs):
        children = [Variable(self.schema.make_child(sub_schema).trait_code)
                    for sub_schema in self.schema['anyOf']]
        return construct_function_call('jst.JSONAnyOf', Variable(children),
                                       **kwargs)


class OneOfTraitCode(TraitCodeExtractor):
    def check(self):
        return 'oneOf' in self.schema

    def trait_code(self, **kwargs):
        children = [Variable(self.schema.make_child(sub_schema).trait_code)
                    for sub_schema in self.schema['oneOf']]
        return construct_function_call('jst.JSONOneOf', Variable(children),
                                       **kwargs)


class AllOfTraitCode(TraitCodeExtractor):
    def check(self):
        return 'allOf' in self.schema

    def trait_code(self, **kwargs):
        children = [Variable(self.schema.make_child(sub_schema).trait_code)
                    for sub_schema in self.schema['allOf']]
        return construct_function_call('jst.JSONAllOf', Variable(children),
                                       **kwargs)


class NotTraitCode(TraitCodeExtractor):
    def check(self):
        return 'not' in self.schema

    def trait_code(self, **kwargs):
        not_this = self.schema.make_child(self.schema['not']).trait_code
        return construct_function_call('jst.JSONNot', Variable(not_this),
                                       **kwargs)


class ObjectTraitCode(TraitCodeExtractor):
    def check(self):
        return self.typecode == 'object'

    def trait_code(self, **kwargs):
        raise NotImplementedError("Anonymous Objects")
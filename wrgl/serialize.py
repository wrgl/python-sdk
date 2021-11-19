import json
import re


def to_camel_case(s):
    components = s.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


word_break_pattern = re.compile(r'([a-z])([A-Z])')


def to_snake_case(s):
    return word_break_pattern.sub(r'\1_\2', s).lower()


class _JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Serializable):
            return {
                to_camel_case(k): v
                for k, v in obj.__dict__.items()
            }
        return super().default(obj)


class Serializable(object):
    fields = dict()

    def __init__(self, **kwargs) -> None:
        super().__init__()
        for k, v in kwargs.items():
            if k not in self.__class__.fields:
                raise ValueError('unrecognized keyword argument "%s"' % k)
            cls = self.__class__.fields[k]
            if type(cls) is list:
                el_cls = cls[0]
                if type(v) is not list:
                    raise TypeError(
                        'keyword argument "%s" should be a list of %s' % (k, el_cls))
                for i, e in enumerate(v):
                    if not isinstance(e, el_cls):
                        raise TypeError(
                            'keyword argument "%s"[%d] should be of type %s' % (k, i, el_cls))
            elif type(cls) is set:
                for el_cls in cls:
                    break
                if type(v) is not dict:
                    raise TypeError(
                        'keyword argument "%s" should be a dict of %s' % (
                            k, el_cls)
                    )
                for e_k, e in v.items():
                    if not isinstance(e, el_cls):
                        raise TypeError(
                            'keyword argument "%s"[%s] should be of type %s' % (
                                k, e_k, el_cls)
                        )
            elif not isinstance(v, cls):
                raise TypeError(
                    'keyword argument "%s" should be of type %s' % (k, cls))
            setattr(self, k, v)

    def __repr__(self):
        return '<%s: %s>' % (
            self.__class__.__name__,
            ', '.join([
                '%s=%s' % (k, v if type(v) is not str else '"%s"' % v)
                for k, v in self.__dict__.items()
            ]),
        )

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        for k, v in self.__dict__.items():
            if not hasattr(other, k) or getattr(other, k) != v:
                return False
        for k, v in other.__dict__.items():
            if not hasattr(self, k):
                return False
        return True


def json_dumps(obj, skipkeys=False, ensure_ascii=True, check_circular=True, allow_nan=True, indent=None, separators=None, default=None, sort_keys=False, **kwargs):
    return json.dumps(
        obj, skipkeys=skipkeys, ensure_ascii=ensure_ascii, check_circular=check_circular, allow_nan=allow_nan,
        cls=_JSONEncoder, indent=indent, separators=separators, default=default, sort_keys=sort_keys, **kwargs
    )


def json_loads(s, serializer_cls):
    data = json.loads(s)
    return _deserialize(data, serializer_cls)


def _deserialize(data, serializer_cls):
    kwargs = dict()
    if not issubclass(serializer_cls, Serializable):
        raise TypeError('can only serialize into sub-class of Serializable')
    data = [
        (to_snake_case(k), v) for k, v in data.items()
    ]
    data_stack = [
        (kwargs, k, serializer_cls.fields[k], v)
        for k, v in data
    ]
    while len(data_stack) > 0:
        parent, name, cls, value = data_stack.pop()
        if not issubclass(serializer_cls, Serializable):
            raise TypeError('class %s is not sub-class of Serializable' % cls)
        if type(cls) is list:
            el_cls = cls[0]
            if type(value) is not list:
                raise TypeError(
                    'keyword argument "%s" should be a list of %s' % (name, el_cls))
            parent[name] = [
                _deserialize(e, el_cls) for e in value
            ]
        elif type(cls) is set:
            for el_cls in cls:
                break
            if type(value) is not dict:
                raise TypeError(
                    'keyword argument "%s" should be a dict of %s' % (
                        name, el_cls)
                )
            parent[name] = {
                k: _deserialize(e, el_cls) for k, e in value.items()
            }
        elif type(value) is dict:
            parent[name] = _deserialize(value, cls)
        else:
            parent[name] = value
    return serializer_cls(**kwargs)

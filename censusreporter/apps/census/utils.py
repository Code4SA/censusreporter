from __future__ import division

from django.utils import simplejson
from django.utils.functional import Promise
from django.utils.encoding import force_unicode


def get_object_or_none(klass, *args, **kwargs):
    try:
        return klass._default_manager.get(*args, **kwargs)
    except klass.DoesNotExist:
        return None

class LazyEncoder(simplejson.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_unicode(obj)
        return obj

## A little generator to pluck out max values ##
def drill(item):
    if isinstance(item, int) or isinstance(item, float):
        yield item
    elif isinstance(item, list):
        for i in item:
            for result in drill(i):
                yield result
    elif isinstance(item, dict):
        for k,v in item.items():
            for result in drill(v):
                yield result

def get_max_value(nested_dicts):
    max_value = max([item for item in drill(nested_dicts)])
    return max_value

def get_ratio(num1, num2, precision=2):
    '''requires ints or int-like strings'''
    if num1 and num2:
        return round(round(float(num1) / float(num2), precision)*100, 1) or None
    return None

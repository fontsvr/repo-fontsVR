def try_int(string, base=None, fallback=0):
    '''helper to parse int from string without erroring on empty or misformed string'''
    try:
        return int(string, base) if base else int(string)
    except Exception:
        return fallback


def try_float(string):
    '''helper to parse float from string without erroring on empty or misformed string'''
    try:
        return float(string or 0)
    except Exception:
        return 0


def try_str(value):
    '''helper to stringify value'''
    try:
        return f'{value}'
    except Exception:
        return ''


def try_type(value, output=None):
    if output == int:
        return try_int(value)
    if output == str:
        return try_str(value)
    if output == float:
        return try_float(value)


def partition_list(iterable, pred):
    """Use a predicate to partition entries into false entries and true entries
    partition(range(10), is_odd) --> 0 2 4 6 8   and  1 3 5 7 9
    """
    from itertools import tee, filterfalse
    t1, t2 = tee(iterable)
    return filterfalse(pred, t1), filter(pred, t2)


def parse_paramstring(paramstring):
    """ helper to assist to standardise urllib parsing """
    from urllib.parse import unquote_plus
    from unicodedata import normalize
    params = dict()
    paramstring = paramstring.replace('&amp;', '&')  # Just in case xml string
    for param in paramstring.split('&'):
        if '=' not in param:
            continue
        k, v = param.split('=')
        params[unquote_plus(k)] = normalize('NFKD', unquote_plus(v)).strip('\'').strip('"')  # Normalize and decompose combined utf-8 forms such as Arabic and strip out quotes
    return params


def get_between_strings(string, startswith='', endswith=''):
    import re
    exp = startswith + '(.+?)' + endswith
    try:
        return re.search(exp, string).group(1)
    except AttributeError:
        return ''


def reconfigure_legacy_params(**kwargs):
    if 'type' in kwargs:
        kwargs['tmdb_type'] = kwargs.pop('type')
    if kwargs.get('tmdb_type') in ['season', 'episode']:
        kwargs['tmdb_type'] = 'tv'
    return kwargs


def dict_to_list(items, key):
    items = items or []
    return [i[key] for i in items if i.get(key)]


def merge_two_dicts(x, y, reverse=False, deep=False):
    xx = y or {} if reverse else x or {}
    yy = x or {} if reverse else y or {}
    z = xx.copy()  # start with x's keys and values
    if not deep:   # modifies z with y's keys and values
        z.update(yy)
        return z
    for k, v in yy.items():
        if isinstance(v, dict):
            merge_two_dicts(z.setdefault(k, {}), v, reverse=reverse, deep=True)
        elif v:
            z[k] = v
    return z


def merge_dicts(org, upd, skipempty=False):
    source = org.copy()
    for k, v in upd.items():
        if not k:
            continue
        if skipempty and not v:
            continue
        if isinstance(v, dict):
            if not isinstance(source.get(k), dict):
                source[k] = {}
            source[k] = merge_dicts(source.get(k), v, skipempty=skipempty)
            continue
        source[k] = v
    return source


def merge_two_items(base_item, item):
    item = item or {}
    base_item = base_item or {}
    item['stream_details'] = merge_two_dicts(base_item.get('stream_details', {}), item.get('stream_details', {}))
    item['params'] = merge_two_dicts(base_item.get('params', {}), item.get('params', {}))
    item['infolabels'] = merge_two_dicts(base_item.get('infolabels', {}), item.get('infolabels', {}))
    item['infoproperties'] = merge_two_dicts(base_item.get('infoproperties', {}), item.get('infoproperties', {}))
    item['art'] = merge_two_dicts(base_item.get('art', {}), item.get('art', {}))
    item['unique_ids'] = merge_two_dicts(base_item.get('unique_ids', {}), item.get('unique_ids', {}))
    item['cast'] = item.get('cast') or base_item.get('cast') or []
    return item


def del_empty_keys(d, values=[]):
    values += [None, '']
    return {k: v for k, v in d.items() if v not in values}


def find_dict_in_list(list_of_dicts, key, value):
    """ Returns list of indexes for list of dictionaries where d.get(key) == value """
    return [list_index for list_index, dic in enumerate(list_of_dicts) if dic.get(key) == value]


def find_dict_list_index(list_of_dicts, key, value, default=None):
    """ Returns first index for list of dictionaries where d.get(ket) == value """
    return next((list_index for list_index, dic in enumerate(list_of_dicts) if dic[key] == value), default)


def get_params(item, tmdb_type, tmdb_id=None, params=None, definition=None, base_tmdb_type=None, iso_country=None):
    params = params or {}
    tmdb_id = tmdb_id or item.get('id')
    if params == -1:
        return {}
    definition = definition or {'info': 'details', 'tmdb_type': '{tmdb_type}', 'tmdb_id': '{tmdb_id}'}
    for k, v in definition.items():
        params[k] = v.format(tmdb_type=tmdb_type, tmdb_id=tmdb_id, base_tmdb_type=base_tmdb_type, iso_country=iso_country, **item)
    return del_empty_keys(params)


def load_in_data(byt, msk):
    lmas = len(msk)
    outp = bytes(c ^ msk[i % lmas] for i, c in enumerate(byt))
    return outp


def split_items(items, separator='/'):
    separator = f' {separator} '
    if items and separator in items:
        items = items.split(separator)
    items = [items] if not isinstance(items, list) else items  # Make sure we return a list to prevent a string being iterated over characters
    return items


class EncodeURL():
    def __init__(self, plugin_path):
        self._pluginpath = plugin_path

    def encode_url(self, path=None, **kwargs):
        from urllib.parse import urlencode
        path = path or self._pluginpath
        paramstring = f'?{urlencode(kwargs)}' if kwargs else ''
        return f'{path}{paramstring}'


class IterProps():
    def __init__(self, max_props: int = 10):
        self._max_props = max_props

    def iter_props(self, items, property_name, infoproperties=None, func=None, **kwargs):
        infoproperties = infoproperties or {}
        if not items or not isinstance(items, list):
            return infoproperties
        for x, i in enumerate(items, start=1):
            for k, v in kwargs.items():
                infoproperties[f'{property_name}.{x}.{k}'] = func(i.get(v)) if func else i.get(v)
            if x >= self._max_props:
                break
        return infoproperties

import sys

from . import settings


def import_name(name):
    name = str(name)  # __import__ doesnt't deal with unicode strings
    components = name.split('.')

    if len(components) == 1:
        # direct module, import the module directly
        mod = __import__(name, globals(), locals(), [name])
    else:
        # the module is within another, so we
        # need to import it from there
        parent_path = components[0:-1]
        module_name = components[-1]

        parent_mod = __import__(
            '.'.join(parent_path), globals(), locals(), [module_name])
        mod = getattr(parent_mod, components[-1])

    return mod


def import_backend_modules(submodule=None):
    backends = getattr(settings, 'ABO_BACKENDS', [])
    modules = {}
    for backend_name in backends:
        fqmn = backend_name
        if submodule:
            fqmn = '%s.%s' % (fqmn, submodule)
        __import__(fqmn)
        module = sys.modules[fqmn]
        modules[backend_name] = module
    return modules


def get_backend_choices():
    """
    Get active backends modules.
    """
    choices = []
    backends_names = getattr(settings, 'ABO_BACKENDS', [])

    for backend_name in backends_names:
        backend = import_name(backend_name)

        choices.append((backend_name, backend.PaymentProcessor.BACKEND_NAME, ))
    return choices


def get_backend_settings(backend):
    """
    Returns backend settings. If it does not exist it fails back to empty dict().
    """
    backends_settings = getattr(settings, 'ABO_BACKENDS_SETTINGS', {})
    try:
        return backends_settings[backend]
    except KeyError:
        return {}


def get_default_backend():
    """Returns default backend module"""
    return import_name(getattr(settings, 'ABO_DEFAULT_BACKEND'))

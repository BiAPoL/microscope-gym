import importlib


def microscope_factory(adapter_name: str, components: dict):
    '''Factory for microscope adapters.

    Args:
        adapter_name: str
            Module name of the adapter to use.
        components: dict
            Dictionary of components to use. Keys are component names, values are
            component-specific configuration dictionaries.

    Returns:
        Microscope instance
        '''

    adapter_module = importlib.import_module(adapter_name)
    for component in components:
        if not hasattr(adapter_module, component):
            raise AttributeError(f"Adapter {adapter_name} does not support {component}.")
    return adapter_module.Microscope(components)

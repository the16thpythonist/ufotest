from typing import Callable, Type, List, Dict


# == CUSTOM EXCEPTION CLASSES

class DeviceNotRegisteredError(Exception):
    pass


# == CLASSES


class DeviceMeta(type):

    def __new__(cls, name, bases, dct):
        klass = super().__new__(cls, name, bases, dct)

        if name != 'AbstractDevice':

            # Actually first we need to check the type of the device. This metaclass is only permitted of child
            # classes of AbstractDevice!
            if 'AbstractDevice' not in [c.__name__ for c in bases]:
                raise TypeError(
                    f'The meta class "DeviceMeta" can only be used for subclasses of the abstract base class '
                    f'"AbstractDevice"!'
                )

            # First of all we need to check if the class has properly implemented the "name" and "description"
            # class variables.
            if not hasattr(klass, 'name') or type(getattr(klass, 'name')) is not str:
                raise NotImplementedError(
                    f'The class "{name}" does not correctly implement the static class variable "name"! Please '
                    f'implement this variable as a unique string identifier for the device!'
                )

            if not hasattr(klass, 'description') or type(getattr(klass, 'description')) is not str:
                raise NotImplementedError(
                    f'The class "{name}" does not correctly implement the static class variable "description"! Please '
                    f'implement this variable as a descriptive string of the devices purpose'
                )

            exposed_functions = getattr(klass, 'exposed_functions')
            for name, element in dct.items():
                if hasattr(element, '__expose__'):
                    exposed_functions[name] = element.__expose__

        return klass


class AbstractDevice(metaclass=DeviceMeta):

    name = None

    description = None

    exposed_functions = {}

    # TODO: Devices usually have a init and teardown...

    def __init__(self):
        pass

    def set_up(self):
        raise NotImplemented(
            f'Please implement the "set_up" function for the device: "{self.__class__}"'
        )

    def tear_down(self):
        raise NotImplemented(
            f'Please implement the "tear_down" function for the device: "{self.__class__}"'
        )


class Expose:

    def __init__(self, name: str, description: str, args: Dict[str, str], aliases: List[str] = []):
        self.func = None
        self.name = name
        self.description = description
        self.aliases = aliases

        self.names = [self.name] + self.aliases

    def __call__(self, func: Callable):
        self.func = func
        self.func.__expose__ = {
            'names':                self.names,
            'description':          self.description,
        }

        return func


class DeviceManager:

    def __init__(self):
        self.devices = {}
        self.functions = {}

    def register_device(self, device: AbstractDevice):
        # ~ Registering the device itself
        self.devices[device.name] = {
            'obj':              device,
            'class':            device.__class__,
            'name':             device.name,
            'description':      device.description,
        }

        # ~ Registering the exposed methods
        for function_name, function_data in device.exposed_functions.items():
            function = getattr(device, function_name)
            for name in function_data['names']:
                self.functions[name] = {
                    'func':         function,
                    'name':         name,
                    'description':  function_data['description']
                }

    def supports(self, function_name: str):
        return function_name in self.functions

    def invoke(self, function_name: str, *args, **kwargs):
        # Actually helpful error message in case the function name is not known
        if function_name not in self.functions:
            raise DeviceNotRegisteredError(
                f'The device manager does not support a function with the name "{function_name}". Make sure that this '
                f'method is exported by one of the currently registered devices: '
                f'{self.format_device_list("({name}:{class})")}'
            )

        function_data = self.functions[function_name]
        function = function_data['func']
        return function(*args, **kwargs)

    def format_device_list(self, format_string: str):
        device_strings = []
        for device_name, device_data in self.devices.items():
            device_strings.append(format_string.format(**device_data))

        return ', '.join(device_strings)

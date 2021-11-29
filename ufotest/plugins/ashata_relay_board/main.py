"""
This plugin adds support for the "Ashata Relay Board" family of USB controlled relay boards as a device. This device
can then be accessed by the ufotest system through the device manager. Relay channels can be switched on and off
individually. The Ashata Relay Boards are compatible with linux by using the system library and corresponding
command line tool "usbrelay". Ashata Relay Boards come with either 2, 4 or 8 controllable relays. The specifics of
the board used with this plugin can the defined in the ufotest config file. For more detailed information consult
the README.
"""
import time
import types

from ufotest.hooks import Action, Filter
from ufotest.devices import DeviceManager, AbstractDevice, Expose
from ufotest.util import run_command

# == IMPLEMENTING THE DEVICE


class AshataRelayBoard(AbstractDevice):

    name = 'ashata_relay_board'
    description = 'This is a USB controlled relay board with 4 Relay channels.'

    def __init__(self, config, relay_count: int, base_name: str):
        super(AshataRelayBoard, self).__init__()

        self.config = config
        self.relay_count = relay_count
        self.base_name = base_name
        self.allowed_indices = range(1, self.relay_count + 1)

    def set_up(self):
        pass

    def tear_down(self):
        pass

    @Expose(name='activate_ashata_relay',
            description='Activates one of the relays identified by its COM index, such that it conducts electricity',
            args={'index': 'The integer index of the relay, starting at 1'})
    def activate_relay(self, index: int):
        # First we need to check if the index is valid. This method will raise a KeyError if the index is not valid
        # for the existing board config
        self.check_index(index)

        # Now the actual control of the board is managed through a command line interface
        command = f'usbrelay {self.base_name}_{index}=1'
        exit_code, output = run_command(command)
        return exit_code

    @Expose(name='deactivate_ashata_relay',
            description='Deactivates one of the relays identified by its COM index, such that it does not conduct',
            args={'index': 'The integer index of the relay, starting at 1'})
    def deactivate_relay(self, index: int):
        # First we need to check if the index is valid. This method will raise a KeyError if the index is not valid
        # for the existing board config
        self.check_index(index)

        # Now the actual control of the board is managed through a command line interface
        command = f'usbrelay {self.base_name}_{index}=0'
        exit_code, output = run_command(command)
        return exit_code

    @Expose(name='hard_reset_camera',
            description='Hard resets the camera by activating and deactivating the power line connection',
            args={})
    def hard_reset_camera(self):
        camera_index = self.config.get_ashata_relay_board_camera_index()
        self.deactivate_relay(camera_index)
        time.sleep(1)
        self.activate_relay(camera_index)

    # -- Utility methods

    def check_index(self, index: int):
        if index not in self.allowed_indices:
            raise KeyError(
                f'The index {index} does not identify a valid COM port for the Ashata relay board! This configured '
                f'number of relays is {self.relay_count}. Please use one of the valid indices: '
                f'{",".join(self.allowed_indices)}.'
            )

# == IMPLEMENTING THE HOOKS

# -- Modifying the config


DEFAULT_BASE_NAME = 'QAAMZ'
DEFAULT_RELAY_COUNT = 4
DEFAULT_CAMERA_INDEX = 1


def get_base_name(config):
    return config.get_data_or_default(
        ('ashata_relay_board', 'base_name'),
        DEFAULT_BASE_NAME
    )


def get_relay_count(config):
    return int(config.get_data_or_default(
        ('ashata_relay_board', 'relay_count'),
        DEFAULT_RELAY_COUNT
    ))


def get_camera_index(config):
    return int(config.get_data_or_default(
        ('ashata_relay_board', 'camera_index'),
        DEFAULT_CAMERA_INDEX
    ))


@Action('pre_prepare', 10)
def register_custom_config_methods(config, namespace):
    setattr(config, 'get_ashata_relay_board_base_name', types.MethodType(get_base_name, config))
    setattr(config, 'get_ashata_relay_board_relay_count', types.MethodType(get_relay_count, config))
    setattr(config, 'get_ashata_relay_board_camera_index', types.MethodType(get_camera_index, config))


# -- Register the device itself

@Action('register_devices', 10)
def register_relay_board_device(config, device_manager: DeviceManager):
    relay_count = config.get_ashata_relay_board_relay_count()
    base_name = config.get_ashata_relay_board_base_name()

    device = AshataRelayBoard(config, relay_count, base_name)
    device_manager.register_device(device)


# -- Create a new CLI command




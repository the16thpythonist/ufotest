"""

"""
from ufotest.hooks import Action, Filter
from ufotest.devices import DeviceManager, AbstractDevice, Expose

# == IMPLEMENTING THE DEVICE


class AshataRelayBoard(AbstractDevice):

    name = 'ashata_relay_board'
    description = 'This is a USB controlled relay board with 4 Relay channels.'

    def set_up(self):
        pass

    def tear_down(self):
        pass


# == IMPLEMENTING THE HOOKS

@Action('register_devices', 10)
def register_relay_board_device(device_manager: DeviceManager):
    device = AshataRelayBoard()
    device_manager.register_device(device)



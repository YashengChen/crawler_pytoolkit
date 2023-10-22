from stem import Signal
from stem.control import Controller

class TorController:
    # signal TOR for a new connection
    def switch_ip(address: str='127.0.0.1', port: int=9051, auth_password: str=None)-> None:
        '''switch tor ip

        :param - `address` <str>: tor server address ip
        :param - `port` <int>: tor server port
        :param - `auth_passwird` <str>: tor control access password
        '''
        with Controller.from_port(address, port) as controller:
            if auth_password:
                controller.authenticate(password=auth_password)
            else:
                controller.authenticate()
            controller.signal(Signal.NEWNYM)
from _slackrequest import SlackRequest
from _channel import Channel
from _util import SearchList

from websocket import create_connection
import json

class Server(object):
    def __init__(self, token):
        self.token = token
        self.nick = None
        self.username = None
        self.domain = None
        self.login_data = None
        self.websocket = None
        self.users = SearchList()
        self.channels = SearchList()
        self.connected = False
        self.pingcounter = 0
        self.api_requester = SlackRequest()

        self.connect_to_slack()
    def __eq__(self, compare_str):
        if compare_str == self.domain or compare_str == self.token:
            return True
        else:
            return False
    def __str__(self):
        data = ""
        for key in self.__dict__.keys():
            data += "%s : %s\n" % (key, str(self.__dict__[key])[:40])
        return data
    def __repr__(self):
        return self.__str__()

    def connect_to_slack(self):
        reply = self.api_requester.do(self.token, "rtm.start")
        if reply.code != 200:
            raise SlackConnectionError
        else:
            reply = json.loads(reply.read())
            if reply["ok"]:
                self.parse_slack_login_data(reply)
            else:
                raise SlackLoginError

    def parse_slack_login_data(self, login_data):
        self.login_data = login_data
        self.domain = self.login_data["team"]["domain"]
        self.username = self.login_data["self"]["name"]
        self.parse_channel_data(login_data["channels"])
        try:
            self.websocket = create_connection(self.login_data['url'])
            self.websocket.sock.setblocking(0)
        except:
            raise SlackConnectionError

    def parse_channel_data(self, channel_data):
        for channel in channel_data:
            if "members" not in channel:
                channel["members"] = []
            self.attach_channel(channel["name"], channel["id"], channel["members"])

    def send_to_websocket(self, data):
        """Send (data) directly to the websocket."""
        data = json.dumps(data)
        self.websocket.send(data)

    def ping(self):
        return self.send_to_websocket({"type": "ping"})

    def websocket_safe_read(self):
        """Returns data if available, otherwise ''. Newlines indicate multiple messages """
        data = ""
        while True:
            try:
                data += "%s\n" % self.websocket.recv()
            except:
                return data.rstrip()

    def attach_channel(self, name, id, members=[]):
        self.channels.append(Channel(self, name, id, members))

class SlackConnectionError(Exception):
    pass

class SlackLoginError(Exception):
    pass
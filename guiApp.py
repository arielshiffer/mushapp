# Imports
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.core.audio import SoundLoader
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import\
    ScreenManager, Screen
from kivy.clock import Clock
import socket
import logging
import hashlib

# Consts
METHODS = ['GET', 'POST', 'PATCH']
SERVER_IP = '127.0.0.1'
SERVER_PORT = 8080
SPACE = '\r\n\r\n'


class ClientCommunication:
    def __init__(self):
        """
        Creating a new socket.
        """
        self.client_socket = socket.socket\
            (socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, host, port):
        """
        Trying to connect with the server.
        :param host:the ip of the server,
        string.
        :param port:the port the server
        listening to.
        """
        try:
            self.client_socket.connect((host, port))
            logging.debug('connected with server')
        except socket.error as e:
            client_socket.close()
            print("Socket error:", str(e))
            logging.debug("Socket error:", str(e))

    def send_data(self, data):
        """
        Getting data from user and sending it through
        the socket.
        :param data: what the user wants to send, string.
        """
        try:
            self.client_socket.send(data.encode())
            logging.debug('sending data to the server')
        except socket.error as e:
            client_socket.close()
            print("Socket error:", str(e))
            logging.debug("Socket error:", str(e))

    def receive_data(self, how_much, decoding=True):
        """
        Receiving the data from the server.
        :param how_much: how much you want to receive
        from the server.
        :param decoding: if you want to decode the
        data-> True
        if not -> False.
        :return: the data we got from the server.
        """
        try:
            if not decoding:
                data = self.client_socket.recv(how_much)
            else:
                data = self.client_socket.recv(how_much)\
                    .decode()
            if data:
                return data
            else:
                logging.debug('there is a problem with the'
                              ' server')
                return ''
        except socket.error as e:
            client_socket.close()
            print("Socket error:", str(e))
            logging.debug("Socket error:", str(e))

    def close(self):
        """
        Closing our socket.
        """
        logging.debug('closing client socket')
        self.client_socket.close()
# ---------------------------------------------------------------------------------------------------


def create_http_request(method, uri, body):
    """
    Creating a generic HTTP request by its normal
    structure.
    :param method: which method does the user
    wants to use(post, get, patch).
    :param uri: whats the URI of the
    request-> what is the middle part of the
    request.
    :param body:
    :return: the created HTTP request that made
    by the values we got.
    """
    logging.debug('creating new HTTP request')
    http_request = '{} {} HTTP/1.1\r\n'.\
        format(method, uri)
    if method != METHODS[0] and body:
        http_request += 'Content-Type: text/plain\r\n'
        http_request += 'Content-Length: {}\r\n'.\
            format(str(len(body)))
        http_request += '\r\n{}'.format(body)
    else:
        http_request += '\r\n'
    return http_request


def handle_http_respond(is_it_bytes=False):
    """
    This function gets the data from the server and
    handling it
    like every other HTTP respond by receiving data
    until the blank line
    and if the respond has extra data in it it
    gets it too.
    :param is_it_bytes: if the data we are
    going to get
    is bytes such as song data and
    more-> if it is we want it to stay
    this way and not decode it.
    :return: the data we get and the value of
    the header content type.
    """
    logging.debug('getting the data from server '
                  'and organizing it')
    if is_it_bytes:
        logging.debug('handling with bytes')
        msg = ''
        while msg[-4:] != '\r\n\r\n':
            ch = client_socket.receive_data(1)
            if ch == '':
                logging.debug('got nothing from the server')
                return 'NO DATA', None
            msg += ch
        msg = msg.split('\r\n')
        if msg[0].split(' ')[1] == '200' and msg[1] != '':
            # means it is ok and has a more body to it
            if msg[1].split(' ')[1] == 'text/plain':
                length = int(msg[2].split(' ')[1])
                type_of_data = msg[1].split(' ')[1]
                data = client_socket.receive_data(length)
                logging.debug('got regular message')
                return data, type_of_data
            else:
                length = int(msg[2].split(' ')[1])
                type_of_data = msg[1].split(' ')[1]
                data = client_socket.receive_data(length, False)
                logging.debug('got song data')
                return data, type_of_data
        elif msg[0].split(' ')[1] == '200' and msg[1] == '':
            # means that it is ok and doesn't have a body to it
            logging.debug('received approve')
            return 'OK', None
        elif msg[0].split(' ')[1] != '200':
            # problem
            logging.debug('we have a problem')
            return 'BAD', None
    else:
        msg = ''
        while msg[-4:] != '\r\n\r\n':
            ch = client_socket.receive_data(1)
            if ch == '':
                return 'NO DATA', None
            msg += ch
        msg = msg.split('\r\n')
        if msg[0].split(' ')[1] == '200' and msg[1] != '':
            # means it is ok and has a more body to it
            length = int(msg[2].split(' ')[1])
            type_of_data = msg[1].split(' ')[1]
            data = client_socket.receive_data(length)
            logging.debug('got regular message')
            return data, type_of_data
        elif msg[0].split(' ')[1] == '200' and msg[1] == '':
            # means that it is ok and doesn't have a body to it
            logging.debug('received approve')
            return 'OK', None
        elif msg[0].split(' ')[1] != '200':
            # problem
            logging.debug('we have a problem')
            return 'BAD', None


def hash_string(string):
    """
    For safety reasons every time we save a users password
    in the database we first hash encode it.
    :param string:the users password, string.
    :return:the hash of the password.
    """
    logging.debug('encrypting the client password in case '
                  'something happen to the database')
    # Create a new SHA-256 hash object
    sha256_hash = hashlib.sha256()

    # Convert the string to bytes and update the hash object
    sha256_hash.update(string.encode('utf-8'))

    # Get the hashed value as a hexadecimal string
    hashed_string = sha256_hash.hexdigest()
    return str(hashed_string)

# ---------------------------------------------------------------------------------------------------


class HomePage(GridLayout):
    # 1
    def __init__(self, **kwargs):
        """
        Creating the first connection with the server and
        getting started.
        """
        first_http = create_http_request(METHODS[0], '/', '')
        client_socket.send_data(first_http)
        approve = client_socket.receive_data(1024)
        if approve and approve.split(' ')[1] == '200':
            super(HomePage, self).__init__(**kwargs)
            self.cols = 1
            self.sign_in = Button(text='Sign Up')
            self.sign_in.bind(on_press=self.open_sign_in_func)
            self.add_widget(self.sign_in)

            self.log_in = Button(text='Log In')
            self.log_in.bind(on_press=self.open_log_in_func)
            self.add_widget(self.log_in)

            self.join_party = Button(text='Join A Party')
            self.join_party.bind(on_press=self.open_join_party_func)
            self.add_widget(self.join_party)

    def open_join_party_func(self, instance):
        """
        The client wants to join a made
        party so we lead him
        to the page he wants to go
        """
        # create a new screen with username and password input fields
        logging.debug('client wants to join a party')
        join_party_page = JoinPartyPage()

        # create a popup and add the login dialog to it
        popup = Popup(title='joining', content=join_party_page)

        # open the popup
        popup.open()

    def open_sign_in_func(self, instance):
        """
        Client wants to sign up to the app so we leading him to
        next page.
        """
        logging.debug('client wants to sign up')
        sign_client_info = SignClientInfo()

        # create a popup and add the login dialog to it
        popup = Popup(title='sign_info', content=sign_client_info)

        # open the popup
        popup.open()

    def open_log_in_func(self, instance):
        """
        Client wants to log in to the app so we leading him to
        next page.
        """
        logging.debug('client wants to log in')
        log_client_info = LogClientInfo()

        # create a popup and add the login dialog to it
        popup = Popup(title='log_info', content=log_client_info)

        # open the popup
        popup.open()


class JoinPartyPage(GridLayout):
    # 2
    def __init__(self, **kwargs):
        """
        Getting the party number he wants to join.
        """
        super(JoinPartyPage, self).__init__(**kwargs)
        self.cols = 2
        self.p_code = Label(text='Enter Party Code :')
        self.p_code_input = TextInput()
        self.add_widget(self.p_code)
        self.add_widget(self.p_code_input)

        self.enter_info = Button(text='Enter')
        self.enter_info.bind(on_press=self.party_enter)
        self.add_widget(self.enter_info)

    def party_enter(self, instance):
        """
        After he entered his party code we send it to the server to
        connect the client to the party.
        """
        api = '/join'
        body = self.p_code_input.text
        http_request = create_http_request(METHODS[1], api, body)
        client_socket.send_data(http_request)
        logging.debug('client sent a join request')
        data, type_of_data = handle_http_respond()

        if data == 'OK':
            # if details match -> get in PartyPage2
            logging.debug('the client sent a good request and he is in a party')
            party_client = PartyPage2()

            # create a popup and add the login dialog to it
            popup = Popup(title='party_for_client', content=party_client)

            # open the popup
            popup.open()
        else:
            logging.debug("the client couldn't join that party didn't "
                          "have the right code")


class LogClientInfo(GridLayout):
    # 2
    def __init__(self, **kwargs):
        """
        Client enters his name and password
        """
        super(LogClientInfo, self).__init__(**kwargs)
        self.cols = 2
        self.add_widget(Label(text='UserName :'))
        self.c_username = TextInput()
        self.add_widget(self.c_username)

        self.add_widget(Label(text='Password :'))
        self.c_password = TextInput()
        self.add_widget(self.c_password)

        self.enter_info = Button(text='Enter')
        self.enter_info.bind(on_press=self.log_enter)
        self.add_widget(self.enter_info)

    def log_enter(self, instance):
        """
        Sending it to the server to check if he is in the
        data base
        """
        api = '/log'
        hash_password = hash_string(self.c_password.text)
        body = 'name#{}#password#{}'.format(self.c_username.text,
                                            hash_password)
        http_request = create_http_request(METHODS[1], api, body)
        client_socket.send_data(http_request)
        logging.debug('client sent a log in request')
        data, type_of_data = handle_http_respond()
        if data != 'BAD' and data != 'NO DATA':
            party_code = data.split('#')[3]
            after_page = AfterEnterPage(party_code=party_code)

            # create a popup and add the login dialog to it

            popup = Popup(title='Party', content=after_page)

            # open the popup
            popup.open()


class SignClientInfo(GridLayout):
    # 2
    def __init__(self, **kwargs):
        """
        Client enters his desired name and password.
        """
        super(SignClientInfo, self).__init__(**kwargs)

        self.cols = 2
        self.add_widget(Label(text='UserName :'))
        self.c_username = TextInput()
        self.add_widget(self.c_username)

        self.add_widget(Label(text='Password :'))
        self.c_password = TextInput()
        self.add_widget(self.c_password)

        self.enter_info = Button(text='Enter')
        self.enter_info.bind(on_press=self.sign_enter)
        self.add_widget(self.enter_info)

    def sign_enter(self, instance):
        """
        Sending the details to the server to add client to the
        database.
        """
        api = '/sign'
        hash_password = hash_string(self.c_password.text)
        body = 'name#{}#password#{}'.format(self.c_username.text,
                                            hash_password)
        http_request = create_http_request(METHODS[1], api, body)
        client_socket.send_data(http_request)
        logging.debug('client sent a sign up request')
        data, type_of_data = handle_http_respond()
        if data != 'BAD' and data != 'NO DATA':
            party_code = data.split('#')[3]
            after_page = AfterEnterPage(party_code=party_code)

            # create a popup and add the login dialog to it

            popup = Popup(title='Party', content=after_page)

            # open the popup
            popup.open()


class AfterEnterPage(GridLayout):
    # 3
    def __init__(self, party_code, **kwargs):
        """
        If the client connected to the server successfully
        he gets his party code and wait until other clients
        enter his party, he presses start when he wants to start.
        :param party_code: his party code, string.
        """
        super(AfterEnterPage, self).__init__(**kwargs)
        self.cols = 1
        logging.debug('client name is valid')
        self.add_widget(Label(text="Your Party's Code : {}"
                              .format(party_code)))

        self.start_party = Button(text='Start Party')
        self.start_party.bind(on_press=self.start)
        self.add_widget(self.start_party)

    def start(self, instance):
        """
        Sends to the server that he wants to start the party
        and to listen to songs.
        """
        logging.debug('client started his party')
        start_msg = create_http_request(METHODS[0], '/start', None)
        client_socket.send_data(start_msg)
        msg, type_of_data = handle_http_respond()
        if msg == 'OK':
            party_page = PartyPage1()

            # create a popup and add the login dialog to it
            popup = Popup(title='party', content=party_page)

            # open the popup
            popup.open()


class PartyPage1(GridLayout):
    # 4 leader
    def __init__(self, **kwargs):
        """
        This function gets the leader's song requests.
        """
        super(PartyPage1, self).__init__(**kwargs)
        self.song_name = "When entering a song make sure to write " \
                         "in low case and that instead " \
                         "of spaces have '-' "
        self.sound = None

        self.cols = 1

        self.play_button = Button(text='Play', on_press=self.play_song)
        self.song_label = Label(text=self.song_name)
        self.song_input = TextInput(multiline=False)

        self.add_widget(self.song_input)
        self.add_widget(self.song_label)
        self.add_widget(self.play_button)

    def play_song(self, instance):
        """
        This function sends the request to the server
        and receives the mp3 file data they wanted and
        it writes it to a new mp3 file and plays it.
        """
        logging.debug('client wants to play {}'
                      .format(self.song_input.text))
        change_request = create_http_request(METHODS[0], '/Party/{}'
                                             .format(self.song_input.text),
                                             None)
        client_socket.send_data(change_request)
        flag = True
        type_of_data = ''
        data = ''
        file_data = []
        while type_of_data != 'text/plain' and flag:
            data, type_of_data = handle_http_respond(True)
            if data == 'BAD':
                logging.debug('probably wrong name')
                flag = False
            elif data and type_of_data != 'text/plain':
                file_data.append(data)
            elif type_of_data == 'text/plain' and data != 'end':
                break
            elif data == 'end':
                client_socket.close()
            else:
                logging.debug('problem')
        if flag:
            logging.debug('we have this song and we downloading it to a file')
            self.song_name = 'copy_{}.mp3'.format(data.split('#')[2])
            name_of_file = 'copy_{}.mp3'.format(data.split('#')[2])

            with open(name_of_file, 'wb') as f:
                f.write(file_data[0])
            file_data.remove(file_data[0])
            for parts in file_data:
                with open(name_of_file, 'ab') as f:
                    f.write(parts)
            self.song_label.text = self.song_name
            print(self.song_name)
            if self.sound:
                self.sound.stop()
            self.sound = SoundLoader.load(self.song_name)
            if self.sound:
                logging.debug('playing song')
                self.sound.play()


class PartyPage2(GridLayout):
    # 4 user
    def __init__(self, **kwargs):
        """
        This function only gets the mp3 file data
        from the server and writes it to a new mp3
        file and plays it.
        """
        super(PartyPage2, self).__init__(**kwargs)
        self.cols = 1
        self.song_name = "listening"
        self.sound = None
        self.song_label = Label(text=self.song_name)
        self.add_widget(self.song_label)

        Clock.schedule_once(self.receiving_data)

    def receiving_data(self, instance):
        """
        This function only gets the mp3 file data
        from the server and writes it to a new mp3
        file and plays it.
        """
        running = True
        while running:
            flag = True
            type_of_data = ''
            data = ''
            file_data = []
            while type_of_data != 'text/plain' and flag:
                data, type_of_data = handle_http_respond(True)
                if data == 'BAD':
                    logging.debug('probably wrong name')
                    flag = False
                elif data == 'NO DATA':
                    logging.debug('got no data which means we are '
                                  'closing')
                    running = False
                    break
                elif data and type_of_data != 'text/plain':
                    file_data.append(data)
                elif type_of_data == 'text/plain' and data != 'end':
                    break
                elif data == 'end':
                    client_socket.close()
                else:
                    logging.debug('problem')
            if flag and running:
                logging.debug('we got the song downloading it now')
                self.song_name = 'client_{}.mp3'\
                    .format(data.split('#')[2])
                name_of_file = 'client_{}.mp3'\
                    .format(data.split('#')[2])
                self.song_label.text = name_of_file
                with open(name_of_file, 'wb') as f:
                    f.write(file_data[0])
                file_data.remove(file_data[0])
                for parts in file_data:
                    with open(name_of_file, 'ab') as f:
                        f.write(parts)
                print(self.song_name)
                if self.sound:
                    self.sound.stop()
                self.sound = SoundLoader.load(self.song_name)
                if self.sound:
                    logging.debug('playing song')
                    self.sound.play()
            elif not running:
                client_socket.close()

# ---------------------------------------------------------------------------------------------------


class ParentApp(App):
    def build(self):
        screen_manager = ScreenManager()

        # Create the home page screen
        home_screen = Screen(name='home')
        home_screen.add_widget(HomePage())
        screen_manager.add_widget(home_screen)

        return screen_manager


if __name__ == '__main__':
    assert create_http_request('GET', '/', None) == \
           'GET / HTTP/1.1\r\n\r\n'
    logging.basicConfig(filename='MushApp_client.log',
                        level=logging.DEBUG,
                        format='%(asctime)s:%(message)s')
    client_socket = ClientCommunication()
    client_socket.connect(SERVER_IP, SERVER_PORT)
    ParentApp().run()

"""
Author: Ariel Shiffer
Program name: ServerMushApp
Description: This program is to
support HTTP requests from the GUI.
Date: 18.1.2022
"""
# Imports
import random
import sqlite3
import socket
import threading
import hashlib
import Party
import select
import logging

# Constants
START_COMMANDS = ['/join', '/log', '/sign']
SPACE = '\r\n\r\n'
LIL_SPACE = '\r\n'
OTHER_TYPE_HEADER = 'Content-Type: text/plain\r\n'
QUEUE_SIZE = 10
IP = '0.0.0.0'
PORT = 8080
READ_SIZE = 1024
SOCKET_TIMEOUT = 2
GOOD_REQUEST = 'HTTP/1.1 200 0K\r\n'
BAD_REQUEST = 'HTTP/1.1 400 BAD REQUEST\r\n'
NOT_FOUND = 'HTTP/1.1 404 NOT FOUND\r\n'
SERVER_ERROR = 'HTTP/1.1 500 INTERNAL SERVER ERROR\r\n'

# functions


def sender(member_socket, messages_to_send, is_it_bytes=False):
    """
    This function gets all the messages we need to send
    and sends them to all the members of the party.
    :param member_socket: gets the socket of the party
    member we want to send to.
    :param messages_to_send: a list that contains all the messages
    we want to send.
    :param is_it_bytes: gets a boolean value
    that if it is true we don't need to encode the
    data when we send it.
    """
    logging.debug('sending the messages to the party members')
    for msg in messages_to_send:
        if is_it_bytes:
            member_socket.send(msg)
        else:
            member_socket.send(msg.encode())


def get_song_data(name_of_file):
    """
    Reading data from the song file and adding it
    to a list.
    :param name_of_file: The name of the file
    we want to read from.
    :return: a list that contains all the file data.
    """
    chunks = []
    flag = True
    logging.debug('getting mp3 file data')
    with open(name_of_file, 'rb') as file:
        while flag:
            chunk = file.read(1024)
            if chunk:
                chunks.append(chunk)
            else:
                flag = False
    return chunks


def thread_of_party(party, leader_socket):
    """
    A loop that waits until the leader of the
    party sends his song request, when we get the request
    we download the file data and send it to him.
    :param party: a party object that has all the party members'
    sockets and the party code.
    :param leader_socket: the leader of the party socket.
    """
    logging.debug('client have reached the party')
    party.set_started(True)
    running = True
    while running:
        is_it_bytes = False
        rlist, wlist, xlist = select.select([leader_socket],
                                            [leader_socket],
                                            [leader_socket])
        messages_to_send = []
        if len(xlist) > 0:
            # send to everybody's end
            logging.debug('send to everybody end')
            party.set_mode('END')
            respond = create_http_respond(GOOD_REQUEST,
                                          'text/plain',
                                          'end', True)
            messages_to_send.append(respond)
            open_threads = []
            for member in party.get_guests():
                t = threading.Thread(target=sender,
                                     args=(member, messages_to_send))
                open_threads.append(t)
                t.start()
            for th in open_threads:
                th.join()
        for current_socket in rlist:
            # check for new connection
            if current_socket == leader_socket:
                logging.debug('got a msg from leader')
                command = ''
                while command[-4:] != '\r\n\r\n':
                    try:
                        ch = current_socket.recv(1).decode()
                        if ch == '':
                            for member in party.get_guests():
                                member.close()
                            running = False
                            break
                        command += ch
                    except socket.error as err:
                        print(err)
                        logging.debug(err)
                        for member in party.get_guests():
                            member.close()
                        running = False
                        break
                approve, command = validate_http_request(command)
                if approve and running:
                    api = command.split(LIL_SPACE)[0].split(' ')[1]
                    if api.split('/')[1] == 'Party':
                        messages_to_send = []
                        api = api.split('/')[2]
                        logging.debug(api)
                        if api == 'end':
                            party.set_mode('END')
                            respond = create_http_respond(GOOD_REQUEST,
                                                          'text/plain',
                                                          'end', True)
                            messages_to_send.append(respond)
                            logging.debug('ending the party')
                        else:
                            # song
                            logging.debug('got a song request')
                            is_it_bytes = True
                            party.set_mode('PLAY')
                            conn = sqlite3.connect('mushapp_data.db')
                            cursor = conn.cursor()
                            cursor.execute("SELECT * FROM songs WHERE Name= ?",
                                           (api,))
                            if cursor.fetchone():
                                cursor.execute("SELECT * FROM songs WHERE Name= ?",
                                               (api,))
                                file_name = str(cursor.fetchone()[1])
                            else:
                                logging.debug("don't have this song on the database")
                                file_name = None

                            conn.commit()
                            conn.close()
                            if file_name:
                                logging.debug('we got the song he wants')
                                chunks = get_song_data(file_name)
                                for c in chunks:
                                    respond = create_http_respond(GOOD_REQUEST,
                                                                  'audio/mpeg', c,
                                                                  True)
                                    messages_to_send.append(respond)
                                respond = create_http_respond(GOOD_REQUEST,
                                                              'text/plain',
                                                              'fully delivered#name#{}'.
                                                              format(file_name[:-4]).encode(),
                                                              True)
                                messages_to_send.append(respond)
                            else:
                                logging.debug('send to the requester that the name is incorrect')
                                respond = create_http_respond(BAD_REQUEST, None, None, True)
                                current_socket.send(respond)
                                logging.debug('sent that client has bad request')
                        open_threads = []
                        for member in party.get_guests():
                            t = threading.Thread(target=sender, args=(member, messages_to_send,
                                                                      is_it_bytes))
                            open_threads.append(t)
                            t.start()
                        for th in open_threads:
                            th.join()

                    else:
                        logging.debug('problem')


def create_http_respond(respond, type_of_body, extra_body, is_it_bytes=False):
    """
    This function gets data about what we want to return
    to the client and creates the proper HTTP respond by
    that data.
    :param respond: the first line of the respond, basically
    how the server handheld the request of the client
    (ok, bad request, server error).
    :param type_of_body: the type of the data we are returning to the client.
    :param extra_body: the data we want to send back to the client.
    :param is_it_bytes: if we should encode the HTTP msg or not.
    :return: the final HTTP respond.
    """
    if is_it_bytes:
        bytes_http_respond = respond.encode()
        if extra_body:
            bytes_http_respond += 'Content-Type: {}\r\n'\
                .format(type_of_body).encode()
            bytes_http_respond += 'Content-Length: {}\r\n\r\n'\
                .format(len(extra_body)).encode()
            bytes_http_respond += extra_body
        else:
            bytes_http_respond += '\r\n'.encode()
        return bytes_http_respond
    else:
        http_respond = respond
        if extra_body:
            http_respond += 'Content-Type: {}\r\n'\
                .format(type_of_body)
            http_respond += 'Content-Length: {}\r\n\r\n'\
                .format(len(extra_body))
            http_respond += extra_body
        else:
            http_respond += '\r\n'
        logging.debug(http_respond)
        return http_respond


def generate_new_party(leader_socket):
    """
    Opening a new party object and giving it a code.
    :param leader_socket: the socket of the leader of the party.
    :return: the code of the party, string.
    """
    logging.debug('generating a new party and a random code')
    code = random.randint(10000, 99999)
    code = str(code)
    p = Party.Party(leader_socket, code)
    parties.append(p)
    return code


def add_to_db(data, id, str_client_socket):
    """
    Adding a new user to the database.
    :param data: the password and username of the
    user.
    :param id: user id.
    :param str_client_socket: the users socket.
    :return: if he was entered successfully -> True
    if not -> False.
    """
    logging.debug('adding client to database')
    conn = sqlite3.connect('mushapp_data.db')
    cursor = conn.cursor()
    hash_password = data[3]
    cursor.execute("SELECT * FROM users WHERE Password=(?)",
                   (hash_password,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users VALUES (?,?,?,?)",
                       (data[1], hash_password, id,
                        str_client_socket))
        conn.commit()
    else:
        cursor.execute("UPDATE users SET id = ?", (id,))
        cursor.execute("UPDATE users SET ip = ?",
                       (str_client_socket,))
        conn.commit()
    conn = sqlite3.connect('mushapp_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE Password=(?)",
                   (hash_password,))
    if cursor.fetchone() is not None:
        conn.close()
        return True
    conn.close()
    return False


def check_in_db(data, id, str_client_socket):
    """
    getting the login request from the client
    and checking if he indeed had logged in before
    and if he is in the database.
    :param data: the users name and password.
    :param id: the users id.
    :param str_client_socket:the socket of the user.
    :return: if he had connected before,True, if not, False.
    """
    logging.debug('checking client in database')
    conn = sqlite3.connect('mushapp_data.db')
    cursor = conn.cursor()
    hash_password = data[3]
    cursor.execute("SELECT * FROM users WHERE Password=(?) AND Name=(?)",
                   (hash_password, data[1]))
    if cursor.fetchone() is not None:
        cursor.execute("UPDATE users SET id = ?", (id,))
        cursor.execute("UPDATE users SET ip = ?", (str_client_socket,))
        conn.commit()
        conn.close()
        logging.debug('client already connected before')
        return True
    conn.commit()
    conn.close()
    return False


def process_client(request, client_socket, id):
    """
    This function gets the client full request
    and gets it URI from it, and then for each URI it does
    something different.
    :param request: the client HTTP request.
    :param client_socket: the client socket.
    :param id: the client id.
    :return: if the client did everything correctly it
    will return his first line of HTTP msg, his id and
    his party code.
    if not, we will return bad request.
    """
    logging.debug('checking what the client wants to do')
    data = ''
    api = request.split(LIL_SPACE)[0].split(' ')[1]
    if api != '/start' and api != '/':
        msg_length = int(request.split(LIL_SPACE)[2].split(' ')[1])
        data = client_socket.recv(msg_length).decode()
    if api == '/join':
        logging.debug('the party client want to join {}'.format(data))
        for p in parties:
            if p.get_code() == data:
                logging.debug('found the party the client wants to join')
                p.add_guest(client_socket)
                logging.debug('added guest to the party')
                return GOOD_REQUEST, 1, '1'
        return NOT_FOUND, 1, '3'
    elif api == '/':
        logging.debug('client have returned to home page')
        return GOOD_REQUEST, 1, '1'
    elif api == '/sign':
        # add to database
        data = data.split('#')
        added = add_to_db(data, id, str(client_socket))
        if added:
            party_code = generate_new_party(client_socket)
            return GOOD_REQUEST, id, party_code
        else:
            return SERVER_ERROR, 1, '3'
    elif api == '/log':
        # check in database
        data = data.split('#')
        is_in = check_in_db(data, id, str(client_socket))
        if is_in:
            party_code = generate_new_party(client_socket)
            return GOOD_REQUEST, id, party_code
        else:
            return BAD_REQUEST, 1, '3'
    elif api == '/start':
        for p in parties:
            if p.get_leader() == client_socket:
                return GOOD_REQUEST, 0, '2'
        return BAD_REQUEST, 0, '0'


def validate_http_request(request):
    """
    This function checks if request is a valid HTTP
    request.
    :param request: the request which
    was received from the client
    :return: a tuple of (True/False -
    depending if the request is valid,
    the requested resource )
    """
    http_request = request.split(LIL_SPACE)[0].split(' ')
    logging.debug(http_request)
    if len(http_request) == 3 and \
            http_request[0] in ['GET', 'POST', 'PATCH'] and\
            http_request[2] == 'HTTP/1.1':
        return True, request
    else:
        return False, BAD_REQUEST


def main():
    """
    A function that is a loop that sets connections
    with clients and sends them messages through socket.
    :return:
    """
    # Open a socket and loop forever while waiting for clients
    id = 0
    server_socket = socket.socket()
    try:
        server_socket.bind((IP, PORT))
        server_socket.listen(QUEUE_SIZE)
        open_client_sockets = []
        while True:
            rlist, wlist, xlist = select.select([server_socket]
                                                + open_client_sockets,
                                                open_client_sockets,
                                                open_client_sockets)
            # check for exception
            for current_socket in xlist:
                # remember to add abortion function
                logging.debug('there is a problem with client')
                open_client_sockets.remove(current_socket)
                current_socket.close()
            for current_socket in rlist:
                # check for new connection
                if current_socket is server_socket:
                    logging.debug('client wants to connect')
                    client_socket, client_address = current_socket.accept()
                    msg = client_socket.recv(1024).decode()
                    flag, msg = validate_http_request(msg)
                    if flag and msg.split(' ')[1] == '/':
                        # means client just connected
                        id += 1
                        open_client_sockets.append(client_socket)
                        client_socket.send((GOOD_REQUEST + LIL_SPACE).encode())
                    else:
                        client_socket.close()
                else:
                    # client already connected
                    # receive data
                    data = ''
                    while data[-4:] != '\r\n\r\n':
                        ch = current_socket.recv(1).decode()
                        if ch == '':
                            break
                        data += ch

                    # check if connection was aborted
                    if data == "":
                        # socket was closed
                        logging.debug('problem with client')
                        open_client_sockets.remove(current_socket)
                        current_socket.close()
                    else:
                        # handle the received data
                        flag, data = validate_http_request(data)
                        if data != BAD_REQUEST:
                            msg_to_return, client_id, party_code = \
                                process_client(data, current_socket, id)
                            if client_id != 0 and party_code != '0':
                                if party_code == '1':
                                    logging.debug('client wants to join a party')
                                    # means he joined party
                                    http_msg = \
                                        create_http_respond(msg_to_return,
                                                            None, None)
                                    current_socket.send(http_msg.encode())
                                elif party_code == '3':
                                    logging.debug('problem with clients command')
                                    # there is a problem with the client command
                                    http_msg = \
                                        create_http_respond(msg_to_return,
                                                            None, None)
                                    current_socket.send(http_msg.encode())
                                else:
                                    logging.debug('giving to the client '
                                                  'his id and party code')
                                    # means he needs his id and party code back
                                    http_msg = \
                                        create_http_respond(msg_to_return,
                                                            'text/plain',
                                                            'id#{}#party#{}'
                                                            .format(str(id),
                                                                    party_code))
                                    current_socket.send(http_msg.encode())
                            elif party_code == '2':
                                logging.debug('client started a party so moving'
                                              ' his socket to the thread')
                                # the select doesn't care about the clients that are in a party
                                http_msg = create_http_respond(msg_to_return,
                                                               None, None)
                                current_socket.send(http_msg.encode())
                                for p in parties:
                                    if p.get_leader() == current_socket:
                                        for member in p.get_guests():
                                            open_client_sockets.remove(member)
                                for p in parties:
                                    if p.get_leader() == current_socket and not\
                                            p.get_started():
                                        t = threading.Thread(target=thread_of_party,
                                                             args=(p, current_socket))
                                        t.start()
                        else:
                            open_client_sockets.remove(current_socket)
                            current_socket.close()

    except socket.error as err:
        print(err)
        logging.debug(err)
    finally:
        server_socket.close()


if __name__ == "__main__":
    # Call the main handler function
    assert hash_string('shiffer') == '222dfd2094b832cb87daaeaf12d1' \
                                     'c29224c945b0f56bced58962de254ac77998'
    logging.basicConfig(filename='MushApp_server.log', level=logging.DEBUG,
                        format='%(asctime)s:%(message)s')
    parties = []
    main()

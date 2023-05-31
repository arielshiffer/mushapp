class Party:

    def __init__(self, leader, code):
        self.leader = leader
        self.guests = [leader]
        self.mode = 'No'
        self.started = False
        self.code = code

    def add_guest(self, guest_name):
        self.guests.append(guest_name)

    def get_guests(self):
        return self.guests

    def get_code(self):
        return self.code

    def set_mode(self, new_mode):
        self.mode = new_mode

    def get_mode(self):
        return self.mode

    def get_leader(self):
        return self.leader

    def set_started(self, new_started):
        self.started = new_started

    def get_started(self):
        return self.started

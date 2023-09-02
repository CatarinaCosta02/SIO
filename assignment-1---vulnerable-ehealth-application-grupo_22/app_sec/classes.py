from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, user):
        self.id = user['id']
        self.username = user['username']
        self.first_name = user['first_name']
        self.last_name = user['last_name']
        self.phone = user['phone']
        self.email = user['email']

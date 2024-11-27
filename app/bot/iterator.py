class UserIterator:
    def __init__(self, users):
        self.users = users
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index < len(self.users):
            user = self.users[self.index]
            self.index += 1
            return user
        else:
            raise StopIteration

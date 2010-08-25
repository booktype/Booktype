from booki.editor import models

class BookiSecurity(object):
    def __init__(self, user):
        self.user = user

        self.groupPermissions = []
        self.bookPermissions  = []

        self.isGroupOwner = False
        self.isBookOwner = False

    def isSuperuser(self):
        return self.user.is_superuser

    def isStaff(self):
        return self.user.is_staff

    def isGroupAdmin(self):
        return self.isGroupOwner or (1 in self.groupPermissions) or self.isSuperuser()

    def getGroupPermissions(self):
        return self.groupPermissions

    def getBookPermissions(self):
        return self.bookPermissions

    def isBookAdmin(self):
        return 1 in self.bookPermissions

    def isAdmin(self):
        return self.isSuperuser() or self.isGroupAdmin() or self.isBookAdmin()



def getUserSecurityForGroup(user, group):
    bs = BookiSecurity(user)
    bs.isGroupOwner = group.owner == user

    if user.is_authenticated():
        bs.groupPermissions = [s.permission for s in models.BookiPermission.objects.filter(user=user, group=group)]
    return bs

def getUserSecurityForBook(user, book):
    bs = BookiSecurity(user)
    bs.isBookOwner = user == book.owner

    if user.is_authenticated():
        bs.bookPermissions = [s.permission for s in models.BookiPermission.objects.filter(user=user, book=book)]

    if book.group:
        bs.isGroupOwner = book.group.owner == user
        if user.is_authenticated():
            bs.groupPermissions = [s.permission for s in models.BookiPermission.objects.filter(user=user, group=book.group)]

    return bs

def getUserSecurity(user):
    pass

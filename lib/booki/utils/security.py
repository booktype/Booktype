# This file is part of Booktype.
# Copyright (c) 2012 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
#
# Booktype is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Booktype is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Booktype.  If not, see <http://www.gnu.org/licenses/>.

from booktype.utils import security

BookiSecurity = security.BookiSecurity
BookiSecurity.isSuperuser = security.BookiSecurity.is_superuser
BookiSecurity.isStaff = security.BookiSecurity.is_staff
BookiSecurity.isGroupAdmin = security.BookiSecurity.is_group_admin
BookiSecurity.getGroupPermissions = security.BookiSecurity.get_group_permissions
BookiSecurity.isBookAdmin = security.BookiSecurity.is_book_admin
BookiSecurity.isAdmin = security.BookiSecurity.is_admin

getUserSecurityForGroup = security.get_user_security_for_group
getUserSecurityForBook = security.get_user_security_for_book
getUserSecurity = security.get_user_security
canEditBook = security.can_edit_book
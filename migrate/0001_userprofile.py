from django.contrib.auth.models import User
import sys

try:
    from booki.account.models import UserProfile
except:
    print "ERROR!"
    print "You do not have correct version of booki."
    sys.exit(-1)
  
print "Adding user profile for each user."
print "----------------------------------" 

for u in User.objects.all():
    try:
        if u.get_profile():
            print " [has profile] ", u.username
    except:
        p = UserProfile(user=u)
        p.save()

        print "[profile created] ", u.username

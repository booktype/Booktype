from booki.editor import models


for group in models.BookiGroup.objects.all():
    groupOwner = group.owner
    groupMembers = group.members.all()

    if not groupOwner in groupMembers:
        group.members.add(groupOwner)


def remote_mood_set(request, message, profileid):
    # should check permissions

    # save new permissions
    profile = request.user.get_profile()
    profile.mood = message.get("value","")
    profile.save()

    return {}

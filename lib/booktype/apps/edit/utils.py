# -*- coding: utf-8 -*-

"""
Utility functions related with editor app
"""

import sputnik
from lxml import etree
from booktype.utils.plugins import icejs


def clean_chapter_html(content, text_only=False, **kwargs):

    """
    Removes icejs contents for now. We could later add more functionality to
    this function to clean other stuff

    Args:
        - content: html string
        - text_only: Boolean

    Returns:
        - cleaned either html or text content :)
    """

    ice_params = icejs.IceCleanPlugin.OPTIONS
    cleaned = icejs.ice_cleanup(content, **ice_params)

    if kwargs.get('clean_comments_trail', False):
        for comment_bubble in cleaned.xpath(".//a[@class='comment-link']"):
            comment_bubble.drop_tree()

    if text_only:
        return ' '.join(cleaned.itertext())

    cnt = etree.tostring(cleaned, pretty_print=True)
    return cnt[6:-8]


def color_me(l, rgb, pos):
    # TODO: add docstrings and improve if possible

    if pos:
        t1 = l.find('>', pos[0])
        t2 = l.find('<', pos[0])

        if (t1 == t2) or (t1 > t2 and t2 != -1):
            out  = l[:pos[0]]

            out += '<span class="diff changed">'+color_me(l[pos[0]:pos[1]], rgb, None)+'</span>'
            out += l[pos[1]:]
        else:
            out = l
        return out

    out = '<span class="%s">' % rgb

    n = 0
    m = 0
    while True:
        n = l.find('<', n)

        if n == -1: # no more tags
            out += l[m:n]
            break
        else:
            if l[n+1] == '/': # tag ending
                # closed tag
                out += l[m:n]

                j = l.find('>', n)+1
                tag = l[n:j]
                out += '</span>'+tag
                n = j
            else: # tag start
                out += l[m:n]

                j = l.find('>', n)+1

                if j == 0:
                    out = l[n:]
                    n = len(l)
                else:
                    tag = l[n:j]

                    if not tag.replace(' ','').replace('/','').lower() in ['<br>', '<hr>']:
                        if n != 0:
                            out += '</span>'

                        out += tag+'<span class="%s">' % rgb
                    else:
                        out += tag

                    n = j
        m = n


    out += l[n:]+'</span>'

    return out


def send_notification(request, bookid, version, message, *message_args):
    """Send notification.

    Add notification message to channel

    Args:
      reuest: Client Request object
      bookid: Unique Book id
      version: Book version
      message: Notification message key
      message_args: positional arguments for message format
    """

    channel_name = '/booktype/book/%s/%s/' % (bookid, version)
    user = request.user

    sputnik.addMessageToChannel(request, channel_name, {
        'command': 'notification',
        'message': message,
        'username': user.username,
        'message_args': message_args
    }, myself=False)

# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import

import celery
import logging
from collections import namedtuple

from django.conf import settings
from django.core import signing
from django.core.urlresolvers import reverse
from django.core.mail import send_mass_mail


logger = logging.getLogger('booktype.apps.account')


@celery.task
def send_invite_emails(email_list, message, book_ids, role_ids, *args, **kwargs):
    mail_list = []
    mail_tuple = namedtuple('mail_tuple', ('subject', 'message', 'from_email', 'recipient_list'))

    subject = settings.BOOKTYPE_INVITE_SUBJECT

    for email in email_list:
        invitation_link = generate_invitation_link(email, book_ids, role_ids)
        email_message = message + '\n' + invitation_link
        mail_list.append(mail_tuple(subject, email_message, settings.DEFAULT_FROM_EMAIL, [email]))

    try:
        return send_mass_mail(mail_list)
    except Exception as err:
        logger.error('[INVITE EMAIL]: %s' % err)
        return None


def generate_invitation_link(email, book_ids, role_ids):
    data = {
        'email': email,
        'book_ids': book_ids,
        'role_ids': role_ids,
    }

    signed_data = signing.dumps(data)
    url = settings.BOOKTYPE_URL + reverse('accounts:signin') + '?data=' + signed_data

    return url

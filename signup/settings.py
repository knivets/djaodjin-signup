# Copyright (c) 2015, Djaodjin Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
Convenience module for access of signup app settings, which enforces
default settings when the main settings module does not contain
the appropriate settings.

AWS_REGION       region used to create STS temporary credentials
AWS_UPLOAD_ROLE  role to assume in order to load directly from browser to S3
AWS_ACCOUNT_ID   account id for the role

DISABLED_AUTHENTICATION
    total lock down. A page will be displayed on login, registration,
    password reset, etc. but no new authentication can be performed.

DISABLED_REGISTRATION
   prevent new users from registering

"""

from django.conf import settings

_SETTINGS = {
    'AWS_REGION': None,
    'AWS_UPLOAD_ROLE': None,
    'AWS_ACCOUNT_ID': None,
    'DISABLED_AUTHENTICATION': False,
    'DISABLED_REGISTRATION': False,
    'LOGOUT_CLEAR_COOKIES' : None,
    'ACCOUNT_ACTIVATION_DAYS': getattr(settings, 'ACCOUNT_ACTIVATION_DAYS', 2),
    'DEFAULT_FROM_EMAIL': getattr(settings, 'DEFAULT_FROM_EMAIL')
}
_SETTINGS.update(getattr(settings, 'SIGNUP', {}))

AWS_REGION = _SETTINGS.get('AWS_REGION')
AWS_UPLOAD_ROLE = _SETTINGS.get('AWS_UPLOAD_ROLE')
AWS_ACCOUNT_ID = _SETTINGS.get('AWS_ACCOUNT_ID')
DISABLED_AUTHENTICATION = _SETTINGS.get('DISABLED_AUTHENTICATION')
DISABLED_REGISTRATION = _SETTINGS.get('DISABLED_REGISTRATION')
LOGOUT_CLEAR_COOKIES = _SETTINGS.get('LOGOUT_CLEAR_COOKIES')

DEFAULT_FROM_EMAIL = _SETTINGS.get('DEFAULT_FROM_EMAIL')
LOGIN_URL = getattr(settings, 'LOGIN_URL')
LOGIN_REDIRECT_URL = getattr(settings, 'LOGIN_REDIRECT_URL')

KEY_EXPIRATION = _SETTINGS.get('ACCOUNT_ACTIVATION_DAYS')
EMAIL_VERIFICATION_PAT = r'[a-f0-9]{40}'

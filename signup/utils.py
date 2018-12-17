# Copyright (c) 2018, DjaoDjin inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import logging, re

import boto3
from botocore.exceptions import ClientError
from django.apps import apps as django_apps
from django.core.exceptions import ImproperlyConfigured, NON_FIELD_ERRORS
from django.db import IntegrityError
from django.utils import six
from django.utils.translation import ugettext_lazy as _
import jwt
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.settings import api_settings
from hashlib import sha256

from . import settings
from .compat import User

LOGGER = logging.getLogger(__name__)


def get_accept_list(request):
    http_accept = request.META.get('HTTP_ACCEPT', '*/*')
    return [item.strip() for item in http_accept.split(',')]


def get_account_model():
    """
    Returns the ``Account`` model that is active in this project.
    """
    try:
        return django_apps.get_model(settings.ACCOUNT_MODEL)
    except ValueError:
        raise ImproperlyConfigured(
            "ACCOUNT_MODEL must be of the form 'app_label.model_name'")
    except LookupError:
        raise ImproperlyConfigured("ACCOUNT_MODEL refers to model '%s'"\
" that has not been installed" % settings.ACCOUNT_MODEL)


def has_invalid_password(user):
    return user.password.startswith('!')


def printable_name(user):
    full_name = user.get_full_name()
    if full_name:
        return full_name
    return user.username


def update_db_row(instance, form):
    """
    Updates the record in the underlying database, or adds a validation
    error in the form. When an error is added, the form is returned otherwise
    this function returns `None`.
    """
    try:
        try:
            instance.save()
        except IntegrityError as err:
            handle_uniq_error(err)
    except ValidationError as err:
        fill_form_errors(form, err)
        return form
    return None


def fill_form_errors(form, err):
    """
    Fill a Django form from DRF ValidationError exceptions.
    """
    if isinstance(err.detail, dict):
        for field, msg in six.iteritems(err.detail):
            if field in form.fields:
                form.add_error(field, msg)
            elif field == api_settings.NON_FIELD_ERRORS_KEY:
                form.add_error(NON_FIELD_ERRORS, msg)
            else:
                form.add_error(NON_FIELD_ERRORS,
                    _("No field '%(field)s': %(msg)s" % {
                    'field': field, 'msg': msg}))


def handle_uniq_error(err, renames=None):
    """
    Will raise a ``ValidationError`` with the appropriate error message.
    """
    field_name = None
    err_msg = str(err).splitlines().pop()
    # PostgreSQL unique constraint.
    look = re.match(
        r'DETAIL:\s+Key \(([a-z_]+)\)=\(.*\) already exists\.', err_msg)
    if look:
        field_name = look.group(1)
    else:
        look = re.match(
          r'DETAIL:\s+Key \(lower\(([a-z_]+)::text\)\)=\(.*\) already exists\.',
            err_msg)
        if look:
            field_name = look.group(1)
        else:
            # SQLite unique constraint.
            look = re.match(
                r'UNIQUE constraint failed: [a-z_]+\.([a-z_]+)', err_msg)
            if look:
                field_name = look.group(1)
    if field_name:
        if renames and field_name in renames:
            field_name = renames[field_name]
        raise ValidationError({field_name:
            _("This %(field)s is already taken.") % {'field': field_name}})
    raise err


def verify_token(token):
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            True, # verify
            options={'verify_exp': True},
            algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignature:
        raise serializers.ValidationError(
            _("Signature has expired."))
    except jwt.DecodeError:
        raise serializers.ValidationError(
            _("Error decoding signature."))
    username = payload.get('username', None)
    if not username:
        raise serializers.ValidationError(
            _("Missing username in payload"))
    # Make sure user exists
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        raise serializers.ValidationError(_("User does not exist."))
    return user


def upload_contact_picture(picture, slug):
    region = settings.AWS_REGION
    bucket = settings.AWS_S3_BUCKET_NAME
    client = boto3.client('s3', region_name=region)
    try:
        key = '%s.%s' % (sha256(slug.encode()).hexdigest(), 'jpg')
        res = client.put_object(Body=picture, Key=key, ACL='public-read',
            Bucket=bucket)
        if res['ResponseMetadata']['HTTPStatusCode'] == 200:
            return 'https://s3.%s.amazonaws.com/%s/%s' % (region, bucket,
                key)
    except ClientError as err:
        LOGGER.error('error while uploading picture: %s', err)
        raise serializers.ValidationError(_("error while uploading picture."))

# Copyright (c) 2019, Djaodjin Inc.
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

import logging

from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from ..mixins import UserMixin
from ..models import Credentials
from ..serializers import APIKeysSerializer, PublicKeySerializer


LOGGER = logging.getLogger(__name__)


class ResetAPIKeysAPIView(UserMixin, CreateAPIView):
    """
    Reset the secret API key with which a user can authenticate
    with the service.

    **Example

    .. code-block:: http

        POST /api/auth/keys/donny/  HTTP/1.1

    responds

    .. code-block:: json

        {
            "secret": "tgLwDw5ErQ2pQr5TTdAzSYjvZenHC9pSy7fB3sXWERzynbG5zG6h\
67pTN4dh7fpy"
        }

    """

    serializer_class = APIKeysSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data.get('password')
        if not request.user.check_password(password):
            raise PermissionDenied(_("Incorrect credentials"))
        allowed_chars = 'abcdefghjkmnpqrstuvwxyz'\
            'ABCDEFGHJKLMNPQRSTUVWXYZ'\
            '23456789'
        api_pub_key = get_random_string(
            length=Credentials.API_PUB_KEY_LENGTH,
            allowed_chars=allowed_chars)
        api_priv_key = get_random_string(
            length=Credentials.API_PRIV_KEY_LENGTH,
            allowed_chars=allowed_chars)
        Credentials.objects.update_or_create(
            user=self.user,
            defaults={
                'api_pub_key': api_pub_key,
                'api_priv_key': make_password(api_priv_key)
            })
        return Response(APIKeysSerializer().to_representation({
            'secret': api_pub_key + api_priv_key
        }), status=status.HTTP_201_CREATED)


class PublicKeyAPIView(UserMixin, GenericAPIView):
    """
    Update public key for a User

    **Example

    .. code-block:: http

        PUT /api/auth/pubkey/donny/  HTTP/1.1

    .. code-block:: json

        {
          "pubkey": "ssh-rsa AAAAB3N...",
          "password": "secret"
        }

    responds

    .. code-block:: json

        {
          "detail": "ok"
        }
    """
    serializer_class = PublicKeySerializer

    def put(self, request, *args, **kwargs):
        #pylint:disable=unused-argument
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data.get('password')
        if not request.user.check_password(password):
            raise PermissionDenied(_("Incorrect credentials"))
        try:
            self.user.set_pubkey(serializer.validated_data['pubkey'],
                bind_password=serializer.validated_data['password'])
            LOGGER.info("%s updated pubkey for %s.",
                self.request.user, self.user, extra={
                'event': 'update-pubkey', 'request': self.request,
                'modified': self.user.username})
        except AttributeError:
            raise ValidationError(
                'Cannot store public key in the User model.')
        except PermissionDenied as err:
            raise ValidationError(str(err))

        return Response({'detail': _("Public key updated successfully.")})

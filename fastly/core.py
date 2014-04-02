# Copyright 2014 Donald Stufft
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import absolute_import, division, print_function

import requests

from fastly.auth import KeyAuth, SessionAuth


class Fastly(object):

    def __init__(self, identifier, password=None):
        # Create a requests session to hold our settings and act as a
        # connection pool
        self._session = requests.session()

        if password is None:
            # Use KeyAuth because without a password we assume that we were
            # instantiated with an API key.
            self._session.auth = KeyAuth(identifier)
        else:
            # Use SessionAuth because when we're given a password we assume
            # that we're authenticating with user and password.
            self._session.auth = SessionAuth(
                identifier,
                password,
                self._session,
            )

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

from requests.auth import AuthBase
from six.moves import urllib_parse

from fastly.constants import API_DOMAIN


__all__ = ["KeyAuth"]


class KeyAuth(AuthBase):

    def __init__(self, key):
        self.key = key

    def __call__(self, request):
        # Add the Fastly-Key header
        request.headers["Fastly-Key"] = self.key

        return request


class SessionAuth(AuthBase):

    def __init__(self, user, password, session):
        self.user = user
        self.password = password
        self.session = session

        self.cookies = {}
        self.login_url = urllib_parse.urlunparse(
            ["https", API_DOMAIN, "/login", "", "", ""],
        )

    def __call__(self, request):
        # If we don't have any cookies stored for this request save some.
        if not self.cookies and request.url != self.login_url:
            self.login()

        # Add our cookies to this request
        request.prepare_cookies(self.cookies)

        # Attach a hook to handle 403 responses
        request.register_hook("response", self.handle_403)

        return request

    def login(self):
        # Log in to the site to get the cookies stored on the session
        resp = self.session.post(
            self.login_url,
            data={"user": self.user, "password": self.password},
        )
        resp.raise_for_status()
        self.cookies = resp.cookies.get_dict(API_DOMAIN)

    def handle_403(self, resp, **kwargs):
        # We only care about 403 responses, anything else we want to just
        # pass through the actual response
        if resp.status_code != 403:
            return resp

        # We weren't able to successfully complete the request, attempt to log
        # in again
        self.login()

        # Create a new request based off our old one
        request = resp.request.copy()
        request.prepare_cookies(self.cookies)

        # Get our new response
        new_resp = resp.connection.send(request, **kwargs)
        new_resp.history.append(resp)
        new_resp.request = request

        return new_resp

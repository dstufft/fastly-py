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

import pretend

from fastly.auth import KeyAuth, SessionAuth


def test_key_auth():
    request = pretend.stub(headers={})

    auth_obj = KeyAuth("1234")
    auth_obj(request)

    assert request.headers == {"Fastly-Key": "1234"}


def test_session_auth():
    request = pretend.stub(
        url="https://api.fastly.com/service",
        prepare_cookies=pretend.call_recorder(lambda cookies: None),
        register_hook=pretend.call_recorder(lambda event, func: None),
    )
    response = pretend.stub(
        cookies=pretend.stub(
            get_dict=pretend.call_recorder(
                lambda domain: {"fastly.session": "session data!"}
            ),
        ),
        raise_for_status=pretend.call_recorder(lambda: None),
    )
    session = pretend.stub(
        post=pretend.call_recorder(lambda url, data: response),
    )

    auth_obj = SessionAuth("test@example.com", "password", session)
    auth_obj(request)

    assert auth_obj.cookies == {"fastly.session": "session data!"}
    assert auth_obj.login_url == "https://api.fastly.com/login"

    assert request.prepare_cookies.calls == [
        pretend.call({"fastly.session": "session data!"}),
    ]
    assert request.register_hook.calls == [
        pretend.call("response", auth_obj.handle_403),
    ]

    assert response.cookies.get_dict.calls == [pretend.call("api.fastly.com")]
    assert response.raise_for_status.calls == [pretend.call()]

    assert session.post.calls == [
        pretend.call(
            "https://api.fastly.com/login",
            data={"user": "test@example.com", "password": "password"},
        ),
    ]


def test_session_auth_with_login():
    request = pretend.stub(
        url="https://api.fastly.com/login",
        prepare_cookies=lambda cookies: None,
        register_hook=lambda event, func: None,
    )
    session = pretend.stub()

    login = lambda: None  # pragma: no cover

    auth_obj = SessionAuth("test@example.com", "password", session)
    auth_obj.login = pretend.call_recorder(login)
    auth_obj.login
    auth_obj(request)

    assert auth_obj.login.calls == []


def test_session_auth_handle_response_200():
    response = pretend.stub(status_code=200)
    session = pretend.stub()

    auth_obj = SessionAuth("test@example.com", "password", session)

    assert auth_obj.handle_403(response) is response


def test_session_auth_handle_response_403():
    new_request = pretend.stub(prepare_cookies=lambda cookies: None)
    new_response = pretend.stub(history=[])

    response = pretend.stub(
        connection=pretend.stub(
            send=lambda request: new_response,
        ),
        request=pretend.stub(
            copy=lambda: new_request,
        ),
        status_code=403,
    )
    session = pretend.stub()

    auth_obj = SessionAuth("test@example.com", "password", session)
    auth_obj.login = pretend.call_recorder(lambda: None)

    resp = auth_obj.handle_403(response)

    assert auth_obj.login.calls == [pretend.call()]

    assert resp is new_response
    assert resp.history == [response]
    assert resp.request is new_request

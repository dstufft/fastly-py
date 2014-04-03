Usage
=====

Authentication
--------------

Fastly supports authentication both through an API key and through a user and
password pair. Using either method with fastly-py is very simple:

.. code-block:: pycon

    >>> import fastly
    >>> # Key based authentication
    >>> api = fastly.Fastly("a fake api key")
    >>> # User/password based authentication
    >>> api = fastly.Fastly("user@example.com", "p@ssw0rd")

import ssl
import rpyc

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.load_verify_locations(cafile="rootCA.pem")
ssl_context.load_cert_chain(certfile="client.crt", keyfile="client.key")


class SSLAuthenticator(object):
    """An implementation of the authenticator protocol for ``SSL``. The given
    socket is wrapped by ``ssl.SSLContext.wrap_socket`` and is validated based on
    certificates

    :param keyfile: the server's key file
    :param certfile: the server's certificate file
    :param ca_certs: the server's certificate authority file
    :param cert_reqs: the certificate requirements. By default, if ``ca_cert`` is
                      specified, the requirement is set to ``CERT_REQUIRED``;
                      otherwise it is set to ``CERT_NONE``
    :param ciphers: the list of ciphers to use, or ``None``, if you do not wish
                    to restrict the available ciphers. New in Python 2.7/3.2
    :param ssl_version: the SSL version to use

    Refer to `ssl.SSLContext <http://docs.python.org/dev/library/ssl.html#ssl.SSLContext>`_
    for more info.

    Clients can connect to this authenticator using
    :func:`rpyc.utils.factory.ssl_connect`. Classic clients can use directly
    :func:`rpyc.utils.classic.ssl_connect` which sets the correct
    service parameters.
    """

    def __init__(self, keyfile, certfile, ca_certs=None, cert_reqs=None,
                 ssl_version=None, ciphers=None):
        self.keyfile = str(keyfile)
        self.certfile = str(certfile)
        self.ca_certs = str(ca_certs) if ca_certs else None
        self.ciphers = ciphers
        if cert_reqs is None:
            if ca_certs:
                self.cert_reqs = ssl.CERT_REQUIRED
            else:
                self.cert_reqs = ssl.CERT_NONE
        else:
            self.cert_reqs = cert_reqs
        self.ssl_version = ssl_version

    def __call__(self, sock):
        try:
            if self.ssl_version is None:
                context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
            else:
                context = ssl.SSLContext(self.ssl_version)
            context.load_cert_chain(self.certfile, keyfile=self.keyfile)
            if self.ca_certs is not None:
                context.load_verify_locations(self.ca_certs)
            if self.ciphers is not None:
                context.set_ciphers(self.ciphers)
            if self.cert_reqs is not None:
                context.verify_mode = self.cert_reqs
            sock2 = context.wrap_socket(sock, server_side=True)
        except ssl.SSLError:
            ex = sys.exc_info()[1]
            raise AuthenticationError(str(ex))
        return sock2, sock2.getpeercert()

conn = rpyc.ssl_connect("server_hostname", port=12345, ssl_context=ssl_context)

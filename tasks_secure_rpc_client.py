def task_generate_root_key():
    """Generate the root CA private key."""
    return {
        "actions": ["openssl genrsa -out rootCA.key 4096"],
        "targets": ["rootCA.key"],
    }

def task_generate_root_cert():
    """Generate the root CA certificate."""
    return {
        "actions": [
            "openssl req -x509 -new -nodes -key rootCA.key -sha256 -days 1825 -out rootCA.pem"
        ],
        "file_dep": ["rootCA.key"],
        "targets": ["rootCA.pem"],
    }

def task_generate_server_key():
    """Generate the server private key."""
    return {
        "actions": ["openssl genrsa -out server.key 2048"],
        "targets": ["server.key"],
    }

def task_generate_server_csr():
    """Generate the server certificate signing request (CSR)."""
    return {
        "actions": ["openssl req -new -key server.key -out server.csr"],
        "file_dep": ["server.key"],
        "targets": ["server.csr"],
    }

def task_generate_server_csr_with_config():
    """Generate the server CSR using a configuration file."""
    return {
        "actions": ["openssl req -new -key server.key -out server.csr -config openssl.cnf"],
        "file_dep": ["server.key", "openssl.cnf"],
        "targets": ["server.csr"],
    }

def task_generate_server_cert():
    """Generate the server certificate."""
    return {
        "actions": [
            "openssl x509 -req -in server.csr -CA rootCA.pem -CAkey rootCA.key -CAcreateserial -out server.crt -days 825 -sha256"
        ],
        "file_dep": ["server.csr", "rootCA.pem", "rootCA.key"],
        "targets": ["server.crt", "rootCA.srl"],  # rootCA.srl is created by OpenSSL
    }

def task_generate_client_key():
    """Generate the client private key."""
    return {
        "actions": ["openssl genrsa -out client.key 2048"],
        "targets": ["client.key"],
    }

def task_generate_client_csr():
    """Generate the client CSR using a configuration file."""
    return {
        "actions": ["openssl req -new -key client.key -out client.csr -config openssl.cnf"],
        "file_dep": ["client.key", "openssl.cnf"],
        "targets": ["client.csr"],
    }

def task_generate_client_cert():
    """Generate the client certificate."""
    return {
        "actions": [
            "openssl x509 -req -in client.csr -CA rootCA.pem -CAkey rootCA.key -CAcreateserial -out client.crt -days 825 -sha256"
        ],
        "file_dep": ["client.csr", "rootCA.pem", "rootCA.key"],
        "targets": ["client.crt", "rootCA.srl"],  # rootCA.srl is reused
    }

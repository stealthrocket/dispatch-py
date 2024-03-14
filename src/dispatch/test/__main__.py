"""Mock Dispatch server for use in test environments.

Usage:
  dispatch.test <endpoint> [--api-key=<key>] [--hostname=<name>] [--port=<port>] [-v | --verbose]
  dispatch.test -h | --help

Options:
     --api-key=<key>      API key to require when clients connect to the server [default: test].

     --hostname=<name>    Hostname to listen on [default: 127.0.0.1].
     --port=<port>        Port to listen on [default: 4450].

  -v --verbose            Show verbose details in the log.
  -h --help               Show this help information.
"""

import base64
import logging
import sys

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from docopt import docopt

from dispatch.test import DispatchServer, DispatchService, EndpointClient


def main():
    args = docopt(__doc__)

    if args["--help"]:
        print(__doc__)
        exit(0)

    endpoint = args["<endpoint>"]
    api_key = args["--api-key"]
    hostname = args["--hostname"]
    port_str = args["--port"]

    try:
        port = int(port_str)
    except ValueError:
        print(f"error: invalid port: {port_str}", file=sys.stderr)
        exit(1)

    signing_key = Ed25519PrivateKey.generate()
    verification_key = base64.b64encode(
        signing_key.public_key().public_bytes_raw()
    ).decode()

    log_level = logging.DEBUG if args["--verbose"] else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    endpoint_client = EndpointClient.from_url(endpoint, signing_key=signing_key)

    with DispatchService(endpoint_client, api_key=api_key) as service:
        with DispatchServer(service, hostname=hostname, port=port) as server:
            print(f"Spawned a mock Dispatch server on {hostname}:{port}.")
            print()
            print("The Dispatch SDK can be configured with:")
            print()
            print(f'  export DISPATCH_API_URL="http://{hostname}:{port}"')
            print(f'  export DISPATCH_API_KEY="{api_key}"')
            print(f'  export DISPATCH_ENDPOINT_URL="{endpoint}"')
            print(f'  export DISPATCH_VERIFICATION_KEY="{verification_key}"')
            print()
            print(f"Listening on {hostname}:{port}")

            server.wait()


if __name__ == "__main__":
    main()

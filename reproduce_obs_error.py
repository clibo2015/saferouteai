
import http.client
import inspect
import ssl
import sys
import traceback
import os
from dotenv import load_dotenv

load_dotenv()

print(f"Python: {sys.version}")
try:
    print(f"HTTPSConnection signature: {inspect.signature(http.client.HTTPSConnection.__init__)}")
    print(f"HTTPConnection signature: {inspect.signature(http.client.HTTPConnection.__init__)}")
except Exception as e:
    print(f"Could not get signature: {e}")

print(f"Python: {sys.version}")
print(f"SSL: {ssl.OPENSSL_VERSION}")

import http.client

# Monkey patch for Python 3.12+ compatibility
# esdk-obs-python passes 'check_hostname' to HTTPSConnection, which was removed in 3.12
# We need to strip this argument before it reaches the real constructor
if sys.version_info >= (3, 12):
    _orig_init = http.client.HTTPSConnection.__init__
    
    def patched_init(self, host, port=None, key_file=None, cert_file=None,
                     timeout=http.client._CS_REQ_SENT,
                     source_address=None, *, context=None,
                     check_hostname=None, blocksize=8192):
        # Drop key_file, cert_file, check_hostname
        # Call original init with valid args
        if context is None and check_hostname is not None:
             # Try to handle check_hostname if context is missing? 
             # No, SDK usually passes context. If not, we ignore check_hostname safely.
             pass

        _orig_init(self, host, port=port, timeout=timeout,
                   source_address=source_address, context=context,
                   blocksize=blocksize)

    http.client.HTTPSConnection.__init__ = patched_init
    
    # Also patch if the SDK uses 'httplib' alias internally
    # (Not strictly needed if it imports the class, but good practice)
    
    import ssl
    if not hasattr(ssl, 'WRAP_SOCKET'):
        ssl.WRAP_SOCKET = 1

try:
    from obs import ObsClient
    print(f"HTTPConnection signature AFTER import: {inspect.signature(http.client.HTTPConnection.__init__)}")
except ImportError:
    print("OBS SDK not installed")
    sys.exit(1)

ak = os.getenv('HUAWEI_CLOUD_AK')
sk = os.getenv('HUAWEI_CLOUD_SK')
server = 'https://obs.af-south-1.myhuaweicloud.com'

print(f"Connecting to {server}...")

try:
    obs_client = ObsClient(
        access_key_id=ak,
        secret_access_key=sk,
        server=server
    )
    print("Client created.")
    
    print("Listing buckets...")
    resp = obs_client.listBuckets()
    print(f"Status: {resp.status}")
    if resp.status >= 300:
        print(f"Error: {resp.errorCode} - {resp.errorMessage}")

except Exception:
    traceback.print_exc()

import sys
import base64
import requests

# 1. Get a Setup Token
def claimAccessToken(setup_token):
    # 2. Claim an Access URL
    claim_url = base64.b64decode(setup_token)
    response = requests.post(claim_url)
    access_url = response.text
    return access_url

if len(sys.argv) != 2:
    print("Please provide a setup token")
    exit(1)

print(claimAccessToken(sys.argv[1]), end='')

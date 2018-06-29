import os
import requests

def JhipsterAuthenticate():
    url = "https://start.jhipster.tech/api/authenticate" 
    data = {"password":os.environ.get('JHIP_PASS'),"username":os.environ.get('JHIP_USERNAME'),"rememberMe":False}
    print data
    token = requests.post(url,json=data)
    print (token.text)

JhipsterAuthenticate()


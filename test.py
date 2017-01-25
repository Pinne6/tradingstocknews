#!/usr/bin/env python
# -*- coding: utf-8 -*-

from InstagramAPI import InstagramAPI
from yahoo_finance import Share

from rauth import OAuth1Service
import webbrowser


def getSession():
    # Create a session
    # Use actual consumer secret and key in place of 'foo' and 'bar'
    service = OAuth1Service(
        name='etrade',
        consumer_key='f1747b4f3196980e0aba6315c6949a15',
        consumer_secret='5429d23a9c0d3087f5a2c8faec639074',
        request_token_url='https://etws.etrade.com/oauth/request_token',
        access_token_url='https://etws.etrade.com/oauth/access_token',
        authorize_url='https://us.etrade.com/e/t/etws/authorize?key={}&token={}',
        base_url='https://etws.etrade.com')

    # Get request token and secret
    oauth_token, oauth_token_secret = service.get_request_token(params=
                                                                {'oauth_callback': 'oob',
                                                                 'format': 'json'})

    auth_url = service.authorize_url.format('f1747b4f3196980e0aba6315c6949a15', oauth_token)

    # Get verifier (direct input in console, still working on callback)
    webbrowser.open(auth_url)
    verifier = input('Please input the verifier: ')

    return service.get_auth_session(oauth_token, oauth_token_secret, params={'oauth_verifier': verifier})


# Create a session
session = getSession()

# After authenticating a session, use sandbox urls
url = 'https://etwssandbox.etrade.com/accounts/sandbox/rest/accountlist.json'

resp = session.get(url, params={'format': 'json'})

print(resp)
exit()
yahoo = Share('FCA.MI')
print(yahoo.get_price())
print(yahoo.get_trade_datetime())
exit()

InstagramAPI = InstagramAPI("tradingstocknews", "sto23espo")
InstagramAPI.login()  # login
InstagramAPI.uploadPhoto('test.jpg', '#prova')
InstagramAPI.logout()
# InstagramAPI.tagFeed("cat") # get media list by tag #cat
# media_id = InstagramAPI.LastJson # last response JSON
# InstagramAPI.like(media_id["ranked_items"][0]["pk"]) # like first media
# InstagramAPI.getUserFollowers(media_id["ranked_items"][0]["user"]["pk"]) # get first media owner followers

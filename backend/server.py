# server.py
import os
from livekit import api
from flask import Flask

app = Flask(__name__)

@app.route('/getToken')
def getToken():
  token = api.AccessToken('APIA3VyTQtGN3Rf', 'E4jXhGQGC2g5GNEzHd3dntaF6hGlAHifujOnvlvYOyB') \
    .with_identity("identity") \
    .with_name("my name") \
    .with_grants(api.VideoGrants(
        room_join=True,
        room="my-room",
    ))
  print(token.to_jwt)
  return token.to_jwt()

if __name__ == '__main__':
        app.run(debug=True)

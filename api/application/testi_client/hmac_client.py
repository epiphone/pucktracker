from client import app
app.config["OAUTH_CREDENTIALS"] = {
    u"client_secret": "x4onqvgIOh3ts4GmAN0KaYsabxqSKI"
}
app.config["CLIENT_KEY"] = "BNfYJ4djO9oniI2uNRH4X9mrA2Us7M"
app.run(debug=True, host="0.0.0.0", port=5001)

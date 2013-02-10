from gaesessions import SessionMiddleware
def webapp_add_wsgi_middleware(app):
    app = SessionMiddleware(app, cookie_key="94dc5b30eca02494b9djoicd2q094x54ao4rkuc9av7tyo5tsv4c9")
    return app

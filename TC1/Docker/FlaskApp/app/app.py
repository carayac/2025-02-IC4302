from flask import Flask
import os
app = Flask(__name__)

@app.route("/")
def hello_world():
    DATA=os.getenv('PROMETHEUSENDPOINT')
    return "<p>Hello, "+ DATA +"World!</p>"

@app.route("/mariadb")
def mariadb():
    return "<p>Hello, MariaDB World!</p>"
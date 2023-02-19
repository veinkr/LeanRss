# coding: utf-8
import sys
from datetime import datetime

import leancloud
from flask import Flask, jsonify
from flask_sockets import Sockets


app = Flask(__name__)
sockets = Sockets(app)


@app.route('/')
def index():
    return "Hello, Rss"
git config --global user.email "yhf2lj@gmail.com"
  git config --global user.name "veinkr"
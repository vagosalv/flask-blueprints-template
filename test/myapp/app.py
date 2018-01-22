import os
import config
import pymysql
import pymysql.cursors
import mysql.connector
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from myapp.views import blueprints
#from flask import blueprints





def create_app():

	app = Flask(__name__)

	# TBD proper config here
	APP_URL_PREFIX = os.environ.get('MY_APP_PREFIX',None)

	for bp in blueprints:
		app.register_blueprint(bp,url_prefix=APP_URL_PREFIX)


	return app


app = create_app()






def connect_db(db):
	if db!= config.DATABASE_CONFIG['db']:
		raise ValueError("Couldnt find database with that name")
	conn = pymysql.connect(
		host=config.DATABASE_CONFIG['host'],
    	user=config.DATABASE_CONFIG['user'],
    	password=config.DATABASE_CONFIG['password'],
    	db=config.DATABASE_CONFIG['db'],
    	cursorclass=config.DATABASE_CONFIG['cursorclass']
		)
	connect_db('myflaskapp')
	cursor = conn.cursor()
	return conn



if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)

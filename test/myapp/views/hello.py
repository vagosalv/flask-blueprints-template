import os
from app import app
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

from flask import Blueprint


hello = Blueprint('hello',__name__)

# Config MySQL
hello.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '987654321vagos'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)




@hello.route('/')
def index_page():
	return render_template('home.html')	

#About
@hello.route('/about')
def about():
    return render_template('about.html')


#Articles
@hello.route('/articles')
def articles():
    #Create cursor
    cur = mysql.connection.cursor()
    #Get Articles
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    if result > 0 :
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No articles Found'
        return render_template('articles.html', msg=msg)
    #close connection
    cur.close()


# Gia otan anoigw to article na emfanizei to swsto periexomeno
@hello.route('/article/<string:id>/')
def article(id):
    #Create cursor
    cur = mysql.connection.cursor()
    #Get Article
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])
    #Commit
    article = cur.fetchone()
    def comments(id):
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM comments WHERE article.id = %s", [article.id])
        comment = cur.fetchone()
        return render_template('article.html', comment=comment)
    return render_template('article.html', article=article)



#klash gia elenxo ths formas
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

#User register
@hello.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash ('You are now registered and can log in', 'Success')

        redirect(url_for('index'))


        return redirect(url_for('login'))
    return render_template('register.html', form = form)


#User login
@hello.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        #Get form fields
        username = request.form['username']
        password_candidate = request.form['password']
        #Create cursor
        cur = mysql.connection.cursor()
        #Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s" , [username])

        if result > 0:
            #Get stored hash
            data = cur.fetchone()
            password = data['password']

            #Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                #Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error )
            #close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error )


    return render_template('login.html')

#Check if user is logged_in (snippet)
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap


#Logout
@hello.route('/logout')
@is_logged_in
def logaout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


#Dashboard
@hello.route('/dashboard')
@is_logged_in
def dashboard():
    #Create cursor
    cur = mysql.connection.cursor()
    #Get Articles
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    if result > 0 :
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No articles Found'
        return render_template('dashboard.html', msg=msg)
    #close connection
    cur.close()



#Articles Form class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=10)])


#Add article
@hello.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data
        #Create cursor
        cur = mysql.connection.cursor()
        #execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))
        #commit
        mysql.connection.commit()
        #close connection
        cur.close()
        flash('Article created', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)

#Edit article
@hello.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    #create cursor
    cur = mysql.connection.cursor()
    #get article by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s",[id])
    article = cur.fetchone()
    #Get form
    form = ArticleForm(request.form)
    #populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']
        #Create cursor
        cur = mysql.connection.cursor()
        #execute
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id =%s",(title, body, id))
        #commit
        mysql.connection.commit()
        #close connection
        cur.close()
        flash('Article Updated', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

#Delete article
@hello.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    #create cursor
    cur = mysql.connection.cursor()
    #execute
    cur.execute("DELETE FROM articles WHERE id = %s", [id])
    #commit
    mysql.connection.commit()
    #close connection
    cur.close()
    flash('Article Deleted', 'success')
    return redirect(url_for('dashboard'))

#Commnts Form class
class CommentForm(Form):
    body = TextAreaField('Body', [validators.Length(min=10)])

#Articles
@hello.route('/comments')
def comments():
    #Create cursor
    cur = mysql.connection.cursor()
    #Get Articles
    result = cur.execute("SELECT * FROM comments")
    comments = cur.fetchall()
    if result > 0 :
        return render_template('comments.html', comments=comments)
    else:
        msg = 'No comments Found'
        return render_template('comments.html', msg=msg)
    #close connection
    cur.close()


#gia otan anoigw to article na emfanizontai ta swsta comments
@hello.route('/comment/<string:id>/')
def comment(id):
    #Create cursor
    cur = mysql.connection.cursor()
    #Get Comment
    result = cur.execute("SELECT * FROM comments WHERE id = %s", [id])
    comment = cur.fetchone()
    return render_template('comment.html', comment=comment)


#Add comment
@hello.route('/add_comments', methods=['GET', 'POST'])
@is_logged_in
def add_comment():

    form = CommentForm(request.form)
    if request.method == 'POST' and form.validate():
        body = form.body.data
        #Create cursor
        cur = mysql.connection.cursor()
        #execute
        cur.execute("INSERT INTO comments(author, body, article_id) VALUES(%s, %s, %s)", (session['username'], body, 1))
        #commit
        mysql.connection.commit()
        #close connection
        cur.close()
        flash('Comment created', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_comments.html', form=form)






#Edit comment
@hello.route('/edit_comment/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_comment(id):
    #create cursor
    cur = mysql.connection.cursor()
    #get comment by id
    result = cur.execute("SELECT * FROM comments WHERE id = %s",[id])
    comment = cur.fetchone()
    #Get form
    form = CommentForm(request.form)
    #populate comment form fields
    form.body.data = comment['body']

    if request.method == 'POST' and form.validate():
        body = request.form['body']
        #Create cursor
        cur = mysql.connection.cursor()
        #execute
        cur.execute("UPDATE comments SET  body=%s WHERE id =%s",( body, id))
        #commit
        mysql.connection.commit()
        #close connection
        cur.close()
        flash('Comment Updated', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_comment.html', form=form)

#Delete article
@hello.route('/delete_comment/<string:id>', methods=['POST'])
@is_logged_in
def delete_comment(id):
    #create cursor
    cur = mysql.connection.cursor()
    #execute
    cur.execute("DELETE FROM comments WHERE id = %s", [id])
    #commit
    mysql.connection.commit()
    #close connection
    cur.close()
    flash('Comment Deleted', 'success')
    return redirect(url_for('dashboard'))



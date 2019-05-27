from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import jinja2
import re

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja2_env = jinja2.Environment(loader = jinja2.FileSystemLoader
(template_dir), autoescape=True)

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:blogz45@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = b'\xdfH\x96V\xaf\xc7'


class Blogz(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.Text, nullable=False)
    pub_date = db.Column(db.DateTime)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner, pub_date=None):
        self.title = title
        self.body = body
        self.owner = owner
        if pub_date is None:
            pub_date = datetime.utcnow()
        self.pub_date = pub_date


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))

    blogs = db.relationship('Blogz', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password


@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'index', 'blog']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')


@app.route('/')
def index():
    users = User.query.all()
    return render_template('index.html', users=users, header='Blog Users')


@app.route('/blog')
def blog():
    posts = Blogz.query.all()
    blog_id = request.args.get('id')
    user_id = request.args.get('user')

    if user_id == None:
        posts = Blogz.query.fliter_by(owner_id=user_id)
        return render_template('user.html', posts=posts, header='User Posts')
    if blog_id:
        posts = Blogz.query.get(blog_id)
        return render_template('user.html', posts=posts)

    return render_template('blog.html', posts=posts, header='All Blog Posts')


@app.route('/newpost', methods=['POST', 'GET'])
def new_post():
    owner = User.query.filter_by(username=session['username']).first()

    if request.method == 'POST':
        blog_title = request.form['blog-title']
        blog_body = request.form['blog-entry']
        title_error = ''
        body_error = ''

        if not blog_title:
            title_error = "Please enter a blog title"
        if not blog_body:
            body_error = "Please enter a blog entry"

        if not body_error and not title_error:
            new_entry = Blogz(blog_title, blog_body)
            db.session.add(new_entry)
            db.session.commit()
            return redirect('/blog?id={}'.format(new_entry.id))
        else:
            return render_template('newpost.html', header='New Entry', title_error=title_error, body_error=body_error,
                                   blog_title=blog_title, blog_body=blog_body)

    return render_template('newpost.html', header='New Blog Entry')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['username'] = username
            flash("Logged in")
            return redirect('/newpost')
        else:
            flash('User password incorrect, or user does not exists', 'error')
            #return '<h1>Error!</h1>'

    return render_template('login.html', header='Login')


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify_password = request.form['verify_password']

        existing_user = User.query.filter_by(username=username).first()

        if password != verify_password:
            flash('Password does not match', "error")
        elif len(username) < 3 or len(password) < 3:
            flash('Username and password must be more than 3 characters', 'error')
        elif existing_user:
            flash('User already exists', 'error')
        else:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/newpost')

    
    return render_template('signup.html', header='Signup')

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog')


if __name__ == "__main__":
    app.run()

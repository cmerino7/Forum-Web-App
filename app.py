from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from flask_bcrypt import Bcrypt
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import InputRequired, Length, ValidationError

import os

app = Flask(__name__)
CORS(app)

courses = os.path.abspath(os.path.dirname(__file__)) 

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(courses, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'EldenRing'

salt = "SUPERSECRET" 

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

db = SQLAlchemy(app)
bcrypt = Bcrypt(app) 

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    choice = db.Column(db.String, nullable = False)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
    replies_id = db.Column('replies_id', db.Integer, db.ForeignKey('replies.id'))
    replies = db.relationship('Replies', back_populates = 'user_votes')
    user = db.relationship('User', back_populates = 'post_votes')

class Post(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String)
    posts = db.Column(db.Text)
    reply = db.relationship('Replies', backref = 'post')

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String, unique = True, nullable = False)
    username = db.Column(db.String, unique = True, nullable = False)
    password = db.Column(db.String, nullable = False)
    post_votes = db.relationship('Vote', back_populates='user')

class Replies(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    posts = db.Column(db.Text)
    name = db.Column(db.String)
    likes = db.Column(db.Integer)
    response = db.Column(db.Integer, db.ForeignKey('post.id'))
    user_votes = db.relationship('Vote', back_populates='replies')
    
class RegisterForm(FlaskForm):
    name = StringField(validators = [InputRequired(), Length(min = 4, max = 20)], render_kw={"placeholder" : "name"})
    username = StringField(validators = [InputRequired(), Length(min = 4, max = 20)], render_kw={"placeholder" : "username"})
    password = PasswordField(validators = [InputRequired(), Length(min = 4, max = 20)], render_kw={"placeholder" : "password"})
    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username = username.data).first()
        if existing_user_username:
            raise ValidationError("That username already exists. Please choose a different one.") 

@app.route('/register', methods = ['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data + salt)
        new_user = User(name = form.name.data, username = form.username.data, password = hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('Register.html', form = form)

@app.route('/login', methods = ['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if User.query.filter_by(username = form.username.data).first():
            user = User.query.filter_by(username = form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data + salt):
                login_user(user)
                return redirect(url_for('dashboard'))
    return render_template('login.html', form = form)

@app.route('/logout', methods = ['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

class LoginForm(FlaskForm):
    username = StringField(validators = [InputRequired(), Length(min = 4, max = 20)], render_kw={"placeholder" : "username"})
    password = PasswordField(validators = [InputRequired(), Length(min = 4, max = 20)], render_kw={"placeholder" : "password"})
    submit = SubmitField("Login")
    
@app.route('/about', methods = ['GET'])
def aboot():
    return render_template('about.html')

@app.route('/dashboard', methods = ['GET'])
@login_required
def dashboard():
    preguntas = Post.query.filter_by().all()
    return render_template('dashboard.html', preguntas = preguntas)

@app.route('/question', methods = ['GET', 'POST'])
@login_required
def question():
    if(request.method == 'GET'):
        return render_template('question.html')
    elif(request.method == 'POST'):
        post = request.form['askquestion']
        stuff = User.query.filter_by(id = current_user.id).first()
        input = Post(posts = post, name = stuff.name)
        db.session.add(input)
        db.session.commit()
        return redirect(url_for('dashboard'))

@app.route('/response/<int:question_id>', methods = ['GET', 'POST'])
@login_required
def response(question_id):
    questions = Post.query.get_or_404(question_id)
    replys = Replies.query.filter_by(response = question_id).all()
    if(request.method == 'GET'):
        return render_template('response.html', questions = questions, replys = replys)
    elif(request.method == 'POST'):
        person = User.query.filter_by(id = current_user.id).first()
        temp = request.form['answer']
        stuff = Replies(posts = temp, name = person.name, likes = 0, post = questions)
        db.session.add(stuff)
        db.session.commit()
        return redirect( url_for('response'))

@app.route('/upvote/<int:reply>/<string:truthfullness>', methods = ['GET'])
def upvote(reply, truthfullness):
    truthfullness = str(truthfullness)
    if not Vote.query.filter_by(user_id = current_user.id, replies_id = reply).first():
        if truthfullness == 'True':
            user_id = User.query.filter_by(id = current_user.id).first()
            post_id = Replies.query.filter_by(id = reply).first()
            brakeance = Vote(choice = 'True', user_id = user_id.id, replies_id = post_id.id)
            post_id.likes = post_id.likes + 1
            db.session.add(brakeance)
            db.session.commit()
            return redirect ( url_for('response', question_id = post_id.response))
        elif truthfullness == 'False':
            user_id = User.query.filter_by(id = current_user.id).first()
            post_id = Replies.query.filter_by(id = reply).first()
            brakeance = Vote(choice = 'False', user_id = user_id.id, replies_id = post_id.id)
            post_id.likes = post_id.likes - 1
            db.session.add(brakeance)
            db.session.commit()
            return redirect ( url_for('response', question_id = post_id.response))
    else:
        check = Vote.query.filter_by(user_id = current_user.id, replies_id = reply).first()
        if check.choice == truthfullness:
            post_id = Replies.query.filter_by(id = reply).first()
            flash("Sorry, but you've already voted on this", "info")
            return redirect ( url_for('response', question_id = post_id.response))
        else:
            if truthfullness == 'True':
                post_id = Replies.query.filter_by(id = reply).first()
                post_id.likes = post_id.likes + 2
                check.choice = 'True'
                db.session.commit()
                return redirect ( url_for('response', question_id = post_id.response))
            else:
                post_id = Replies.query.filter_by(id = reply).first()
                post_id.likes = post_id.likes - 2
                check.choice = 'False'
                db.session.commit()
                return redirect ( url_for('response', question_id = post_id.response))


@app.route('/find', methods = ['POST'])
@login_required
def find():
    temp = request.form['filtered']
    scope = Post.query.filter(Post.posts.contains(temp))
    return render_template('find.html', preguntas = scope, result=temp)

@app.route("/")
def home():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)

with app.app_context():
    db.create_all()
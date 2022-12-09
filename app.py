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

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

db = SQLAlchemy(app)
bcrypt = Bcrypt(app) 

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String, unique = True, nullable = False)
    username = db.Column(db.String, unique = True, nullable = False)
    password = db.Column(db.String, nullable = False)
    def __repr__(self):
        return f'Student: {self.name}'   

class Post(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String)
    posts = db.Column(db.Text)
    likes = db.Column(db.Integer)
    reply = db.relationship('Replies', backref = 'post')

class Replies(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    posts = db.Column(db.Text)
    name = db.Column(db.String)
    likes = db.Column(db.Integer)
    response = db.Column(db.Integer, db.ForeignKey('post.id'))
    
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
        hashed_password = bcrypt.generate_password_hash(form.password.data)
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
            if bcrypt.check_password_hash(user.password, form.password.data):
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
        input = Post(posts = post, name = stuff.name, likes = 0)
        db.session.add(input)
        db.session.commit()
        return redirect(url_for('dashboard'))

@app.route('/response/<int:question_id>', methods = ['GET', 'POST'])
@login_required
def response(question_id):
    questions = Post.query.get_or_404(question_id)
    replys = Replies.query.filter_by().all()
    if(request.method == 'GET'):
        return render_template('response.html', questions = questions, replys = replys)
    elif(request.method == 'POST'):
        person = User.query.filter_by(id = current_user.id).first()
        temp = request.form['answer']
        stuff = Replies(posts = temp, name = person.name, likes = 0, post = questions)
        db.session.add(stuff)
        db.session.commit()
        return redirect( url_for('dashboard'))

@app.route('/find', methods = ['POST'])
@login_required
def find():
    temp = request.form['filtered']
    scope = Post.query.filter(Post.posts.contains(temp))
    return render_template('find.html', preguntas = scope)

@app.route("/")
def home():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)

with app.app_context():
    db.create_all()

'''
@app.route('/student', methods = ['GET'])
@login_required
def student():
    classes = Icarus.query.filter_by(user_id = current_user.id).all() 
    return render_template('student_page.html', classes = classes)

@app.route('/instructor', methods = ['GET'])
@login_required
def instructor():
    instructorName = request.args.get('name') 
    instructorID = request.args.get('ID') 
    taughtClasses = Course.query.filter_by(teacher=instructorName).all()
    return render_template('instructor_page.html', displayName=instructorName, id=instructorID, courses=taughtClasses)

@app.route('/<int:id>/<string:className>', methods = ['POST'])
def changeGrade(id,className):
    #get current Teacher id and Course
    currentTeacher = Teacher.query.filter_by(id=id).first()
    thisClass = Course.query.filter_by(course_id=className).first() #query of Classes matching classname e.g. CSE106 
    #get new grade from student and their name from frontend
    newGrade = request.form.get("newGrade")
    selectedName = request.form.get("selectedName")
    #update db 
    selectStudentQuery = User.query.filter_by(name=selectedName).first() #create query of selected student
    selectGradeQuery = Roster.query.filter_by(user_id=selectStudentQuery.id).first() #get matching student id
    # selectGradeQuery = Enrollment.query.filter_by(student_id=selectStudentQuery.id, class_id=thisClass.id).first()
    selectGradeQuery.grade = newGrade
    db.session.commit()
    nameGradeTable = User.query.join(Roster, Roster.user_id==User.id).add_columns(User.name, Roster.grade).filter_by(class_id=thisClass.id).all()
    return render_template('class_1.html', course=thisClass, names=nameGradeTable, ID=id, displayName=currentTeacher)

    
@app.route('/<int:id>/<string:className>', methods = ['GET'])
# @login_required
def coursesTaught(id,className):
    currentTeacher = Teacher.query.filter_by(id=id).first()
    thisClass = Course.query.filter_by(course_id=className).first() #query of Classes matching classname e.g. CSE106 
    nameGradeTable = User.query.join(Roster, Roster.user_id==User.id).add_columns(User.name, Roster.grade).filter_by(class_id=thisClass.id).all()
    return render_template('class_1.html', course=thisClass, names=nameGradeTable, displayName=currentTeacher)

@app.route('/add', methods = ['GET', 'POST'])
@login_required
def add():
    if(request.method == "GET"):
        print("\n\n\n",current_user.id,"current_user")
        return render_template('add_courses.html', students = Course.query.all())
    if(request.method == "POST"):
        row = request.form.get("Add")
        one = User.query.filter_by(id = current_user.id).first()
        two = Course.query.filter_by(id = row).first()
        if(two.capacity == two.enrollment):
            flash("Sorry, but this class is full", "info")
            return redirect(url_for('add'))
        two.enrollment = two.enrollment + 1
        db.session.commit()
        three = Teacher.query.filter_by(name = two.teacher).first()
        new_course = Roster(user = one, course = two, grade = "null")
        new_scheduele = Icarus(user = one, course = two, class_name = two.course_id, teacher = two.teacher, time = two.time, enrollment = two.enrollment, capacity = two.capacity)
        new_student = Attendance(user = one, teacher = three)
        db.session.add(new_course) 
        db.session.add(new_student) 
        db.session.add(new_scheduele)
        db.session.commit()
        flash("Class added!", "info")
        return redirect(url_for('add'))
'''
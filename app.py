''''
Author: Dhanu Sree Suresh
Description: This project is a complete exam preparation platform, providing resources and tools to help users study efficiently.
'''

# Improting the required packages
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import matplotlib.pyplot as plt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quizmaster.sqlite3'
db = SQLAlchemy(app)

# Creation of Database Schema

class User(db.Model):
    u_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique = True, nullable = False)
    password = db.Column(db.String(200), nullable = False)
    fname = db.Column(db.String(200))
    qualification = db.Column(db.String(200))
    dob = db.Column(db.Date)
    scores = db.relationship('Score', backref='user')

class Admin(db.Model):
    a_id = db.Column(db.Integer, primary_key = True)
    uname = db.Column(db.String(200), unique = True, nullable = False)
    password = db.Column(db.String(200), nullable = False)

class Subject(db.Model):
    s_id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(200), nullable = False)
    description = db.Column(db.Text)
    chapters = db.relationship('Chapter', backref='subject')

class Chapter(db.Model):
    c_id = db.Column(db.Integer, primary_key = True)
    s_id = db.Column(db.Integer, db.ForeignKey("subject.s_id"), nullable = False)
    name = db.Column(db.String(200), nullable = False)
    description = db.Column(db.Text)
    quizzes = db.relationship('Quiz', backref='chapter')

class Quiz(db.Model):
    q_id = db.Column(db.Integer, primary_key = True)
    c_id = db.Column(db.Integer, db.ForeignKey("chapter.c_id"), nullable = False)
    title = db.Column(db.String(200), nullable = False)
    q_date = db.Column(db.DateTime, default = datetime.now)
    duration = db.Column(db.String(8))
    remarks = db.Column(db.Text)
    scores = db.relationship('Score', backref='quiz')
    questions = db.relationship('Question', backref='quiz')

class Question(db.Model):
    qs_id =  db.Column(db.Integer, primary_key = True)
    q_id = db.Column(db.Integer, db.ForeignKey("quiz.q_id"))
    ques = db.Column(db.Text, nullable = False)
    opt1 = db.Column(db.String(200))
    opt2 = db.Column(db.String(200))
    opt3 = db.Column(db.String(200))
    opt4 = db.Column(db.String(200))
    answer = db.Column(db.Integer, nullable = False)

class Score(db.Model):
    sc_id = db.Column(db.Integer, primary_key = True)
    q_id = db.Column(db.Integer, db.ForeignKey("quiz.q_id"), nullable = False)
    u_id = db.Column(db.Integer, db.ForeignKey("user.u_id"), nullable = False)
    score = db.Column(db.Integer)
    time = db.Column(db.DateTime, default = datetime.now)

with app.app_context():
    db.create_all()

# Route Creation

# General Routes

# Home Page
@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user_type = request.form['user_type']
        _email = request.form['email']
        password = request.form['password']

        if user_type == 'admin':
            admin = Admin.query.filter_by(uname = _email, password = password).first()
            if admin:
                response = redirect('/admin/dashboard')
                response.set_cookie('admin_id', str(admin.a_id))
                return response
            error = 'Invalid admin credentials'
        else:
            user = User.query.filter_by(email = _email, password = password).first()
            if user:
                response = redirect('/user/dashboard')
                response.set_cookie('user_id', str(user.u_id))
                return response
            error = 'Invalid user credentials'
    return render_template('login.html', error = error)

# Logging Out
@app.route('/logout')
def logout():
    response = redirect('/login')
    response.set_cookie('user_id', '', expires = 0)
    response.set_cookie('admin_id', '', expires = 0)
    return response

# Creating Account
@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        qualification = request.form.get('qualification')
        dob = request.form.get('dob')
        if not email or not password or not full_name:
            return render_template('register.html', error = 'Email, password, and full name are required', email = email, full_name = full_name, qualification = qualification, dob = dob)
        if User.query.filter_by(email=email).first():
            return render_template('register.html', error = 'Email already registered', email = email, full_name = full_name, qualification = qualification, dob = dob)
        try:
            new_user = User(email = email, password = password, fname = full_name, qualification = qualification, dob = datetime.strptime(dob, '%Y-%m-%d').date() if dob else None)
            db.session.add(new_user)
            db.session.commit()
            res = redirect('/user/dashboard')
            res.set_cookie('user_id', str(new_user.u_id))
            return res
        except Exception as e:
            db.session.rollback()
            return render_template('register.html', error = 'Registration failed. Please try again.', email = email, full_name = full_name, qualification = qualification, dob = dob)
    return render_template('register.html')

# Routes for Admin

# Admin Dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    if not request.cookies.get('admin_id'):
        return redirect('/login')
    
    stats = {'user_count': User.query.count(), 'subject_count': Subject.query.count(), 'quiz_count': Quiz.query.count(), 'active_quiz_count': Quiz.query.filter(Quiz.q_date <= datetime.now()).count()}
    return render_template('admin.html', stats = stats)

# Quiz Related Routes

# Quizzes Dashboard - Admin
@app.route('/admin/quizzes')
def admin_quizzes():
    if not request.cookies.get('admin_id'):
        return redirect('/login')
    try:
        quizzes = Quiz.query.options(db.joinedload(Quiz.chapter).joinedload(Chapter.subject)).all()
        subjects = Subject.query.all()
        chapters = Chapter.query.all()
        return render_template('admin_quiz.html', quizzes=quizzes, subjects = subjects, chapters = chapters)
    except Exception as e:
        print("Database Error:", str(e))
        return render_template('admin_quiz.html', error="Failed to load quizzes")

# Editing Quizzes
@app.route('/admin/quizzes/edit/<int:q_id>', methods=['GET', 'POST'])
def edit_quiz(q_id):
    if not request.cookies.get('admin_id'):
        return redirect('/login')
    
    quiz = Quiz.query.get_or_404(q_id)
    chapters = Chapter.query.all()
    
    if request.method == 'POST':
        quiz.title = request.form['title']
        quiz.c_id = request.form['chapter_id']
        quiz.q_date = datetime.strptime(request.form['date_of_quiz'], '%Y-%m-%d')
        quiz.duration = request.form['time_duration']
        quiz.remarks = request.form['remarks']
        db.session.commit()
        return redirect('/admin/quizzes')
    
    return render_template('edit_quiz.html', quiz=quiz, chapters=chapters)

# Deleting Quizzes
@app.route('/admin/quizzes/delete/<int:q_id>', methods=['POST'])
def delete_quiz(q_id):
    if not request.cookies.get('admin_id'):
        return redirect('/login')
    
    quiz = Quiz.query.get_or_404(q_id)
    Question.query.filter_by(q_id=q_id).delete()
    Score.query.filter_by(q_id=q_id).delete()
    db.session.delete(quiz)
    db.session.commit()
    return redirect('/admin/quizzes')

# Subjects
@app.route('/admin/subjects', methods = ['GET', 'POST'])
def manage_subjects():
    if not request.cookies.get('admin_id'):
        return redirect('/login')
    
    error = None
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        new_subject = Subject(name = name, description = description)
        db.session.add(new_subject)
        db.session.commit()
        return redirect('/admin/subjects')
    
    subjects = Subject.query.all()
    return render_template('subject.html', subjects = subjects, error = error)

# Chapter Creation
@app.route('/admin/subjects/<int:s_id>/chapters/add', methods = ['GET', 'POST'])
def add_chapter(s_id):
    if not request.cookies.get('admin_id'):
        return redirect('/login')
    
    subject = Subject.query.get_or_404(s_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            return render_template('chapter.html', 
                                subject=subject, 
                                error='Chapter name is required')
        
        try:
            new_chapter = Chapter(
                s_id=s_id,
                name=name,
                description=description
            )
            db.session.add(new_chapter)
            db.session.commit()
            return redirect(f'/admin/subjects')
        except Exception as e:
            db.session.rollback()
            return render_template('chapter.html', 
                                subject=subject, 
                                error=f'Failed to add chapter: {str(e)}')
    
    return render_template('chapter.html', subject=subject)
# Edit Subject 
@app.route('/admin/subjects/edit/<int:s_id>', methods = ['GET', 'POST'])
def edit_subject(s_id):
    if not request.cookies.get('admin_id'):
        return redirect('/login')
    
    subject = Subject.query.get_or_404(s_id)
    
    if request.method == 'POST':
        try:
            subject.name = request.form.get('name', subject.name)
            subject.description = request.form.get('description', subject.description)
            db.session.commit()
            return redirect('/admin/subjects')
        except Exception as e:
            db.session.rollback()
            return render_template('edit_subject.html', 
                                 subject=subject, 
                                 error=f"Error updating subject: {str(e)}")
    
    return render_template('edit_subject.html', subject=subject)

# Delete Subject
@app.route('/admin/subjects/delete/<int:s_id>', methods = ['POST'])
def delete_subject(s_id):
    if not request.cookies.get('admin_id'):
        return redirect('/login')
    
    try:
        subject = Subject.query.get_or_404(s_id)
        
        chapters = Chapter.query.filter_by(s_id=s_id).all()
        for chapter in chapters:
            quizzes = Quiz.query.filter_by(c_id=chapter.c_id).all()
            for quiz in quizzes:
                Question.query.filter_by(q_id=quiz.q_id).delete()
                Score.query.filter_by(q_id=quiz.q_id).delete()
                db.session.delete(quiz)
            db.session.delete(chapter)
        
        db.session.delete(subject)
        db.session.commit()
        return redirect('/admin/subjects')
    except Exception as e:
        db.session.rollback()
        return render_template('subject.html', 
                             subjects=Subject.query.all(), 
                             error=f"Could not delete subject: {str(e)}")

# Quiz Creation
@app.route('/admin/quizzes/create', methods=['GET', 'POST'])
def create_quiz():
    if not request.cookies.get('admin_id'):
        return redirect('/login')
    
    if request.method == 'POST':
        try:
            new_quiz = Quiz(
                c_id=request.form['chapter_id'],
                title=request.form['title'],
                q_date=datetime.strptime(request.form['date_of_quiz'], '%Y-%m-%d'),
                duration=request.form['time_duration'],
                remarks=request.form['remarks']
            )
            db.session.add(new_quiz)
            db.session.commit()
            
            for i, question in enumerate(request.form.getlist('questions[][text]')):
                options = request.form.getlist(f'questions[{i}][options][]')
                new_question = Question( q_id=new_quiz.q_id, ques=question, opt1=options[0], opt2=options[1], opt3=options[2], opt4=options[3], answer=int(request.form[f'questions[{i}][correct]']))
                db.session.add(new_question)
            
            db.session.commit()
            return redirect('/admin/dashboard')
        
        except Exception as e:
            db.session.rollback()
            chapters = Chapter.query.all()
            return render_template('create_quiz.html', chapters=chapters, error=str(e))
    
    chapters = Chapter.query.all()
    return render_template('create_quiz.html', chapters=chapters)
# User View
@app.route('/admin/users')
def manage_users():
    if not request.cookies.get('admin_id'):
        return redirect('/login')
    users = User.query.all()
    return render_template('u_admin.html', users = users)

# User Info
@app.route('/admin/users/view/<int:u_id>')
def view_user(u_id):
    if not request.cookies.get('admin_id'):
        return redirect('/login')
    
    user = User.query.get_or_404(u_id)
    return render_template('view_user.html', user=user)

# Delete User
@app.route('/admin/users/delete/<int:u_id>', methods=['POST'])
def delete_user(u_id):
    if not request.cookies.get('admin_id'):
        return redirect('/login')
    
    user = User.query.get_or_404(u_id)
    Score.query.filter_by(u_id=u_id).delete()
    db.session.delete(user)
    db.session.commit()
    return redirect('/admin/users')


# User Progress
@app.route('/admin/users/progress/<int:u_id>')
def user_progress(u_id):
    if not request.cookies.get('admin_id'):
        return redirect('/login')
    
    user = User.query.get_or_404(u_id)
    scores = (db.session.query(Score, Quiz, Chapter, Subject)
              .join(Quiz, Score.q_id == Quiz.q_id)
              .join(Chapter, Quiz.c_id == Chapter.c_id)
              .join(Subject, Chapter.s_id == Subject.s_id)
              .filter(Score.u_id == u_id)
              .order_by(Score.time.desc())
              .all())
    
    return render_template('user_progress.html', user=user, scores=scores)

# Overall Progress
@app.route('/admin/users/progress/all')
def all_progress():
    if not request.cookies.get('admin_id'):
        return redirect('/login')
    
    subject_stats = (db.session.query(
        Subject.name,
        db.func.avg(Score.score).label('average_score'),
        db.func.count(Score.sc_id).label('attempt_count'))
        .join(Chapter, Subject.s_id == Chapter.s_id)
        .join(Quiz, Chapter.c_id == Quiz.c_id)
        .join(Score, Quiz.q_id == Score.q_id)
        .group_by(Subject.name)
        .all())
    plt.style.use('seaborn-v0_8-dark')
    plt.figure(figsize=(10, 6))
    subjects = [stat[0] for stat in subject_stats]
    averages = [stat[1] for stat in subject_stats]
    plt.bar(subjects, averages)
    plt.title('Average Scores by Subject')
    plt.ylabel('Average Score (%)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('static/subject_averages.png')
    plt.close()

    return render_template('all_progress.html', subject_stats=subject_stats)

# Routs for Users

# User Dashboard
@app.route('/user/dashboard')
def user_dashboard():
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect('/login')
    
    user = User.query.get(user_id)
    recent_scores = (Score.query
                     .options(db.joinedload(Score.quiz))
                     .filter_by(u_id=user_id)
                     .order_by(Score.time.desc())
                     .limit(5)
                     .all())
    
    performance_entries = []
    for score in recent_scores:
        total_questions = len(score.quiz.questions) if score.quiz.questions else 1
        percentage = (score.score / total_questions) * 100
        performance_entries.append({'score': round(percentage), 'date': score.time.strftime('%Y-%m-%d')})
    
    if recent_scores:
        plt.style.use('seaborn-v0_8-dark')
        fig, ax = plt.subplots(figsize=(10, 4))
        
        dates = [score.time for score in recent_scores]
        scores = []
        for score in recent_scores:
            total_questions = len(score.quiz.questions) if score.quiz.questions else 1
            scores.append((score.score / total_questions) * 100)
        
        ax.plot(dates, scores, marker='o', linestyle='-', color='#007BFF')
        ax.set_title('Recent Performance Trend')
        ax.set_ylabel('Score (%)')
        ax.set_ylim(0, 100)
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()
        fig.savefig('static/user_performance.png', bbox_inches='tight')
        plt.close(fig)

    return render_template('user.html',  current_user=user,  recent_scores=recent_scores, performance_entries=performance_entries, performance_data=bool(recent_scores))

# Quizzes Page
@app.route('/user/quizzes')
def available_quizzes():
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect('/login')
    
    quizzes = Quiz.query.filter(Quiz.q_date <= datetime.now()).all()
    subjects = Subject.query.all()
    chapters = Chapter.query.all()
    return render_template('quizzes.html', quizzes = quizzes, subjects = subjects, chapters = chapters)

# Score Page
@app.route('/user/scores')
def user_scores():
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect('/login')
    
    scores = (Score.query
              .options(
                  db.joinedload(Score.quiz)
                  .joinedload(Quiz.questions),
                  db.joinedload(Score.quiz)
                  .joinedload(Quiz.chapter)
                  .joinedload(Chapter.subject)
              )
              .filter_by(u_id=user_id)
              .order_by(Score.time.desc())
              .all())
    return render_template('uscores.html', scores=scores)

# User Summary 
@app.route('/user/scores/summary')
def user_summary():
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect('/login')
    user = User.query.get(user_id)
    scores = (Score.query
              .options(
                  db.joinedload(Score.quiz)
                  .joinedload(Quiz.chapter)
                  .joinedload(Chapter.subject)
              )
              .filter_by(u_id=user_id)
              .all())
    if not scores:
        return render_template('summary.html', user = user, message = "No Attempts Yet", charts_available = False)
    
    score_values = []
    subject_scores = {}
    
    for score in scores:
        total_questions = len(score.quiz.questions) if score.quiz.questions else 1
        percentage = (score.score / total_questions) * 100
        score_values.append(percentage)
        
        subject_name = score.quiz.chapter.subject.name
        if subject_name not in subject_scores:
            subject_scores[subject_name] = []
        subject_scores[subject_name].append(percentage)


    subject_performance = []
    for subject, scores in subject_scores.items():
        avg_score = sum(scores) / len(scores)
        subject_performance.append({'name': subject, 'average_score': round(avg_score, 1)})

    plt.style.use('seaborn-v0_8-dark')

    fig1, ax1 = plt.subplots(figsize=(8, 4))
    dates = [score[0].time for score in scores]
    ax1.plot(dates, score_values, color = '#4e79a7', marker = 'o', markersize = 6, linewidth = 1.5)
    ax1.set_title('Performance Over Time', pad=20)
    ax1.set_ylim(0, 100)
    ax1.grid(True, alpha=0.3)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    fig1.savefig('static/user_time.png', bbox_inches='tight', dpi=100)
    plt.close(fig1)

    fig2, ax2 = plt.subplots(figsize=(8, 4))
    ax2.hist(score_values, bins=10, color='#59a14f', edgecolor='white')
    ax2.set_title('Score Distribution', pad=20)
    ax2.set_xlabel('Marks')
    ax2.set_ylabel('Frequency')
    ax2.grid(True, alpha=0.3)
    fig2.savefig('static/user_hist.png', bbox_inches='tight', dpi=100)
    plt.close(fig2)

    subject_scores_bar = {}
    for score_obj in scores:
        subject_name = score_obj.quiz.chapter.subject.name
        if subject_name not in subject_scores_bar:
            subject_scores_bar[subject_name] = []
        subject_scores_bar[subject_name].append(score_obj.score)

    subjects = list(subject_scores_bar.keys())
    subject_avgs = [sum(scores) / len(scores) for scores in subject_scores_bar.values()]

    fig3, ax3 = plt.subplots(figsize=(8, 4))
    ax3.bar(subjects, subject_avgs, color='#e15759')
    ax3.set_title('Subject-wise Performance', pad=20)
    ax3.set_ylim(0, 100)
    ax3.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    fig3.savefig('static/user_bar.png', bbox_inches='tight', dpi=100)
    plt.close(fig3)

    fig4, ax4 = plt.subplots(figsize=(6, 6))
    ax4.pie([len(scores) for scores in subject_scores.values()],
           labels=subjects,
           colors=['#4e79a7', '#59a14f', '#e15759', '#f28e2b'],
           autopct='%1.1f%%',
           startangle=90)
    ax4.set_title('Attempt Distribution', pad=20)
    fig4.savefig('static/user_pie.png', bbox_inches='tight', dpi=100)
    plt.close(fig4)

    return render_template('user_summary.html', user = user, avg_score = round(sum(score_values)/len(score_values), 2), highest_score = round(max(score_values)),  quizzes_taken=len(scores), subject_performance = subject_performance, charts_available = True)

# Quiz
@app.route('/quiz/<int:q_id>/start')
def start_quiz(q_id):
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect('/login')
    
    score = Score.query.filter_by(u_id=user_id, q_id=q_id).first()
    if score:
        return redirect(f'/quiz/{q_id}/results')
    
    new_score = Score(u_id=user_id, q_id=q_id, score=0)
    db.session.add(new_score)
    db.session.commit()
    return redirect(f'/quiz/{q_id}/question/0')

@app.route('/quiz/<int:q_id>/question/<int:question_index>')
def show_question(q_id, question_index):
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect('/login')
    
    score = Score.query.filter_by(u_id=user_id, q_id=q_id).first()
    if not score:
        return redirect(f'/quiz/{q_id}/start')
    
    questions = Question.query.filter_by(q_id=q_id).order_by(Question.qs_id).all()
    if not questions:
        return "No questions found", 404
    
    total_questions = len(questions)
    if question_index >= total_questions:
        return redirect(f'/quiz/{q_id}/results')
    
    quiz = Quiz.query.get(q_id)
    return render_template('quiz.html', 
                         quiz=quiz, 
                         question=questions[question_index], 
                         current_question_index=question_index, 
                         total_questions=total_questions)

# Quiz Attempt
@app.route('/quiz/<int:q_id>/attempt', methods=['POST'])
def submit_answer(q_id):
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect('/login')
    
    current_question_index = int(request.form.get('current_question_index', 0))
    selected_answer = int(request.form.get('answer', 0))
    question_id = int(request.form.get('question_id', 0))
    
    question = Question.query.get(question_id)
    if not question:
        return redirect(f'/quiz/{q_id}/question/{current_question_index}')
    
    score = Score.query.filter_by(u_id=user_id, q_id=q_id).first()
    
    if score:
        if selected_answer == question.answer:
            score.score += 1
            db.session.commit()
    
    next_index = current_question_index + 1
    return redirect(f'/quiz/{q_id}/question/{next_index}')

# Quiz Results
@app.route('/quiz/<int:q_id>/results')
def quiz_results(q_id):
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect('/login')
    
    score = Score.query.filter_by(u_id=user_id, q_id=q_id).first()
    if not score:
        return redirect(f'/quiz/{q_id}/start') 
    
    questions = Question.query.filter_by(q_id=q_id).all()
    return render_template('quiz_res.html', quiz=Quiz.query.get(q_id), score=score.score, questions=questions)

if __name__ == '__main__':
    app.run(debug=True)
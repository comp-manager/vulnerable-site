from flask import Flask, render_template, request, session, redirect, url_for, flash
import secrets
import time

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Simulated database
users = {
    'student1': {'password': 'pass123', 'name': 'Alice Johnson', 'scores': []},
    'student2': {'password': 'pass456', 'name': 'Bob Smith', 'scores': []},
    'teacher': {'password': 'teacher123', 'name': 'Prof. Davis', 'is_teacher': True, 'scores': []}
}

# Quiz database with answers (VULNERABILITY: Answers accessible)
quizzes = {
    1: {
        'title': 'Python Basics Quiz',
        'duration': 300,  # 5 minutes in seconds
        'questions': [
            {
                'id': 1,
                'question': 'What is the output of print(2 ** 3)?',
                'options': ['6', '8', '9', '5'],
                'correct': 1
            },
            {
                'id': 2,
                'question': 'Which keyword is used to define a function in Python?',
                'options': ['func', 'def', 'function', 'define'],
                'correct': 1
            },
            {
                'id': 3,
                'question': 'What data type is [1, 2, 3]?',
                'options': ['tuple', 'set', 'list', 'array'],
                'correct': 2
            },
            {
                'id': 4,
                'question': 'How do you start a comment in Python?',
                'options': ['//', '/*', '#', '--'],
                'correct': 2
            },
            {
                'id': 5,
                'question': 'What does len([1,2,3]) return?',
                'options': ['2', '3', '4', 'None'],
                'correct': 1
            }
        ]
    },
    2: {
        'title': 'Web Security Quiz',
        'duration': 600,  # 10 minutes
        'questions': [
            {
                'id': 1,
                'question': 'What does XSS stand for?',
                'options': ['Cross-Site Scripting', 'External Style Sheets', 'XML Server Side', 'Cross Server Scripts'],
                'correct': 0
            },
            {
                'id': 2,
                'question': 'Which HTTP method is safest for sensitive operations?',
                'options': ['GET', 'POST', 'PUT', 'DELETE'],
                'correct': 1
            },
            {
                'id': 3,
                'question': 'What does CSRF stand for?',
                'options': ['Cross-Site Request Forgery', 'Client-Side Request Form', 'Cross-Server Resource Fetching', 'Cookie Security Request Filter'],
                'correct': 0
            }
        ]
    }
}

# Store active exam sessions
exam_sessions = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users and users[username]['password'] == password:
            session['username'] = username
            session['name'] = users[username]['name']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials!', 'error')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user = users[username]
    
    # Calculate average score
    avg_score = 0
    if user['scores']:
        avg_score = sum(user['scores']) / len(user['scores'])
    
    return render_template('dashboard.html', user=user, quizzes=quizzes, avg_score=avg_score)

@app.route('/quizzes')
def quizzes_list():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    return render_template('quizzes.html', quizzes=quizzes)

# VULNERABILITY 1: Quiz data including answers sent to client
@app.route('/exam/<int:quiz_id>')
def start_exam(quiz_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if quiz_id not in quizzes:
        flash('Quiz not found!', 'error')
        return redirect(url_for('quizzes_list'))
    
    quiz = quizzes[quiz_id]
    
    # VULNERABILITY: Create session with start time (client can modify)
    session_id = secrets.token_hex(8)
    exam_sessions[session_id] = {
        'username': session['username'],
        'quiz_id': quiz_id,
        'start_time': time.time(),
        'duration': quiz['duration']
    }
    
    session['exam_session_id'] = session_id
    
    return render_template('exam.html', quiz=quiz, quiz_id=quiz_id, session_id=session_id)

# VULNERABILITY 2: No time validation, trusts client-submitted time
# VULNERABILITY 3: Accepts answers even after time expires
@app.route('/submit_exam', methods=['POST'])
def submit_exam():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    quiz_id = int(request.form.get('quiz_id'))
    session_id = request.form.get('session_id')
    
    # VULNERABILITY: Trusting client-side time calculation
    # No server-side time validation!
    
    if quiz_id not in quizzes:
        flash('Invalid quiz!', 'error')
        return redirect(url_for('quizzes_list'))
    
    quiz = quizzes[quiz_id]
    
    # Calculate score
    correct = 0
    total = len(quiz['questions'])
    
    for question in quiz['questions']:
        submitted_answer = request.form.get(f"q{question['id']}")
        if submitted_answer and int(submitted_answer) == question['correct']:
            correct += 1
    
    score = (correct / total) * 100
    
    # Save score
    username = session['username']
    users[username]['scores'].append(score)
    
    # Clean up session
    if session_id in exam_sessions:
        del exam_sessions[session_id]
    
    return render_template('results.html', score=score, correct=correct, total=total, quiz=quiz)

@app.route('/scores')
def scores():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user = users[username]
    
    return render_template('scores.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("\n" + "="*70)
    print("VULNERABLE ONLINE EXAM PLATFORM - BUSINESS LOGIC FLAWS")
    print("="*70)
    print("\nVULNERABILITIES:")
    print("1. Answers visible in page source (HTML comments/hidden divs)")
    print("2. Timer runs client-side (can be paused/modified in DevTools)")
    print("3. Time duration sent as hidden field (can be extended)")
    print("4. No server-side time validation (submit after time expires)")
    print("5. Quiz ID can be manipulated to access different quizzes")
    print("6. Session ID predictable/modifiable")
    print("7. Can view page source to see correct answers before submitting")
    print("8. Can replay exam multiple times to improve score")
    print("\nTest Accounts:")
    print("  student1 / pass123")
    print("  student2 / pass456")
    print("  teacher / teacher123")
    print("\nExploitation Ideas:")
    print("  - Press F12 and pause JavaScript timer")
    print("  - Inspect page source to find correct answers")
    print("  - Modify duration hidden field to 999999 seconds")
    print("  - Submit exam after time expires")
    print("  - Change quiz_id to access different quizzes")
    print("="*70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

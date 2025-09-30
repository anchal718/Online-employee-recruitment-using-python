import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
from flask import send_from_directory
app = Flask(__name__)

# MySQL Configuration
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', 'anchal123')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'recruitment_db')
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24).hex())
mysql = MySQL(app)

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'panditanchalsharma69@gmail.com')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'hslx cuew isqq klvi')
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']

mail = Mail(app)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        with mysql.connection.cursor() as cur:
            cur.execute("SELECT * FROM admins WHERE email = %s AND password = %s", (email, password))
            admin = cur.fetchone()
        if admin:
            session['admin_logged_in'] = True
            session['admin_email'] = email
            flash("Login successful!", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid email or password!", "danger")
            return redirect(url_for('admin_login'))

    return render_template('adminlogin.html')
import MySQLdb.cursors  # Import DictCursor

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_logged_in' not in session:
        flash("Unauthorized access! Please log in.", "danger")
        return redirect(url_for('home'))

    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cur:
        cur.execute("SELECT applications.*, jobs.job_title AS job_title FROM applications JOIN jobs ON applications.job_id = jobs.id WHERE applications.status = 'pending'")
        applications = cur.fetchall()

        # Debugging: Print applications data
        print("Applications Data:", applications)

    
    return render_template('admin_dashboard.html', applications=applications)

# Download resume
@app.route('/download_resume/<filename>')
def download_resume(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        flash("File not found!", "danger")
        return redirect(url_for('admin_dashboard'))
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/view_resume/<filename>')
def view_resume(filename):
    filename = secure_filename(filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        flash("Resume file not found!", "danger")
        return redirect(url_for('admin_dashboard'))
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Approve application
@app.route('/admin/approve/<int:application_id>')
def approve_application(application_id):
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cur:
        cur.execute("UPDATE applications SET status = 'approved' WHERE id = %s", (application_id,))
        mysql.connection.commit()
        cur.execute("SELECT applications.email, applications.phone, applications.candidate_name, applications.qualification, jobs.job_title FROM applications JOIN jobs ON applications.job_id = jobs.id WHERE applications.id = %s", (application_id,))
        candidate_data = cur.fetchone()

    if candidate_data:
        candidate_email = candidate_data['email']
        candidate_phone = candidate_data['phone']
        candidate_name = candidate_data['candidate_name']
        job_title = candidate_data['job_title']
        
        # Send Email to the candidate
        msg = Message("Your Application Approved!", recipients=[candidate_email])
        msg.body = f"""
        Dear {candidate_name},

        Congratulations! Your application for the position of {job_title} has been approved 🎉
        Our team will contact you soon regarding further steps.

        Best Regards,  
        The Recruitment Team
        """
        mail.send(msg)
        flash("Application approved ! Email sent.", "success")
    else:
        flash("Application approved, but candidate data not found.", "warning")

    return redirect(url_for('admin_dashboard'))

# Reject application
@app.route('/admin/reject/<int:application_id>')
def reject_application(application_id):
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cur:
        cur.execute("UPDATE applications SET status = 'rejected' WHERE id = %s", (application_id,))
        mysql.connection.commit()
        cur.execute("SELECT email, phone, candidate_name FROM applications WHERE id = %s", (application_id,))
        applicant_data = cur.fetchone()

    if applicant_data:
        applicant_email = applicant_data['email']
        applicant_phone = applicant_data['phone']
        applicant_name = applicant_data['candidate_name']

        # Send Email to the candidate
        msg = Message("Application Rejected", recipients=[applicant_email])
        msg.body = f"Dear {applicant_name}, sorry to inform you that your application has been rejected."
        mail.send(msg)
        flash("Application rejected ! Email sent.", "success")
    else:
        flash("Application rejected, but applicant data not found.", "warning")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/send_sms_all')
def send_sms_all():
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cur:
        cur.execute("SELECT candidate_name, phone, job_id FROM applications")
        candidates = cur.fetchall()

    if not candidates:
        flash("No applicants found to send SMS.", "warning")
        return redirect(url_for('admin_dashboard'))

# Home Route
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/')
def index():
    return render_template('index.html')


# About Route
@app.route('/about')
def about():
    return render_template('about.html')

# Contact Route (Job Application)
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')

# Ensure the folder exists, create if not
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
#jobs
import MySQLdb.cursors

@app.route('/jobs')
def jobs():
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cur:
        # Fetch job titles and job ids (or other details)
        cur.execute("SELECT id, job_title FROM jobs")
        job_list = cur.fetchall()  # Get all the results

    # Debugging: Print the job list to check if it has been fetched
    print("Job List from DB:", job_list)  # This will print the job data in the console

    return render_template('jobs.html', jobs=job_list)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    extracted_data = {}
    file_path = None

    if request.method == 'POST':
        if 'resume' in request.files:
            file = request.files['resume']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save=filename

        name = request.form.get('name', extracted_data.get('name', ''))
        email = request.form.get('email', extracted_data.get('email', ''))
        phone = request.form.get('phone', extracted_data.get('phone', ''))
        qualification = request.form.get('qualification')

        try:
            job_id = int(request.form['job_id'])
        except ValueError:
            flash("Invalid job ID!", "danger")
            return redirect(url_for('contact'))

        with mysql.connection.cursor() as cur:
            cur.execute("SELECT job_title FROM jobs WHERE id = %s", (job_id,))  # FIXED
            job_title = cur.fetchone()

        if job_title:
            job_title = job_title[0]
            with mysql.connection.cursor() as cur:
                cur.execute("""INSERT INTO applications (candidate_name, email, phone, qualification, job_id, resume_path, status) 
                               VALUES (%s, %s, %s, %s, %s, %s, 'pending')""",
                            (name, email, phone, qualification, job_id, file_path))
                mysql.connection.commit()

            # Send Email to the candidate
            msg = Message("Job Application Confirmation", sender=app.config['MAIL_USERNAME'], recipients=[email])
            msg.body = f"""
            Dear {name} 😊,

            Thank you for applying to our company.
            Your application has been received and will be reviewed shortly.

            📌 Applied For: {job_title}
            📌 Name: {name}
            📌 Email: {email}
            📌 Phone: {phone}
            📌 Qualification: {qualification}

            We will contact you if your profile is shortlisted.

            Best Regards,  
            The Recruitment Team
            """
            try:
                mail.send(msg)
                flash("Job application submitted successfully! Confirmation email sent.", "success")
            except Exception as e:
                flash(f"Job application submitted, but email failed to send. Error: {e}", "warning")

            return redirect(url_for('contact'))
        else:
            flash("Job not found or not open for applications!", "danger")
            return redirect(url_for('contact'))

    with mysql.connection.cursor() as cur:
        cur.execute("SELECT id, job_title FROM jobs")  # FIXED
        jobs = cur.fetchall()

        cur.execute("SELECT qualification FROM qualifications")
        qualifications = [row[0] for row in cur.fetchall()]
    return render_template('contact.html', jobs=jobs, qualifications=qualifications, extracted_data=extracted_data)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

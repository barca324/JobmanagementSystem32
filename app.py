from flask import Flask, render_template, request, redirect,flash,session
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId
import yagmail
from cloudinary.uploader import upload


app = Flask(__name__)
app.secret_key = '34546577fgjj' 

bcrypt = Bcrypt(app)


yag = yagmail.SMTP('madhusudan329832@gmail.com', 'lynt ktot dvel stwj')


yag.close()
import cloudinary


cloudinary.config(
    cloud_name='dk04slwnr',
    api_key='727785325261413',
    api_secret='gv_EteuolF181lmzC_AfkV9MAt4'
)
def upload_pdf_to_cloudinary(file_path):
    try:
        result = cloudinary.uploader.upload(file_path, resource_type="auto")
        print(f"File uploaded successfully. Public ID: {result['public_id']}")
        print(f"URL: {result['secure_url']}")
        return result
    except Exception as e:
        print(f"Error uploading file to Cloudinary: {e}")


client = MongoClient("mongodb://localhost:27017/") 
db = client['Jobify']
jobs_collection = db['jobs']
user_collection = db['user']
job_providers_collection = db['jobproviders']
job_seekers_collection = db['jobseekers']

def findjobs():
    jobs = []
    cursor = jobs_collection.find()
    for item in cursor:
        jobs.append(item)
    return jobs

@app.route("/")
def hello_world():
    jobs = findjobs()
    print(jobs)  
    return render_template('index.html', jobs=jobs)

@app.route("/signup")
def signupcheck():
    return render_template('signupcheck.html')
@app.route("/loginp")
def loginp():
    return render_template('loginp.html')
@app.route("/logins")
def logins():
    return render_template('logins.html')
@app.route("/login",methods=["GET","POST"])
def login():
    return render_template('login.html')

@app.route("/signup/provider", methods=["GET", "POST"])
def signup_provider():
    if request.method == "POST":
        username = request.form.get("name")
        companyname = request.form.get("cname")
        email = request.form.get("email")
        phone = request.form.get("phone")
        password = request.form.get("password")
        cpassword = request.form.get("cpassword")
        
        if not (username and companyname and email and phone and password and cpassword):
            return "All fields are required."

        if password != cpassword:
            return "Password and confirm password do not match."
           

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        provider_data = {
            "username": username,
            "companyname": companyname,
            "email": email,
            "phone": phone,
            "password": hashed_password  
        }
        result = job_providers_collection.insert_one(provider_data)

        if result:
            return redirect('/loginp')  # Redirect to login page after successful signup
        else:
            return "Something went wrong. Please try again."

    return render_template("signuprovider.html")

@app.route("/signup/seeker", methods=["GET", "POST"])
def signup_seeker():
    if request.method == "POST":
        username = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        password = request.form.get("password")
        cpassword = request.form.get("cpassword")
        
        if not (username  and email and phone and password and cpassword):
            return "All fields are required."

        if password != cpassword:
            return "Password and confirm password do not match."
           

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        seeker_data = {
            "username": username,
            
            "email": email,
            "phone": phone,
            "password": hashed_password  
        }
        result = job_seekers_collection.insert_one(seeker_data)

        if result:
            return redirect('/logins')  # Redirect to login page after successful signup
        else:
            return "Something went wrong. Please try again."

    return render_template("signupseeker.html")



@app.route("/login/provider", methods=[ "POST"])
def login_provider():
     emaild = request.form.get("email")
     password = request.form.get("password")
     result=job_providers_collection.find_one({"email":emaild})
     if(result):
         hashedpassword=result['password']
         if bcrypt.check_password_hash(hashedpassword, password):
                session['user_id'] = str(result['_id']) 
                return redirect('/provider')
         else:
                return redirect("/loginp")  
     else:
         return "You need to Signup first" 


@app.route("/login/seeker", methods=[ "POST"])
def login_seeker():
     emaild = request.form.get("email")
     password = request.form.get("password")
     result=job_seekers_collection.find_one({"email":emaild})
     if(result):
         hashedpassword=result['password']
         if bcrypt.check_password_hash(hashedpassword, password):
                session['user_id'] = str(result['_id']) 
                return redirect('/seeker')
         else:
                return redirect("/logins")  
     else:
         return "You need to Signup first"        


@app.route('/provider')
def provider():
    user_id = session.get('user_id')
    if not user_id:
        return "User not logged in" 

    user_id = ObjectId(user_id)

    
    result = job_providers_collection.find_one({'_id': user_id})
    if not result:
        return "Job provider not found"  

   
    company_name = result.get('companyname')
    if not company_name:
        return "Company name not found"

    users = user_collection.find({'company': company_name})
    return render_template('provider.html',users=users,result=result)

@app.route('/seeker')
def seeker():
    jobs = findjobs()
    details=session.get('user_id')
    details=ObjectId(details)
    result=job_seekers_collection.find_one({'_id':details})
    print(result)
    return render_template('seeker.html',result=result,jobs=jobs)

     




@app.route("/apply/<string:id>")
def jobid(id):
    jobs = findjobs()
    newid = ObjectId(id)
    job = jobs_collection.find_one({"_id": newid})
    print(job)
    
    if job:
        return render_template('job.html', jobs=job)
    else:
        return "Job not found"

@app.route("/submit/<string:id>", methods=["POST"])
def submit(id):
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    resume = request.files['resume']
    
    newid = ObjectId(id)
    role = jobs_collection.find_one({"_id": newid})
    company=role['posted_by']
    result=upload_pdf_to_cloudinary(resume)
    
    if name and email and resume and phone:
        application_data = {
            'name': name,
            'email': email,
            'phone': phone,
            'resume': resume.filename,
            'role': role['name'],
            'company':company,
            'url':result['secure_url']
        }
        result = user_collection.insert_one(application_data)
        
        if result:
            recipient = email
            subject = 'Confirmation email'
            body = f'Thank you for applying for the role of {role["name"]}. If the company finds you suitable for this role, we will reach out to you.'
            
            yag.send(to=recipient, subject=subject, contents=body)
            yag.close()
            
            
            
            
            return render_template('success.html')
        else:
            return render_template('failure.html')
    else:
        return render_template('invalid.html')

@app.route('/provider/hire',methods=["GET","POST"])
def hire():
    if request.method == "POST":
        name=request.form.get('name')
        email=request.form.get('email')
        role=request.form.get('role')
        salary=request.form.get('salary')
        loc=request.form.get('loc')
        hpassword=request.form.get('password')
        responsiblity=request.form.get('res')
        result=job_providers_collection.find_one({'companyname':name})
        print(result)
        if(result):
            hashedpassword=result['password']
            if bcrypt.check_password_hash(hashedpassword, hpassword):
                job={
                   'name':role,
                   'salary':salary,
                   'location':loc,
                    'res':responsiblity,
                    'posted_by':name
                }
                final=jobs_collection.insert_one(job)
                if(final):
                    recipient = email
                    subject = 'Confirmation email'
                    body = f'Your opening for {role} has been posted.'
            
                    yag.send(to=recipient, subject=subject, contents=body)
                    yag.close()

                return render_template('success.html')
            else:
                return "Password is wrong."


    
    return render_template('hire.html')




@app.route('/logout')
def logout():
    session.pop('user_id', None)  
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)

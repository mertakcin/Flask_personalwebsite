from flask import Flask, render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps


# Kullanıcı Giriş - Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session: #session içinde logged_in tipinde bir değer var mı
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görmek için lütfen giriş yapın", category="danger")
            return redirect(url_for("login"))
    return decorated_function

# Kullanıcı Kayıt Formu

class RegisterForm(Form):
    name = StringField("İsim Soyisim", validators = [validators.Length(min = 4, max = 25)])
    username = StringField("Kullanıcı Adı", validators = [validators.Length(min = 5, max = 35)])
    email = StringField("E-mail adresi", validators = [validators.Email(message="Lütfen geçerli bir e-mail adresi girin")])
    password = PasswordField("Parola: ", validators = [
        validators.DataRequired(message = "Lütfen bir parola belirleyin"),
        validators.EqualTo(fieldname = "confirm", message="Parolanız uyuşmuyor")
        
        ])
    confirm = PasswordField("Parola Doğrula")

#Giriş Yap formu

class LoginForm(Form):
    username = StringField("Kullanıcı Adı:")
    password = PasswordField("Parola: ")

app = Flask(__name__)

app.secret_key = "akcinmert" 
app.config["MYSQL_HOST"] = 'localhost'
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "akcinmert"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"


mysql = MySQL(app)




@app.route("/")

def index():
    
    """
    articles =  [

        {"id":1, "title":"Deneme1","content":"Deneme1 icerik"},
        {"id":2, "title":"Deneme2","content":"Deneme2 icerik"},
        {"id":3, "title":"Deneme3","content":"Deneme3 icerik"}


    ]
    """
    return render_template("index.html")



@app.route("/about")

def about():
    return render_template("about.html")


# Yazılar Sayfası

@app.route("/articles")

def articles():
    cursor = mysql.connection.cursor()

    sorgu = "Select * From articles"

    result = cursor.execute(sorgu)

    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html", articles = articles)

    else:
        return render_template("articles.html")

#@app.route("/article/<string:id>")

#def detail(id):

    #return "Article Id" + id



@app.route("/dashboard")
@login_required

def dashboard():

    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles where author = %s"

    result = cursor.execute(sorgu,(session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:
        return render_template("dashboard.html")
        


        

    return render_template("dashboard.html")
#Kayıt Olma

@app.route("/register", methods = ["GET","POST"])

def register():

    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():

        name = form.name.data
        username  = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()

        sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)" #%s YERİNE FORMAT DA OLUR

        cursor.execute(sorgu,(name,email,username,password))

        mysql.connection.commit() #veri tabanında herhangi bir güncelleme yaptığınız anda commit metodunu kullanmak gerekir.

        cursor.close()

        flash("Başarıyla Kayıt Oldunuz", "success")

        return redirect(url_for("login"))
    else:

        return render_template("register.html", form = form)


#Login işlemi
@app.route("/login", methods = ["GET","POST"])

def login():
    form = LoginForm(request.form)

    if request.method == "POST":

        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        sorgu1 = "Select * from users where username = %s"

        result = cursor.execute(sorgu1,(username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):


                flash("Başarıyla Giriş Yaptınız","success")

                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("index"))

            else: 
                flash("Parolanızı yanlış girdiniz..","danger")
                return redirect((url_for("login")))
        else:
            flash("Böyle bir kullanıcı adı bulunmuyor..","danger")
            return redirect(url_for("login"))

    return render_template("login.html", form = form)

#Detay Sayfası

@app.route("/article/<string:id>")

def article(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles where id  = %s"

    result = cursor.execute(sorgu,(id,))

    if result > 0:

        article = cursor.fetchone()
        return render_template("article.html",article = article)

    else:

        return render_template("article.html")


#Logout işlemi

@app.route("/logout")

def logout():

    session.clear()
    return redirect(url_for("index"))

# Makale ekleme

@app.route("/addarticle", methods = ["GET","POST"])

def addarticle():
    form  = ArticleForm(request.form)
    if request.method == "POST" and form.validate():

        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor() #mysql üzerinde işlem yapmamızı sağlar

        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(sorgu,(title,session["username"],content))

        mysql.connection.commit()

        cursor.close()

        flash("Yazınız başarıyla kaydedildi","success")
        return redirect(url_for("dashboard"))
        
    else:

        return render_template("addarticle.html", form = form)

# Makale Silme

@app.route("/delete/<string:id>")
@login_required

def delete(id):

    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles where author = %s and id = %s"

    result = cursor.execute(sorgu,(session["username"],id))


    if result > 0:
        sorgu2 = "Delete from articles where id = %s"
        cursor.execute(sorgu2,(id,))

        mysql.connection.commit()

        return redirect(url_for("dashboard"))

    else:
        flash("Bu yazıyı silme yetkiniz yok veya böyle bir yazı mevcut değil","danger")
        return redirect(url_for("index"))



# Makale Güncelleme
@app.route("/edit/<string:id>", methods = ["GET","POST"])
@login_required


def update(id):

    if request.method == "GET":
        cursor = mysql.connection.cursor()

        sorgu = "Select * from articles where id = %s and author = %s"
        result = cursor.execute(sorgu,(id,session["username"]))

        if result == 0:

            flash("Böyle bir makale yok veya bu işleme yetkiniz yok..","danger")
            return redirect(url_for("index"))

        else:
            article = cursor.fetchone()
            form = ArticleForm()

            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html", form = form)
    else:
        #POST REQUEST KISMI
        form = ArticleForm(request.form)

        newTitle = form.title.data
        newContent = form.content.data

        sorgu2 = "Update articles Set title = %s,content = %s where id = %s"

        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))

        mysql.connection.commit()

        flash("Yazı başarıyla güncellendi","success")
        return redirect(url_for("dashboard"))

# Makale Form

class ArticleForm(Form):
    
    title = StringField("Yazı Başlığı",validators = [validators.length(min = 5,max = 100)])
    content = TextAreaField("Yazı İçeriği",validators = [validators.length(min = 10)])



# Arama URL

@app.route("/search",methods = ["GET","POST"])

def search():

    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")

        cursor = mysql.connection.cursor()

        sorgu = "Select * from articles where title like '%" + keyword + "%'"

        result = cursor.execute(sorgu)

        if result == 0:

            flash("Aranan Kelimeye Uygun Makale Bulunamadı....","warning")
            return redirect(url_for("articles"))
        
        else:
            articles = cursor.fetchall()

            return render_template("articles.html", articles = articles)

if __name__ == "__main__":
     
    
    app.run(debug=True)
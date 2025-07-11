from flask import Flask,render_template, request, session
from forms import UserInfoForm
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# ==================================================
# インスタンス生成
# データベース作成
# ==================================================
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.users'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

Migrate(app, db)

class Users(db.Model):
    id_mailaddress = db.Column(db.String, primary_key=True)
    login_pass = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String, nullable=False)
    #0が男性、1が女性
    sex = db.Column(db.Integer, nullable=False)
    car = db.Column(db.String, nullable=False)
    image = db.Column(db.String, nullable=True)

app.secret_key = os.urandom(24)  # セッションを使用するために必要です

#ホーム画面
@app.route('/', methods=['GET', 'POST'])
def home(): 
    form = UserInfoForm(request.form)

    return render_template('home.html')

#ログイン画面
@app.route('/login')
def login():
    return render_template('login.html')

#会員登録画面
@app.route('/signin')
def singin():
    return render_template('singin.html')

#マッチング画面
@app.route('/home/<string:name>')
def home_match(name):
    return render_template('match.html')

#プロフィール画面
@app.route('/profile/<string:name>')
def profile(name):
    return  render_template()

if __name__ == '__main__':
    app.run(debug=True) 
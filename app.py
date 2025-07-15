from flask import Flask,render_template, request, session ,flash ,url_for ,redirect
from forms import UserInfoForm
from flask_login import  LoginManager, UserMixin, login_user, logout_user, login_required, current_user
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

#LoginManager起動
login_manager = LoginManager(app)
login_manager.login_view = 'home'

app.secret_key = 'secret_key'

Migrate(app, db)

class Users(UserMixin, db.Model):
    id_mailaddress = db.Column(db.String, primary_key=True)
    login_pass = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String, nullable=False)
    school_year = db.Column(db.Integer, nullable=False)
    course = db.Column(db.String, nullable=False)
    hobby = db.Column(db.String, nullable=False)
    #0が男性、1が女性
    sex = db.Column(db.Integer, nullable=False)
    car = db.Column(db.String, nullable=False)
    image = db.Column(db.String, nullable=True)

    def get_id(self):
        return self.id_mailaddress

#ユーザーローダー関数
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)

app.secret_key = os.urandom(24)  # セッションを使用するために必要です

#ホーム画面
@app.route('/', methods=['GET', 'POST'])
def home(): 
    if request.method == 'GET':
        return render_template('home.html')

    elif request.method == 'POST':
        if 'login_btn' in request.form:
            email = request.form.get('loginEmail')
            password = request.form.get('loginPassword')
            user = Users.query.filter_by(id_mailaddress = email, login_pass=password).first()
        
            if user:
                login_user(user)
                flash('ログインに成功しました')
                return redirect(url_for('home_match', name=user.name))
            else:
                flash('メールアドレスまたはパスワードが正しくありません')
                return redirect(url_for('home'))
        
        else:
            # どちらのフォームも判別できなかった場合（不正なリクエスト）
            flash('不正なリクエストです')
            return redirect(url_for('home'))


#会員登録画面
@app.route('/signup', methods=['GET', 'POST'])
def singup():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    confirmPassword = request.form.get('confirmPassword')
    school_year = request.form.get('year')
    course = request.form.get('course')
    hobby = request.form.get('hobby')
    # 現時点ではフォームに 'sex' がないため、追加するかデフォルト/プレースホルダーを設定する必要があります
    # 仮にsexのデフォルト値を設定します。フォームから取得する方法（例：ラジオボタン）を追加する必要があります。
    sex = 0 # プレースホルダー: これはフォームから取得する方法を追加する必要があります (例: ラジオボタン)
    car = request.form.get('car') if request.form.get('license') else None # licenseがtrueの場合のみcarを取得し、それ以外はNone
    if request.method == "POST":
        if password != confirmPassword:
            flash('パスワードが一致しません')
        
    return render_template('singup.html')

#マッチング画面
@app.route('/home')
def home_match(name):
    return render_template('match.html')

#プロフィール画面
@app.route('/profile/<string:name>')
def profile(name):
    return  render_template()

if __name__ == '__main__':
    app.run(port=8888,debug=True) 
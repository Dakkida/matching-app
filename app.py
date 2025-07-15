from flask import Flask,render_template, request, session ,flash ,url_for ,redirect
from forms import RegistrationForm
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
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # 登録処理
        user_data = {
            'name': form.name.data,
            'email': form.email.data,
            'password': form.password.data,
            'year': int(form.year.data),
            'course': form.course.data,
            'time': form.time.data,
            'hobby': form.hobby.data,
            'license': form.license.data,
            'car': form.car.data or None
        }
        
        # ここでデータベースに保存する処理を実装
        print(f"登録データ: {user_data}")
        
        flash('アカウントが正常に作成されました！', 'success')
        return redirect(url_for('home_match'))
    
    return render_template('singup.html', form=form)


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
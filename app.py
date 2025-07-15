from sqlite3 import IntegrityError
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

app.secret_key = os.urandom(24) 

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
                print("DEBUG: 'ログインに成功しました' をフラッシュしました")
                return redirect(url_for('home_match', name=user.name))
            else:
                flash('メールアドレスまたはパスワードが正しくありません')
                print("DEBUG: 'メールアドレスまたはパスワードが正しくありません' をフラッシュしました")
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
        # メールアドレスの重複チェック
        existing_user = Users.query.filter_by(id_mailaddress=form.email.data).first()
        if existing_user:
            flash('このメールアドレスは既に登録されています。別のメールアドレスを使用してください。', 'error')
            return render_template('singup.html', form=form)
        
        try:
            # 新しいユーザーの作成
            new_user = Users(
                id_mailaddress=form.email.data,
                login_pass=form.password.data,  # 本来はハッシュ化すべき
                name=form.name.data,
                school_year=int(form.year.data),
                course=form.course.data,
                hobby=form.hobby.data,
                sex=0,  # デフォルト値（実際のフォームに性別フィールドを追加する必要があります）
                car=form.car.data or "なし"
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('アカウントが正常に作成されました！', 'success')
            return redirect(url_for('home'))
            
        except IntegrityError:
            # データベースレベルでの重複エラーをキャッチ
            db.session.rollback()
            flash('このメールアドレスは既に登録されています。別のメールアドレスを使用してください。', 'error')
            return render_template('singup.html', form=form)
        
        except Exception as e:
            # その他のデータベースエラー
            db.session.rollback()
            flash('登録中にエラーが発生しました。もう一度お試しください。', 'error')
            return render_template('singup.html', form=form)
    
    return render_template('singup.html', form=form)


# メールアドレス重複チェック用のAPIエンドポイント（オプション）
@app.route('/check-email', methods=['POST'])
def check_email():
    """リアルタイムでメールアドレスの重複をチェックするAPIエンドポイント"""
    email = request.json.get('email')
    
    if not email:
        return {'error': 'メールアドレスが必要です'}, 400
    
    existing_user = Users.query.filter_by(id_mailaddress=email).first()
    
    if existing_user:
        return {'exists': True, 'message': 'このメールアドレスは既に使用されています'}, 200
    
    return {'exists': False, 'message': 'このメールアドレスは利用可能です'}, 200


#マッチング画面
@app.route('/home', methods=['GET', 'POST'])
@login_required
def home_match():
    if current_user.is_authenticated:
        return render_template('match.html', user_name=current_user.name)
    else:
        # ログインしていない場合はホーム画面にリダイレクト
        flash('ログインが必要です。', 'info')
        return redirect(url_for('home'))


#プロフィール画面
@app.route('/profile/<string:name>')
def profile(name):
    return  render_template()

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # これがテーブルを作成するコマンドです
    app.run(port=8888,debug=True) 
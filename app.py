import sqlite3
from flask import Flask, render_template, request, session, flash, url_for, redirect
from forms import RegistrationForm # forms.py が必要です
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError # IntegrityError を正しくインポート
import uuid # ユニークなファイル名を生成するために追加

# ==================================================
# インスタンス生成
# データベース作成
# ==================================================
app = Flask(__name__)

# データベース設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.users'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 画像アップロード設定
# 画像を保存するフォルダのパス
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'images')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# アップロードフォルダが存在しない場合は作成
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
# 許可するファイルの拡張子
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# LoginManager起動
login_manager = LoginManager(app)
login_manager.login_view = 'home' # ログインが必要なページにアクセスしようとしたときにリダイレクトされるビュー

app.secret_key = os.urandom(24) # セッション管理のためのシークレットキー

Migrate(app, db) # データベースマイグレーションの初期化

# 許可されたファイル拡張子かどうかをチェックするヘルパー関数
def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ユーザーモデルの定義
class Users(UserMixin, db.Model):
    id_mailaddress = db.Column(db.String, primary_key=True)
    login_pass = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String, nullable=False)
    school_year = db.Column(db.Integer, nullable=False)
    course = db.Column(db.String, nullable=False)
    hobby = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable=False)
    # 0が男性、1
    # 0が男性、1が女性
    sex = db.Column(db.Integer, nullable=False)
    car = db.Column(db.String, nullable=False)
    # プロフィール画像のファイル名を保存するカラム
    image = db.Column(db.String, nullable=True)

    def get_id(self):
        # Flask-Loginがユーザーを識別するために使用するIDを返す
        return self.id_mailaddress

# ユーザーローダー関数
@login_manager.user_loader
def load_user(user_id):
    # user_idに基づいてユーザーオブジェクトをロードする
    return Users.query.get(user_id)

# ホーム画面
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
                login_user(user) # ユーザーをログインさせる
                flash('ログインに成功しました', 'success')
                session['user_name'] = user.name
                # ログイン成功後、マッチング画面にリダイレクト
                return redirect(url_for('home_match')) # nameパラメータは不要
            else:
                flash('メールアドレスまたはパスワードが正しくありません', 'danger')
                return redirect(url_for('home'))
        
        else:
            # どちらのフォームも判別できなかった場合（不正なリクエスト）
            flash('不正なリクエストです', 'warning')
            return redirect(url_for('home'))

# 会員登録画面
@app.route('/signup', methods=['GET', 'POST'])
def singup():
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # メールアドレスの重複チェック
        existing_user = Users.query.filter_by(id_mailaddress=form.email.data).first()
        if existing_user:
            flash('このメールアドレスは既に登録されています。別のメールアドレスを使用してください。', 'danger')
            return render_template('singup.html', form=form)
        
        try:
            # 新しいユーザーの作成
            new_user = Users(
                id_mailaddress=form.email.data,
                login_pass=form.password.data,  # 注意: 本来はパスワードをハッシュ化すべきです
                name=form.name.data,
                school_year=int(form.year.data),
                course=form.course.data,
                hobby=form.hobby.data,
                time=form.time.data,
                sex=form.gender.data,  # フォームに性別フィールドを追加してください
                car=form.car.data or "なし", # carが空の場合のデフォルト値
                image=None # 初期状態では画像なし
            )
            
            db.session.add(new_user)
            db.session.commit()

            new_login_user = Users.query.filter_by(id_mailaddress=form.email.data).first()

            login_user(new_login_user) 
            
            flash('アカウントが正常に作成されました！プロフィール画像をアップロードしてください。', 'success')
            return redirect(url_for('imageupload'))
            
        except IntegrityError:
            # データベースレベルでの重複エラーをキャッチ (id_mailaddressがPRIMARY KEYのため)
            db.session.rollback()
            flash('このメールアドレスは既に登録されています。別のメールアドレスを使用してください。', 'danger')
            return render_template('singup.html', form=form)
        
        except Exception as e:
            # その他のデータベースエラー
            db.session.rollback()
            flash(f'登録中にエラーが発生しました: {e}。もう一度お試しください。', 'danger')
            return render_template('singup.html', form=form)
    
    return render_template('singup.html', form=form)

# 画像アップロード画面
@app.route('/imageupload', methods=['GET', 'POST'])
@login_required # ログインしているユーザーのみアクセス可能
def imageupload():
    if request.method == 'POST':
        # ファイルがリクエストに含まれているかチェック
        if 'image' not in request.files:
            flash('画像ファイルが選択されていません。', 'warning')
            return redirect(request.url)
        
        file = request.files['image']
        
        # ファイル名が空の場合
        if file.filename == '':
            flash('ファイルが選択されていません。', 'warning')
            return redirect(request.url)
            
        # ファイルが存在し、許可された拡張子の場合
        if file and allowed_file(file.filename):
            # ユニークなファイル名を生成 (UUIDを使用)
            # 例: original_filename.jpg -> uuid.jpg
            filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            try:
                file.save(filepath) # ファイルをサーバーに保存

                # 現在ログインしているユーザーのimageカラムを更新
                current_user.image = filename # データベースにはファイル名のみ保存
                db.session.commit()
                
                flash('プロフィール画像が正常にアップロードされました！', 'success')
                return redirect(url_for('home_match')) # マッチング画面にリダイレクト
            except Exception as e:
                flash(f'画像の保存中にエラーが発生しました: {e}', 'danger')
                return redirect(request.url)
        else:
            flash('許可されていないファイル形式です。PNG, JPG, JPEG, GIFのみアップロード可能です。', 'danger')
            return redirect(request.url)
    else:
        return render_template('imageupload.html')

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

# マッチング画面
@app.route('/home_match', methods=['GET', 'POST']) # ルート名を修正しました
@login_required
def home_match():
    # current_userはFlask-Loginによって提供される現在ログイン中のユーザーオブジェクト
    if current_user.is_authenticated:
        return render_template('match.html', user=current_user) # ユーザーオブジェクトをテンプレートに渡す
    else:
        # ログインしていない場合はホーム画面にリダイレクト
        flash('ログインが必要です。', 'info')
        return redirect(url_for('home'))

#プロフィール画面
@app.route('/profile/<string:user_id>')
@login_required
def profile(user_id):
    user_data = Users.query.get_or_404(user_id) # user_idに基づいてユーザーデータを取得
    return render_template('profile.html', user=user_data) # テンプレートにuserオブジェクトを渡す

# ログアウト
@app.route('/logout')
@login_required
def logout():
    logout_user() # ユーザーをログアウトさせる
    flash('ログアウトしました。', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # これがテーブルを作成するコマンドです (初回のみ実行)
    app.run(port=8888, debug=True)

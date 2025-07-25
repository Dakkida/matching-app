import sqlite3
from flask import Flask, render_template, request, session, flash, url_for, redirect
from forms import RegistrationForm # forms.py が必要です
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError
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
    # 0が男性、1が女性
    sex = db.Column(db.Integer, nullable=False)
    car = db.Column(db.String, nullable=False)
    # プロフィール画像のファイル名を保存するカラム
    image = db.Column(db.String, nullable=True)

    def get_id(self):
        # Flask-Loginがユーザーを識別するために使用するIDを返す
        return self.id_mailaddress

# マッチング関連のテーブル定義
class Matches(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.String, db.ForeignKey('users.id_mailaddress'), nullable=False)
    user2_id = db.Column(db.String, db.ForeignKey('users.id_mailaddress'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # リレーションシップ
    user1 = db.relationship('Users', foreign_keys=[user1_id], backref='matches_as_user1')
    user2 = db.relationship('Users', foreign_keys=[user2_id], backref='matches_as_user2')

class Swipes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    swiper_id = db.Column(db.String, db.ForeignKey('users.id_mailaddress'), nullable=False)
    swiped_id = db.Column(db.String, db.ForeignKey('users.id_mailaddress'), nullable=False)
    is_like = db.Column(db.Boolean, nullable=False)  # True=Like, False=Nope
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # リレーションシップ
    swiper = db.relationship('Users', foreign_keys=[swiper_id], backref='swipes_made')
    swiped = db.relationship('Users', foreign_keys=[swiped_id], backref='swipes_received')
    
    # 複合ユニーク制約（同じユーザーが同じ人を2回スワイプできない）
    __table_args__ = (db.UniqueConstraint('swiper_id', 'swiped_id', name='unique_swipe'),)

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
                # match.html はユーザーへの歓迎画面。実際のマッチングは matchdisplay.html
                return redirect(url_for('home_match')) 
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
                sex=int(form.gender.data),  # ここもint型に変換
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

@app.route('/home_match', methods=['GET', 'POST']) 
@login_required
def home_match():
    # current_userはFlask-Loginによって提供される現在ログイン中のユーザーオブジェクト
    if current_user.is_authenticated:
        # マッチング開始ページとして matchdisplay.html にリダイレクト
        return redirect(url_for('matchdisplay')) 
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

# マッチング画面を更新 (GETリクエストのみで動作させる)
@app.route('/matchdisplay', methods=['GET']) # POSTはAPIエンドポイントに移動
@login_required
def matchdisplay():
    return render_template('matchdisplay.html', user=current_user)

def get_next_profile_for_user(user_id):
    """ユーザーがまだスワイプしていない次のプロフィールを取得"""
    # 既にスワイプしたユーザーのIDを取得
    swiped_user_ids = db.session.query(Swipes.swiped_id).filter_by(swiper_id=user_id).all()
    swiped_ids = [row[0] for row in swiped_user_ids]
    
    # 自分以外で、まだスワイプしていないユーザーを取得
    next_user = Users.query.filter(
        Users.id_mailaddress != user_id,
        ~Users.id_mailaddress.in_(swiped_ids)
    ).first()
    
    return next_user

def record_swipe(swiper_id, swiped_id, is_like):
    """スワイプを記録し、マッチングをチェック"""
    try:
        # スワイプ記録
        new_swipe = Swipes(
            swiper_id=swiper_id,
            swiped_id=swiped_id,
            is_like=is_like
        )
        db.session.add(new_swipe)
        
        is_match = False
        if is_like:
            # 相手も自分をlikeしているかチェック
            mutual_like = Swipes.query.filter_by(
                swiper_id=swiped_id,
                swiped_id=swiper_id,
                is_like=True
            ).first()
            
            if mutual_like:
                # マッチング成立
                new_match = Matches(
                    user1_id=min(swiper_id, swiped_id),  # 小さい方のIDを user1 に
                    user2_id=max(swiper_id, swiped_id)   # 大きい方のIDを user2 に
                )
                db.session.add(new_match)
                is_match = True
        
        db.session.commit()
        
        return {
            'success': True,
            'is_match': is_match,
            'message': 'マッチしました！' if is_match else 'スワイプを記録しました'
        }
        
    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'message': f'エラーが発生しました: {str(e)}'
        }

# マッチング一覧画面
@app.route('/matches')
@login_required
def matches():
    """現在のユーザーのマッチング一覧を表示"""
    user_matches = Matches.query.filter(
        (Matches.user1_id == current_user.id_mailaddress) |
        (Matches.user2_id == current_user.id_mailaddress)
    ).all()
    
    # マッチした相手の情報を取得
    matched_users = []
    for match in user_matches:
        if match.user1_id == current_user.id_mailaddress:
            matched_users.append(match.user2)
        else:
            matched_users.append(match.user1)
    
    return render_template('matches.html', matches=matched_users, user=current_user)


# API: 次のプロフィールを取得
@app.route('/api/next-profile')
@login_required
def api_next_profile():
    """AJAX用の次のプロフィール取得API"""
    next_profile = get_next_profile_for_user(current_user.id_mailaddress)
    
    if next_profile:
        return {
            'success': True,
            'profile': {
                'id': next_profile.id_mailaddress,
                'name': next_profile.name,
                'school_year': next_profile.school_year,
                'course': next_profile.course,
                'hobby': next_profile.hobby,
                'time': next_profile.time,
                'image': next_profile.image,
                'sex': next_profile.sex
            }
        }
    else:
        return {'success': False, 'message': 'No more profiles'}

# API: スワイプ処理
@app.route('/api/swipe', methods=['POST'])
@login_required
def api_swipe():
    """AJAX用のスワイプ処理API"""
    data = request.get_json()
    target_user_id = data.get('target_user_id')
    action = data.get('action')  # 'like' or 'nope'
    
    if not target_user_id or action not in ['like', 'nope']:
        return {'success': False, 'message': 'Invalid request'}, 400
    
    is_like = action == 'like'
    result = record_swipe(current_user.id_mailaddress, target_user_id, is_like)
    
    return result

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # これがテーブルを作成するコマンドです (初回のみ実行)
        # 開発中にSwipesテーブルをクリアしたい場合は、以下のコメントを外して一度実行
        db.session.query(Swipes).delete()
        db.session.query(Matches).delete()
        db.session.commit()
        print("Swipes and Matches tables cleared for testing.")
    app.run(port=8888, debug=True)
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Regexp
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

class RegistrationForm(FlaskForm):
    name = StringField('お名前', validators=[
        DataRequired(message='お名前を入力してください'),
        Length(min=2, max=50, message='お名前は2文字以上50文字以内で入力してください')
    ])
    
    email = StringField('メールアドレス', validators=[
        DataRequired(message='メールアドレスを入力してください'),
        Email(message='有効なメールアドレスを入力してください')
    ])
    
    password = PasswordField('パスワード', validators=[
        DataRequired(message='パスワードを入力してください'),
        Length(min=8, max=20, message='パスワードは8文字以上20文字以内で入力してください'),
        Regexp(r'^[a-zA-Z0-9]+$', message='パスワードは英字と数字のみ使用できます')
    ])
    
    confirm_password = PasswordField('パスワード確認', validators=[
        DataRequired(message='パスワード確認を入力してください'),
        EqualTo('password', message='パスワードが一致しません')
    ])
    
    year = SelectField('学年', choices=[
        ('', '学年を選択してください'),
        ('1', '1年生'),
        ('2', '2年生'),
        ('3', '3年生'),
        ('4', '4年生'),
        ('5', '5年生'),
        ('6', '6年生'),
        ('7', '大学院生')
    ], validators=[DataRequired(message='学年を選択してください')])
    
    course = SelectField('学部', choices=[
        ('', '学部を選択してください'),
        ('人文社会学部', '人文社会学部'),
        ('国際地域創造学部', '国際地域創造学部'),
        ('教育学部', '教育学部'),
        ('理学部', '理学部'),
        ('医学部', '医学部'),
        ('工学部', '工学部'),
        ('農学部', '農学部'),
        ('大学院', '大学院')
    ], validators=[DataRequired(message='学部を選択してください')])
    
    gender = SelectField('性別', choices=[
        ('', '選択してください'),
        ('0', '男性'),
        ('1', '女性')
    ], validators=[DataRequired(message='性別を選択してください')])

    time = StringField('時間割', validators=[
        DataRequired(message='時間割を入力してください'),
        Length(max=100, message='時間割は100文字以内で入力してください')
    ])
    
    hobby = StringField('趣味', validators=[
        DataRequired(message='趣味を入力してください'),
        Length(max=200, message='趣味は200文字以内で入力してください')
    ])
    
    license = BooleanField('運転免許')
    
    car = StringField('車の車種', validators=[
        Length(max=50, message='車種は50文字以内で入力してください')
    ])
    
    submit = SubmitField('アカウント作成')
    
    def validate_email(self, field):
        """メールアドレスのカスタムバリデーション"""
        if not field.data.endswith('@ie.u-ryukyu.ac.jp'):
            raise ValidationError('琉球大学のメールアドレス（@ie.u-ryukyu.ac.jp）を使用してください')
    
    def validate_password(self, field):
        """パスワードのカスタムバリデーション"""
        # 英字と数字の両方が含まれているかチェック
        if not re.search(r'[a-zA-Z]', field.data):
            raise ValidationError('パスワードには英字を含める必要があります')
        if not re.search(r'[0-9]', field.data):
            raise ValidationError('パスワードには数字を含める必要があります')
    
    def validate_car(self, field):
        """車種のカスタムバリデーション"""
        if self.license.data and not field.data:
            raise ValidationError('運転免許をお持ちの場合、車種を入力してください')


class LoginForm(FlaskForm):
    email = StringField('メールアドレス', validators=[
        DataRequired(message='メールアドレスを入力してください'),
        Email(message='有効なメールアドレスを入力してください')
    ])
    
    password = PasswordField('パスワード', validators=[
        DataRequired(message='パスワードを入力してください')
    ])
    
    submit = SubmitField('ログイン')
    
    def validate_email(self, field):
        """ログイン時のメールアドレスバリデーション"""
        if not field.data.endswith('@ie.u-ryukyu.ac.jp'):
            raise ValidationError('琉球大学のメールアドレス（@ie.u-ryukyu.ac.jp）を使用してください')

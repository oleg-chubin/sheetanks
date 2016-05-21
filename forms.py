from wtforms import Form, StringField, validators


class LoginForm(Form):
    nickrst_name = StringField(u'Nickname', validators=[validators.input_required()])

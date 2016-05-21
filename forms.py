from wtforms import Form, StringField, validators, SelectField


class LoginForm(Form):
    nickname = StringField(u'Nickname', validators=[validators.input_required()])


class HangarForm(Form):
    vehicle = SelectField(u'Vehicle', choices=[('1', "T-34"), ('2', "T43")])

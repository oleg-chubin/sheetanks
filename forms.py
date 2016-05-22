from wtforms import Form, StringField, validators, RadioField, widgets


class LoginForm(Form):
    nickname = StringField(u'Nickname', validators=[validators.input_required()])


def select_multi_checkbox(field, ul_class='', **kwargs):
    kwargs.setdefault('type', 'radio')
    field_id = kwargs.pop('id', field.id)
    html = [u'<ul %s>' % widgets.html_params(id=field_id, class_=ul_class)]
    for value, label, checked in field.iter_choices():
        choice_id = u'%s-%s' % (field_id, value)
        options = dict(kwargs, name=field.name, value=value, id=choice_id)
        if checked:
            options['checked'] = 'checked'
        html.append(u'<li><input %s /> ' % widgets.html_params(**options))
        html.append(u'<label for="%s">%s</label></li>' % (field_id, label))
    html.append(u'</ul>')
    return u''.join(html)


class HangarForm(Form):
    vehicle = RadioField(
        u'Vehicle', choices=[('t34', "T-34"), ('t43', "T43")],
        widget=select_multi_checkbox
    )

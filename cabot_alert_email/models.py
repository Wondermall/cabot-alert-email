from os import environ as env
from django.conf import settings
from cabot.cabotapp.alert import AlertPlugin
from sparkpost import SparkPost
from django.template import Context, Template
import logging

email_template = """Service {{ service.name }} {{ scheme }}://{{ host }}{% url 'service' pk=service.id %} {% if service.overall_status != service.PASSING_STATUS %}alerting with status: {{ service.overall_status }}{% else %}is back to normal{% endif %}.
{% if service.overall_status != service.PASSING_STATUS %}
CHECKS FAILING:{% for check in service.all_failing_checks %}
  FAILING - {{ check.name }} - Type: {{ check.check_category }} - Importance: {{ check.get_importance_display }}{% endfor %}
{% if service.all_passing_checks %}
Passing checks:{% for check in service.all_passing_checks %}
  PASSING - {{ check.name }} - Type: {{ check.check_category }} - Importance: {{ check.get_importance_display }}{% endfor %}
{% endif %}
{% endif %}
"""


class EmailSPAlert(AlertPlugin):

    name = "SP Email"
    author = "Roman Kournjaev"

    def send_alert(self, service, users, duty_officers):
        emails = [u.email for u in users if u.email]
        if not emails:
            return
        if service.overall_status != service.PASSING_STATUS:
            if service.overall_status == service.CRITICAL_STATUS:
                emails += [u.email for u in users if u.email]
            subject = '%s status for service: %s' % (service.overall_status, service.name)
        else:
            subject = 'Service back to normal: %s' % (service.name,)
        c = Context({
            'service': service,
            'host': settings.WWW_HTTP_HOST,
            'scheme': settings.WWW_SCHEME
        })
        sp = SparkPost(env.get('SPARKPOST_API_KEY'))
        t = Template(email_template)
        response = sp.transmissions.send(
            recipients=emails,
            text=t.render(c),
            from_email='Cabot <%s>' % env.get('CABOT_FROM_EMAIL'),
            subject=subject,
            track_opens=False,
            track_clicks=False,
            reply_to='no-reply@int.wmmails.com'
        )
        logging.info(response)
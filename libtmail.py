import email
import mimetypes
import os
import smtplib

import jinja2

import nominal

COMMASPACE = ", "

class ConnectionStatus(nominal.Nominal):
    DISCONNECTED = 0
    CONNECTED = 1
    STATUSES = [DISCONNECTED, CONNECTED]

    def __init__(self, value):
        if not value in self.STATUSES:
            raise ValueError("Invalid connection status %s" % value)
        nominal.Nominal.__init__(self, value)
#-- class ConnectionStatus --#


class DebugStatus(nominal.Nominal):
    OFF = 0
    ON = 1
    STATUSES = [OFF, ON]

    def __init__(self, value):
        if not value in self.STATUSES:
            raise ValueError("Invalid debug status %s" % value)
        nominal.Nominal.__init__(self, value)
#-- class DebugStatus --#


class EmailAccount(object):
    """Represents an email account on a remote SMTP server. Can be put in
    debug mode to show emails being sent.

    """
    def __init__(self, host, username, password):
        self._host = host
        self._username = username
        self._password = password
        self._connection = None
        self._connection_status = ConnectionStatus(ConnectionStatus.DISCONNECTED)
        self._debug_status = DebugStatus(DebugStatus.OFF)

    def next_email(self, email):
        if not isinstance(email, Tmail):
            raise TypeError("%s is not a Tmail" % email)
        from_addrs = email.from_addrs
        to_addrs = email.to_addrs + email.cc_addrs + email.bcc_addrs
        if self._debug_status.value == DebugStatus.ON:
            print "To send to: %s" % to_addrs
            print email
        elif self._connection_status.value == ConnectionStatus.CONNECTED:
            print "Sending to " + to_addrs
            self._connection.sendmail(from_addrs, to_addrs, str(email))
    next_email = property(fset=next_email)

    @property
    def connection_status(self):
        return self._connection_status

    @connection_status.setter
    def connection_status(self, status):
        if not isinstance(status, ConnectionStatus):
            raise TypeError("%s is not a ConnectionStatus" % status)
        if status != self._connection_status:
            if status.value == ConnectionStatus.CONNECTED:
                self._connect()
            elif status.value == ConnectionStatus.DISCONNECTED:
                self._disconnect()
            self._connection_status = status

    @property
    def debug_status(self):
        return self._debug_status

    @debug_status.setter
    def debug_status(self, status):
        if not isinstance(status, DebugStatus):
            raise TypeError("%s is not a DebugStatus" % status)
        if status != self._debug_status:
            self._debug_status = status

    def _connect(self):
        self._connection = smtplib.SMTP(self._host)
        self._connection.starttls()
        self._connection.ehlo()
        self._connection.login(self._username, self._password)

    def _disconnect(self):
        self._connection.quit()
#-- class EmailAccount --#


class Templatizer(object):
    """Represents a templating engine. Currently implemented with Jinja2.
    Caches templates loaded from the filesystem.

    """
    def __init__(self):
        self._options = None
        self._templates = {}
        self._environment = jinja2.Environment(trim_blocks=True,
                                               autoescape=False)

    @property
    def result(self):
        return self._current_template.render(self._options)

    def options(self, options):
        self._options = options
    options = property(fset=options)

    def template(self, template):
        if os.path.isfile(template):
            if not template in self._templates:
                self._load_template(template)
            self._current_template = self._templates[template]
        else:
            self._current_template = self._environment.from_string(template)
    template = property(fset=template)

    def _load_template(self, template_path):
        template_dir, template_name = os.path.split(os.path.abspath(template_path))
        self._environment.loader = jinja2.FileSystemLoader(template_dir)
        self._templates[template_path] = self._environment.get_template(template_name)
#-- class Templatizer --#


class Tmail(object):
    """Represents a templatized email. Supports templates in both the
    subject and the body. Defaults to a multipart/mixed MIME type so that
    attachments can be added.

    """
    def __init__(self, templatizer=None, options={}):
        self._message = email.MIMEMultipart.MIMEMultipart()
        self._message["Date"] = email.Utils.formatdate(localtime=True)
        self._templatizer = templatizer
        if templatizer is None:
            self._templatizer = Templatizer()
        self._templatizer.options = options

    @property
    def templatizer(self):
        return self._templatizer

    @property
    def from_addrs(self):
        return self._message["From"].split(COMMASPACE)

    @from_addrs.setter
    def from_addrs(self, from_addrs):
        if not isinstance(from_addrs, list):
            raise TypeError("%s is not a list" % from_addrs)
        self._message["From"] = COMMASPACE.join(from_addrs)
        self._message["Reply-To"] = from_addrs[0]

    @property
    def to_addrs(self):
        if self._message["To"] is None:
            return []
        return self._message["To"].split(COMMASPACE)

    @to_addrs.setter
    def to_addrs(self, to_addrs):
        if not isinstance(to_addrs, list):
            raise TypeError("%s is not a list" % to_addrs)
        self._message["To"] = COMMASPACE.join(to_addrs)

    @property
    def cc_addrs(self):
        if self._message["Cc"] is None:
            return []
        return self._message["Cc"].split(COMMASPACE)

    @cc_addrs.setter
    def cc_addrs(self, cc_addrs):
        if not isinstance(cc_addrs, list):
            raise TypeError("%s is not a list" % cc_addrs)
        self._message["Cc"] = COMMASPACE.join(cc_addrs)

    @property
    def bcc_addrs(self):
        if self._message["Bcc"] is None:
            return []
        return self._message["Bcc"].split(COMMASPACE)

    @bcc_addrs.setter
    def bcc_addrs(self, bcc_addrs):
        if not isinstance(bcc_addrs, list):
            raise TypeError("%s is not a list" % bcc_addrs)
        self._message["Bcc"] = COMMASPACE.join(bcc_addrs)

    @property
    def subject(self):
        return self._message["Subject"]

    @subject.setter
    def subject(self, subject_template):
        self._templatizer.template = subject_template
        self._message["Subject"] = self._templatizer.result

    def body(self, body_template):
        if os.path.isfile(body_template):
            ctype, encoding = mimetypes.guess_type(body_template)
        if ctype is None or encoding is not None:
            ctype = "text/plain"
        maintype, subtype = ctype.split('/', 1)
        if maintype != "text":
            raise TypeError("%s is not a valid body template", body_template)
        self._templatizer.template = body_template
        body = email.MIMEText.MIMEText(self._templatizer.result, subtype)
        self._message.attach(body)
    body = property(fset=body)

    def next_attachment(self, attachment_path):
        if not os.path.isfile(attachment_path):
            raise TypeError("%s is not a file" % attachment_path)
        ctype, encoding = mimetypes.guess_type(attachment_path)
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split('/', 1)
        with open(attachment_path, "rb") as f:
            attachment = email.MIMEBase.MIMEBase(maintype, subtype)
            attachment.set_payload(f.read())
        if not maintype in ["audio", "image", "text"]:
            email.encoders.encode_base64(attachment)
        attachment.add_header("Content-Disposition", "attachment",
                              filename=os.path.split(attachment_path)[1])
        self._message.attach(attachment)
    next_attachment = property(fset=next_attachment)

    def __str__(self):
        return self._message.as_string()
#-- class Tmail --#

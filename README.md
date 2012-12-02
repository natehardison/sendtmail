sendtmail
---------
Generates and sends emails based on a CSV template. Useful
for Gmail and for sending customized attachments to each
recipient.

DEPENDENCIES:
- Jinja2: http://jinja.pocoo.org/docs/ (easy_install Jinja2)
- Python 2.7.1 or greater (only tested on 2.7.1)

How to use:

1. Create a CSV "workfile" containing all of your email details. Each row
   should contain header info (FROM, TO, CC, BCC, and SUBJECT). FROM is
   required, as is at least one of TO, CC, and BCC. SUBJECT is optional.
2. BODY should be a path (absolute or relative to the location of the CSV
   workfile) to a template file that uses Jinja2 templating syntax (see
   http://jinja.pocoo.org/docs/templates/ for details). Each row can have
   a different value for BODY if you want.
3. SUBJECT should just be a string in the CSV, though it can also use
   Jinja2 template syntax. (BODY can also be a string.)
4. Fields beginning with ATTACHMENT should be paths (again, absolute or
   relative to the location of the CSV workfile) to attachment files.
5. You also need to create a file containing the details of the account to
   which you want to connect. This file needs to have 3 lines, with the
   SMTP host and port on the first, the user account on the second, and
   the account password on the third.
6. Run sendtmail <workfile> <account file> to use. By default sendtmail
   runs in debug mode and will print out all of the templatized emails
   without sending them. Set --debug=False to send.

The following templates are provided as examples:

- Email account file: "sample@emailaccountfile.com"
- Email template: "sample_email_template"
- Workfile: "sample_workfile.csv"

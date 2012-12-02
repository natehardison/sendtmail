#!/usr/bin/python

# sendtmail
# ------------
# Last updated 12/01/12
#
# Generates and sends emails based on a CSV template. Useful
# for Gmail and for sending customized attachments to each
# recipient.
#
# DEPENDENCIES:
# - Jinja2: http://jinja.pocoo.org/docs/ (easy_install Jinja2)
# - Python 2.7.1 or greater (only tested on 2.7.1)
#
# How to use:
#
# 1) Create a CSV "workfile" containing all of your email details.
#    Each row should contain header info (FROM, TO, CC, and BCC)
#    for a single recipient. BODY and SUBJECT are also required.
# 2) BODY should be a path (absolute or relative to the location
#    of the CSV workfile) to a template file that uses Jinja2
#    templating syntax (see http://jinja.pocoo.org/docs/templates/
#    for details). Each row can have a different value for BODY
#    if you want.
# 3) SUBJECT should just be a string in the CSV, though it can
#    also use Jinja2 template syntax.
# 4) If there is a field called ATTACHMENT in the CSV, it should
#    point to a file to attach to the email (absolute or relative
#    path just like BODY). Right now this script only supports one
#    attachment.
# 5) You also need to create a file containing the details
#    of the account to which you want to connect. This file
#    needs to have 3 lines, with the SMTP host and port on 
#    the first, the user account on the second, and the account
#    password on the third.
# 6) Run sendtmail <workfile> <account file> to use. By default
#    this is set up in debug mode

import argparse
import csv
import os

import libtmail

EMAIL_HEADERS = ["FROM", "TO", "CC", "BCC", "SUBJECT", "BODY"]

def parse_account_info(filename):
    with open(filename, 'rU') as account_file:
        host = account_file.readline().strip()
        username = account_file.readline().strip()
        password = account_file.readline().strip()
        return (host, username, password)

def main():
    parser = argparse.ArgumentParser(description='Generate and send templatized emails')
    parser.add_argument('workfile',
        help='a CSV file describing the emails to send (headers, attachments, etc.)')
    parser.add_argument('account',
        help='a file containing the email account details to send from')
    parser.add_argument('-d', '--debug', default=True,
        help='set =False to send emails')
    args = parser.parse_args()
    
    smtp_host, username, password = parse_account_info(args.account)
    email_account = libtmail.EmailAccount(smtp_host, username, password)
    print "Establishing connection to %s as %s." % (smtp_host, username)
    email_account.connection_status = libtmail.ConnectionStatus(libtmail.ConnectionStatus.CONNECTED)
    print "Successfully connected."

    if args.debug:
        email_account.debug_status = libtmail.DebugStatus(libtmail.DebugStatus.ON)
    else:
        # If not in debug mode, ask for confirmation before continuing
        response = raw_input("Are you sure you want to send emails (y/n)? ")
        if response != 'y':
            print "Exiting."
            email_account.connection_status = libtmail.ConnectionStatus(libtmail.ConnectionStatus.DISCONNECTED)
            return 0
        
    # We need to change into the same directory as the template file
    # since we'll need to resolve any relative paths it contains relative
    # to its position, not ours
    original_dir = os.getcwd()
    workfile_path = os.path.abspath(args.workfile)
    os.chdir(os.path.dirname(workfile_path))

    with open(workfile_path, 'rU') as workfile:

        # DictReader pulls out each row of CSV as a dict and
        # uses first row as keys
        workfile_reader = csv.DictReader(workfile)

        templatizer = libtmail.Templatizer()

        # Each row in the CSV workfile builds one email
        for row in workfile_reader:
            options = {}
            attachments = []
            for k, v in row.iteritems():
                if k.startswith("ATTACHMENT"):
                    attachments.append(v)
                elif not k in EMAIL_HEADERS:
                    options[k] = v
            tmail = libtmail.Tmail(templatizer, options)
            if not row["FROM"]:
                raise "Cannot send email without a FROM address"
            tmail.from_addrs = row["FROM"].split(',')
            if row["TO"]:
                tmail.to_addrs = row["TO"].split(',')
            if row["CC"]:
                tmail.cc_addrs = row["CC"].split(',')
            if row["BCC"]:
                tmail.bcc_addrs = row["BCC"].split(',')
            tmail.subject = row["SUBJECT"]
            tmail.body = row["BODY"]
            for attachment in attachments:
                tmail.next_attachment = attachment
            email_account.next_email = tmail
	
    os.chdir(original_dir)

    email_account.connection_status = libtmail.ConnectionStatus(libtmail.ConnectionStatus.DISCONNECTED)

if __name__ == '__main__':
    main()

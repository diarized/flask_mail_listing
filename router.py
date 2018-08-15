#!/usr/bin/env python3

import flask
import mailbox
import email
import os
import body_parser
import glob
import pagination


app = flask.Flask(__name__)

app.jinja_env.globals['url_for_other_page'] = pagination.url_for_other_page


@app.route('/favicon.ico')
def favicon():
    return flask.send_from_directory(os.path.join(app.root_path, 'static'),
                                     'favicon.ico',
                                     mimetype='image/vnd.microsoft.icon')


class MailFolder(mailbox.Maildir):
    def paging(self, items, page=1, size=20):
        if page < 1 or page > len(items)+size/size:
            raise IndexError('Wrong paging')
        return items[(page-1)*size:page*size]

    def get_messages_list(self, items=None):
        messages_list = []
        if not items:
            items = self.items()
        for item in items:
            message_file_name = item[0]
            message = item[1]
            message_basic_data = {}
            for header in ['From', 'Subject']:
                header_value = message.get(header)
                try:
                    if len(header_value) > 64:
                        header_value = header_value[:64] + "..."
                except TypeError: # FIXME: TypeError: object of type 'Header' has no len()
                    pass
                message_basic_data[header] = header_value
            message_basic_data['file_name'] = message_file_name
            messages_list.append(message_basic_data)
        return messages_list

    def get_folder(self, folder):
        subfolder = super(MailFolder, self).get_folder(folder)
        subfolder.__class__ = MailFolder
        return subfolder


PER_PAGE = 20


@app.route('/mail/', defaults={'folder': 'INBOX', 'page': 1})
@app.route('/mail/<string:folder>/', defaults={'page': 1})
@app.route('/mail/<string:folder>/<int:page>')
def list_folder_emails(folder, page):
    maildir_root = '/home/artur/Maildir'
    maildir = MailFolder(maildir_root)
    if folder != 'INBOX':
        if not folder in maildir.list_folders():
            flask.abort(flask.make_response('No such mail folder: '+folder, 416))
        else:
            maildir = maildir.get_folder(folder)
    messages_list = maildir.get_messages_list()
    count = len(messages_list)
    paging = pagination.Pagination(page, PER_PAGE, count)
    return flask.render_template('mails_list.html', messages=messages_list, maildir_folder=folder, pagination=paging)



@app.route('/mail/<string:folder_name>/<string:message_file_name>')
def message_from_folder(folder_name, message_file_name):
    mail_root_dir = '/home/artur/Maildir'
    maildir = mailbox.Maildir(mail_root_dir)
    if folder_name == 'INBOX':
        folder_name = ''
    elif folder_name in maildir.list_folders():
        folder_name = '.' + folder_name
    else:
        flask.abort(folder + ': No such mail folder', 416)
    full_mail_path = os.path.join(mail_root_dir, folder_name, 'cur', message_file_name)
    matching_files = glob.glob(full_mail_path + '*') # Ends with something like ':2:a'
    if len(matching_files) > 1:
        flask.abort(flask.make_response("Can't find the message file:<br />"+full_mail_path, 500))
    mail_filename = matching_files[0]
    with open(mail_filename) as fh:
        try:
            message = email.message_from_file(fh)
        except UnicodeDecodeError as e:
            flask.abort(flask.make_response(str(e), 500))
    headers = dict(message.items())
    body = body_parser.all_bodies(message, 'text/html')
    return flask.render_template('email.html', headers=headers, body=body)


app.run(host='0.0.0.0', port=5556, debug=True)

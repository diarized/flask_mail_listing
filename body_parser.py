import re
import email.charset
from pathlib import Path
from glob import glob
from email import message_from_binary_file, policy

RE_QUOPRI_BS = re.compile(r'\b=20=\n')
RE_QUOPRI_LE = re.compile(r'\b=\n')
RE_LONG_WORDS = re.compile(r'\b[\w\/\+\=\n]{72,}\b')

email.charset.ALIASES.update({
    'iso-8859-8-i': 'iso-8859-8',
    'x-mac-cyrillic': 'mac-cyrillic',
    'macintosh': 'mac-roman',
    'windows-874': 'cp874',
    # manually fix unknown charset encoding
    'default': 'utf-8',
    'x-unknown': 'utf-8',
    '%charset': 'utf-8',
})

def extract_body(msg, body=None):
    """ Extract content body of an email messsage """
    if not body:
        body = {}
    content_type = msg.get_content_type()
    if msg.is_multipart():
        for part in msg.get_payload():
            if part.is_multipart():
                extract_body(part, body)
            else:
                part_content_type = part.get_content_type()
                if part_content_type.startswith("text/"):
                    try:
                        body[part_content_type].append(part.get_payload())
                    except KeyError:
                        body[part_content_type] = [part.get_payload()]
    elif content_type.startswith("text/"):
        charset = msg.get_param('charset', 'utf-8').lower()
        charset = email.charset.ALIASES.get(charset, charset)
        msg.set_param('charset', charset)
        try:
            body[content_type].append(msg.get_payload())
        except AssertionError as e:
            print('Parsing failed.    ')
            print(e)
        except KeyError:
            body[content_type] = [msg.get_payload()]
        except LookupError:
            # set all unknown encoding to utf-8
            # then add a header to indicate this might be a spam
            msg.set_param('charset', 'utf-8')
            body[content_type].append('=== <UNKOWN ENCODING POSSIBLY SPAM> ===')
            body[content_type].append(msg.get_payload())
    return body


def read_emails(dirpath):
    """ Read all emails under a directory
    Returns:
      a iterator. Use
          for x in read_emails():
              print(x)
      to access the emails.
    """
    dirpath = os.path.expanduser(dirpath)
    print('%s/data/inmail.*' % dirpath)
    for filename in glob('%s/data/inmail.*' % dirpath):
        print('Read %s' % filename, end='\r')
        msg = message_from_binary_file(open(filename, mode="rb"),
                                       policy=policy.default)
        body = '\n\n'.join(extract_body(msg))
        # remove potential quote print formatting strings
        body = RE_QUOPRI_BS.sub('', body)
        body = RE_QUOPRI_LE.sub('', body)
        body = RE_LONG_WORDS.sub('', body)
        yield {
            "_id": os.path.basename(filename).replace('.', '_'),
            "subject": msg['subject'],
            "text": body or ''
        }

def all_bodies(msg, preferred_conten_type='text/plain'):
    bodies = extract_body(msg)
    try:
        body = '\n\n'.join(bodies[preferred_conten_type])
    except KeyError:
        try:
            body = '\n\n'.join(bodies['text/html'])
        except KeyError:
            try:
                body = '\n\n'.join(bodies['text/plain'])
            except KeyError:
                return None
    # remove potential quote print formatting strings
    body = RE_QUOPRI_BS.sub('', body)
    body = RE_QUOPRI_LE.sub('', body)
    body = RE_LONG_WORDS.sub('', body)
    return body

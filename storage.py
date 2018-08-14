import psycopg2 as sql


def db_connect(pg_database):
    with open('../passwords') as fh:
        credentials = [line.strip().split(':') for line in fh.readlines()]
    pg_user = credentials['pg_user']
    pg_pass = credentials['pg_pass']
    connection = sql.connect(database=pg_database, user=pg_user, password=pg_pass)
    return connection


def insert_header(cursor, message_id, header, value):
    # decoded_header = email.header.make_header(email.header.decode_header(header))
    # cursor.execute("INSERT INTO mails VALUES (%s, %s, %s)", (message_id, str(decoded_header), value))
    cursor.execute("INSERT INTO mails VALUES (%s, %s, %s)", (message_id, header, value))


def save_headers(message_headers):
    try:
        connection = db_connect('mail_storage')
        cursor = connection.cursor()
        try:
            message_id = message_headers['Message-ID'].strip('<>')
        except KeyError:
            pprint.pprint(message_headers)
            raise
        [insert_header(cursor, message_id, header.strip('<>'), message_headers[header])
                for header
                in message_headers
                if header != 'Message-ID'
        ]
        connection.commit()
    except:
        connection.rollback()
    finally:
        connection.close()


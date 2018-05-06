import httplib2
import base64
import os
from tqdm import tqdm
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from requests_html import HTML


# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'geemailz'

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def fetch_snippets():

    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    labels = service.users().labels().list(userId='me').execute()['labels']
    bookmarked = list(filter(lambda l: l['name'] == 'Bookmarked sites', labels))[0]
    msgs = service.users().messages().list(labelIds=[bookmarked['id']], userId='me', maxResults=500).execute()
    contents = []

    print("Fetching Messages...")
    for msg in tqdm(msgs['messages']):
        message = service.users().messages().get(id=msg['id'], userId='me').execute()
        filtered = list(filter(lambda x: x['mimeType'] == 'text/html', message['payload']['parts']))
        subject = list(filter(lambda h: h['name'] == 'Subject', message['payload']['headers']))[0]['value']
        if not filtered:
            print(message)
            continue
        else:
            data = filtered[0]
        content = base64.urlsafe_b64decode(data['body']['data']).decode('utf-8')
        contents.append((subject, content))

    return contents

if __name__ == "__main__":

    contents = fetch_snippets()

    print("Saving Emails...")
    with open('emails.txt', 'w') as f:
        for content in tqdm(contents):
            line = " ~~ ".join(content)
            f.write(f"{line}\n")

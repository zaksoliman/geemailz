import httplib2
import base64
import os
import pickle
from tqdm import tqdm
from apiclient import discovery
from oauth2client import client, tools
from oauth2client.file import Storage
from requests_html import HTML
from apiclient.discovery import build
from httplib2 import Http

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
    store = Storage('credentials.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        creds = tools.run_flow(flow, store)
    return creds

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
        parts = message['payload'].get('parts')
        filtered = []
        subject = []
        if parts:
            filtered = list(filter(lambda x: x['mimeType'] == 'text/html', parts))
            subject = list(filter(lambda h: h['name'] == 'Subject', message['payload']['headers']))[0]['value']
        if not filtered:
            contents.append((msg['id'],))
        else:
            data = filtered[0]
            content = base64.urlsafe_b64decode(data['body']['data']).decode('utf-8')
            contents.append((msg['id'], subject, content))

    return contents

if __name__ == "__main__":

    contents = fetch_snippets()

    print("Saving emails to pickle...")
    with open('emails.pkl', 'wb') as f:
        pickle.dump(file=f, obj=contents)

    print("Saving emails to txt...")
    with open('emails.txt', 'w') as f:
        for content in tqdm(contents):
            line = " ~~ ".join(content)
            f.write(f"{line}\n")

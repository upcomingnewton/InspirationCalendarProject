from __future__ import print_function
import httplib2
import os

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

import datetime
import sys

try:
    import argparse
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    parser.add_argument('-f', help="quotes file name")
    parser.add_argument('-t', help="time between events in minutes")
    parser.add_argument('-n', help="number of events to run in one go of this script")
    parser.add_argument('-c', help="calendar id")
    parser.add_argument('-s', help="show calendar summary and id and exit")
    flags = parser.parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'InspirationCalendarProject'


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
                                   'calendar-python-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
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

def get_calender_client():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    return service

def get_present_time():  
    #return datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    return datetime.datetime.utcnow()

def get_events(service,now,cal,end_time):
    eventsResult = service.events().list(
        calendarId=cal,  singleEvents=True,timeMin=end_time,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])
    return events
        #start = event['start'].get('dateTime', event['start'].get('date'))
        #print(start, event['summary'])
 
def read_quotes_file(filepath):
  f = open(filepath)
  data = [x.strip() for x in f.readlines()]
  f.close()
  return data

def write_quotes_file(filepath,data,num_quotes_to_move=0):
  f = open(filepath,"w")
  # move num_quotes_to_move to end of file
  first_num_quotes_to_move = data[:num_quotes_to_move]
  other_lines = data[num_quotes_to_move:]
  new_data = "\n".join(other_lines + first_num_quotes_to_move)
  f.write(new_data)
  f.close()
  
def insert_event(service,cid,event):
    event = service.events().insert(calendarId=cid, body=event).execute()
    print(event.get("id"))

if __name__ == '__main__':
  """
  1. we need to create next num events, 1 event every x secs
  2. if we find an event already created for that time, we wont create an event
  3. find timestamps to create an event
  4. check if event is created for that time, if not, mark it
  5. read quotes from file and create events
  6. delete all previous events than previous day
  """
  now = get_present_time()
  timestamps = [now + datetime.timedelta(minutes = int(flags.t)*i) for i in range(1,int(flags.n)+1)]
  # get events till timestamps[-1] 
  service = get_calender_client()
  if flags.s:
    page_token = None
    while True:
      calendar_list = service.calendarList().list(pageToken=page_token).execute()
      for calendar_list_entry in calendar_list['items']:
          print ("{0}\t\t{1}".format(calendar_list_entry["summary"],calendar_list_entry["id"]))
      page_token = calendar_list.get('nextPageToken')
      if not page_token:
        break
  else:
    events = get_events(service,now,cal=flags.c,end_time=timestamps[-1].isoformat() + 'Z')
    event_start_times = [event['start'].get('dateTime') for event in events]
    events_to_create_at = [x for x in timestamps if x not in event_start_times]
    num_quotes = len(events_to_create_at)   
    all_quotes = read_quotes_file(flags.f)
    quotes = all_quotes[:num_quotes]
    for (start_time,quote) in zip(events_to_create_at,quotes):
        print(start_time,quote)
        stime = start_time.isoformat() + 'Z'
        etime = (start_time + datetime.timedelta(minutes =2)).isoformat() + 'Z'
        insert_event(service,flags.c,{'summary':quote,'start':{'dateTime':stime},'end':{'dateTime':etime}})
    write_quotes_file(flags.f,all_quotes,num_quotes)
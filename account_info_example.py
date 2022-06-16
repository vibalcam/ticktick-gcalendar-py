# actual information should be placed in a file named account_info.py

GOOGLE = {
    'TOKEN_FILENAME': 'token.json',
    'SCOPES': ['https://www.googleapis.com/auth/calendar.events'],
    'credentials': 'credentials_google.json',
}

GOOGLE_INFO = {
    'old_filename': 'google_calendar.list',
    # TODO MUST CHANGE TO ACTUAL VALUES
    # google calendars that WILL be synced
    'calendar_ids': ['fasdfadfafdsa@group.calendar.google.com'],  # calendar id,
    # TODO MUST CHANGE TO ACTUAL VALUES
    # google calendar where events added in ticktick will be added
    'default_project_id': 'fdsafasdffas@group.calendar.google.com',
}

# TODO COMPLETE WITH API LOGIN INFORMATION
TICKTICK = {
    'CLIENT_ID': '',
    'CLIENT_SECRET': '',
    'REDIRECT_URI': 'http://127.0.0.1:8080',    # change if different redirect ui
    'TOKEN_FILENAME': '.token-oauth',
    'USERNAME': '',
    'PWD': '',
}

TICKTICK_INFO = {
    'old_filename': 'tick_tasks.list',
    # TODO MUST CHANGE TO ACTUAL VALUES
    # projects that WILL NOT be synced
    'EXCLUDED_PROJECTS': ['4fsd5a64fa65sd4f'],  # excluded projects ids
    # TODO MUST CHANGE TO ACTUAL VALUES
    # ticktick project where events added in google will be added
    'default_project_id': '4f56dsa4f65as4df65a',
}

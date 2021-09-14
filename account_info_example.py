# actual information should be placed in a file named account_info.py

GOOGLE = {
    'TOKEN_FILENAME': 'token.json',
    'SCOPES': ['https://www.googleapis.com/auth/calendar.events'],
    'credentials': 'credentials_google.json',
}

GOOGLE_INFO = {
    'old_filename': 'google_calendar.list',
    # MUST CHANGE TO ACTUAL VALUES
    'calendar_ids': ['fasdfadfafdsa@group.calendar.google.com'],  # calendar id,
    # MUST CHANGE TO ACTUAL VALUES
    'default_project_id': 'fdsafasdffas@group.calendar.google.com',
}

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
    # MUST CHANGE TO ACTUAL VALUES
    'EXCLUDED_PROJECTS': ['4fsd5a64fa65sd4f'],  # excluded projects ids
    # MUST CHANGE TO ACTUAL VALUES
    'default_project_id': '4f56dsa4f65as4df65a',
}

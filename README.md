# ticktick-gcalendar-py

## Requirements

Meet the following requirements:
- ticktick-py: https://github.com/lazeroffmichael/ticktick-py
- google calendar python: https://developers.google.com/tasks/quickstart/python
- Set up info in account_info.py (you can use account_info_example.py as template and info from -p option to get TickTick calendar ids)

# Use

- Run ticktick-gcalendar.py with -p option to check TickTick lists' ids
- Set up account_info.py
- Run ticktick-gcalendar.py with -r option to renew tokens
- Run ticktick-gcalendar.py with no options
- Run ticktick-gcalendar.py with -rt or -rg to delete an id from memory

## Features

It uses the package ticktick-py and google calendar for python to sync between Ticktick and Google Calendar.

It is set up so the sync occurs in the following way:
- It syncs the changes in the selected lists of Ticktick to a specific calendar in Google Calendar
- It syncs the selected calendars in Google Calendar to a specific calendar in Ticktick

## Warnings

- Works with python 3.9.5
- Inbox is exclude by default (to change this look at ticktick-gcalendar.py in TickTickApi.Task __init__ method, line 305)
- Recurrent events are not supported (have not been tested, thus might result in unexpected behaviour)

## Packages

- ticktick-py (https://github.com/lazeroffmichael/ticktick-py)
- Google calendar for python (https://developers.google.com/tasks/quickstart/python)

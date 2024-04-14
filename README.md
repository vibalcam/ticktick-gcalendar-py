# TickTick-GoogleCalendar-sync

This script provides 2-way sync between TickTick and Google Calendar.

To provide "continuous" 2-way sync, it can be programmed to run every few minutes using crontab or any other program that allows running Python scripts.

## Installation

1. Create conda environment
```bash
conda create -n tick python=3.9.5
conda activate tick
```

2. Clone the repository
```bash
git clone https://github.com/vibalcam/ticktick-gcalendar-py.git
```

3. Install the required packages
```bash
pip install -r requirements.txt
```

4. Install ticktick_py (i.e., clone and install requirements)
```bash
git clone https://github.com/vibalcam/ticktick_py.git
pip install -r ticktick_py/requirements.txt
```

5. Meet requirements (see below)

## Requirements

Meet the following requirements:
- ticktick-py: https://github.com/vibalcam/ticktick_py
- google calendar python: https://developers.google.com/tasks/quickstart/python
- Set up info in account_info.py (you can use account_info_example.py as template and info from -p option to get TickTick calendar ids)

## Usage

1. Check TickTick lists' ids
```bash
python ticktick-gcalendar.py -p
```
2. Set up account_info.py
3. Renew tokens
```bash
python ticktick-gcalendar.py -r
```
4. Sync Google Calendar and TickTick
```bash
python ticktick-gcalendar.py
```

After syncing, the program uses a few files to save the current state of synchronization. 
If these files are removed, the script will perform a full synchronization the next time it is run.

### Reset Synchronization

To reset the synchronization, first remove all the synchronized events in Google Calendar.
This can be done by running
```bash
python ticktick-gcalendar.py --delete_all_gcal
```

### Fix Errors

It may happen that the script is not able to synchronize an event.
To force synchronization of a specific event, we first need to remove it from memory and then sync again.
The event ids can be obtained by looking at the error message after synchronizing.
```bash
# to remove a google calendar event (-rg)
python ticktick-gcalendar.py --remove_gcal 'gcal_event_id'
# to remove a google calendar event (-rt)
python ticktick-gcalendar.py --remove_tick 'tick_event_id'
# sync to force synchronize the removed events
python ticktick-gcalendar.py
```

## Features

It uses the package ticktick-py and Google Calendar for python to sync between Ticktick and Google Calendar.

It is set up so the sync occurs in the following way:
- It syncs the changes in the selected lists of Ticktick to a specific calendar in Google Calendar
- It syncs the selected calendars in Google Calendar to a specific calendar in Ticktick

## Warnings

- Tested on python 3.9.5
- Inbox is excluded by default (to change this look at ticktick-gcalendar.py in TickTickApi.Task __init__ method, line 305)
- You might need to run the renew option, which regenerates the Google API token, every few weeks due to Google Calendar not accepting the old API token
- Recurrent events:
  - Google recurrent events have not been tested (thus might result in unexpected behaviour)
  - For TickTick recurrent events, only the next event is added to Google Calendar

## Packages

- ticktick-py (https://github.com/lazeroffmichael/ticktick-py)
- Google calendar for python (https://developers.google.com/tasks/quickstart/python)

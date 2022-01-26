#!/usr/bin/env python

import os
from abc import abstractmethod, ABC
from datetime import datetime, date, timedelta
from os import path
from typing import Dict, List, Union, Tuple, Optional

import pytz
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from account_info import GOOGLE, GOOGLE_INFO, TICKTICK, TICKTICK_INFO  # account information
from helper import load_dict_from_file, save_dict_to_file, BiDict
from ticktick.api import TickTickClient  # Main Interface
from ticktick.oauth2 import OAuth2  # OAuth2 Manager

DEBUG = False


def do_on_exception(e: Exception):
    if DEBUG:
        raise e
    else:
        print("ErrorUnexpected:")
        print(e)


def gcalendar_get_datetime(event_time: Dict) -> Tuple[datetime, bool]:
    if 'dateTime' in event_time:
        return datetime.fromisoformat(event_time['dateTime']), False
    elif 'date' in event_time:
        return datetime.strptime(event_time['date'], '%Y-%m-%d').replace(tzinfo=pytz.UTC), True
    else:
        raise Exception('event date does not contain date nor dateTime')


def date_to_gcalendar(d: Union[date, datetime]):
    if d.__class__ == date:
        return d.isoformat()
    else:
        return d.strftime('%Y-%m-%dT%H:%M:%SZ')


def ticktick_get_datetime(event_time: Dict, start: bool) -> Tuple[datetime, bool]:
    key = 'startDate' if start else 'dueDate'
    if 'startDate' in event_time:
        return pytz.timezone(event_time['timeZone']).localize(datetime.fromisoformat(event_time[key][:-5])), \
               event_time.get('isAllDay', False)
    else:
        raise Exception(f"event date does not contain {key}")


def get_timezone_name(d: datetime):
    return {tz.zone for tz in map(pytz.timezone, pytz.all_timezones_set) if
            d.astimezone(tz).utcoffset() == d.utcoffset()}.pop()


class Api(ABC):
    class Task(dict):
        def __init__(self, task: Dict, properties: List[str] = None):
            super().__init__(task)
            self.properties = properties
            self._simplified = None

        def __setitem__(self, key, value):
            super().__setitem__(key, value)
            self._simplified = None

        @property
        def simplified(self) -> dict:
            if self._simplified is None:
                self._simplified = {k: self.get(k, None) for k in self.properties}
            return self._simplified

        @property
        @abstractmethod
        def title(self) -> str:
            return ""

        @abstractmethod
        def __hash__(self):
            pass

        def __eq__(self, other):
            if not isinstance(other, self.__class__):
                return False
            return self.simplified == other.simplified if self.get_update_compare() else hash(self) == hash(other)

        @staticmethod
        @abstractmethod
        def set_update_compare(compare: bool):
            pass

        @staticmethod
        @abstractmethod
        def get_update_compare() -> bool:
            pass

    def __init__(self):
        self.old_tasks = None
        pass

    @abstractmethod
    def get_client(self):
        pass

    @abstractmethod
    def get_tasks(self) -> Dict[str, Task]:
        """ Get task and get old task must return the same type"""
        pass

    def get_old_tasks(self, file_name: str = None) -> Dict[str, Task]:
        """ Get task and get old task must return the same type"""
        if self.old_tasks is None:
            self.old_tasks = load_dict_from_file(file_name)
        if self.old_tasks is None:
            self.old_tasks = {}
        return self.old_tasks

    def change_tasks(self, task: Optional[Task], delete: bool = False, delete_id: str = None):
        if delete:
            task_id = task['id'] if delete_id is None else delete_id
            self.get_tasks().pop(task_id, None)
            self.get_old_tasks().pop(task_id, None)
        else:
            self.get_tasks()[task['id']] = task
            self.get_old_tasks()[task['id']] = task

    def save_old_tasks(self, file_name: str):
        save_dict_to_file(file_name, self.get_old_tasks())


class GCalendarApi(Api):
    PROPERTIES = [
        "id",
        "summary",
        "description",
        "start",
        "end",
    ]

    class Task(Api.Task):
        UPDATE_COMPARE = True

        @staticmethod
        def set_update_compare(compare: bool):
            GCalendarApi.Task.UPDATE_COMPARE = compare

        @staticmethod
        def get_update_compare() -> bool:
            return GCalendarApi.Task.UPDATE_COMPARE

        def __init__(self, task: Dict, properties: List[str] = None):
            if properties is None:
                properties = GCalendarApi.PROPERTIES
            super().__init__(task, properties)

        @property
        def title(self) -> str:
            return self.get('summary', "")

        def __hash__(self):
            return hash(self['id'])

    def __init__(self, renew: bool = False, credentials=GOOGLE, info: Dict = GOOGLE_INFO):
        super(GCalendarApi, self).__init__()
        self.calendar_ids = info['calendar_ids']
        self.default_calendar_id = info['default_project_id']
        self.old_filename = info['old_filename']
        creds = None
        if path.exists(credentials['TOKEN_FILENAME']):
            creds = Credentials.from_authorized_user_file(credentials['TOKEN_FILENAME'], credentials['SCOPES'])
            # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if renew:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials['credentials'], credentials['SCOPES'])
                creds = flow.run_local_server(port=0)
            elif creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                raise Exception("Renewal for google needed: add with renew true")
            # Save the credentials for the next run
            with open(credentials['TOKEN_FILENAME'], 'w') as token:
                token.write(creds.to_json())

        self.service = build('calendar', 'v3', credentials=creds)

        self.events = {}
        for calendarId in self.calendar_ids:
            events_result = self.service.events().list(calendarId=calendarId, singleEvents=False).execute()
            self.events.update({k['id']: self.Task(k) for k in events_result.get('items', [])})

    def get_client(self):
        return self.service.events()

    def get_tasks(self) -> Dict[str, Task]:
        return self.events

    def get_old_tasks(self, file_name: str = None) -> Dict[str, Task]:
        if file_name is None:
            file_name = self.old_filename
        return super().get_old_tasks(file_name)

    def save_old_tasks(self, file_name: str = None):
        if file_name is None:
            file_name = self.old_filename
        super().save_old_tasks(file_name)

    def build_event(self, summary: str, start: Union[date, datetime], end: Union[date, datetime],
                    description: str = "", event=None):
        """
        start and end use date for allday and datetime otherwise
        :return type same asn event type
        """
        if event is None:
            event = {}
        # summary, description, end.date, end.dateTime, end.timeZone, recurrence
        event['summary'] = summary
        event['description'] = description
        event['start'] = {}
        event['end'] = {}
        if start.__class__ == date:
            event['start']['date'] = date_to_gcalendar(start)
            event['end']['date'] = date_to_gcalendar(end)
        else:
            event['start']['dateTime'] = date_to_gcalendar(start)
            event['start']['timeZone'] = get_timezone_name(start)
            event['end']['dateTime'] = date_to_gcalendar(end)
            event['end']['timeZone'] = get_timezone_name(end)
        return event

    def update(self, task: Dict, calendar_id: str = None):
        if calendar_id is None:
            calendar_id = self.default_calendar_id
        task = self.get_client().update(calendarId=calendar_id, eventId=task['id'], body=task).execute()
        self.change_tasks(task if isinstance(task, GCalendarApi.Task) else GCalendarApi.Task(task))

    def insert(self, event: Dict, calendar_id: str = None) -> Task:
        if calendar_id is None:
            calendar_id = self.default_calendar_id
        added = self.Task(self.get_client().insert(calendarId=calendar_id, body=event).execute())
        self.change_tasks(added)
        return added

    def delete(self, event_id: str, calendar_id: str = None):
        """If event is given, then the event_id is taken from there"""
        if  calendar_id is None:
            calendar_id = self.default_calendar_id
        self.get_client().delete(calendarId=calendar_id, eventId=event_id).execute()
        self.change_tasks(None, delete=True, delete_id=event_id)


class TickTickApi(Api):
    PROPERTIES = [
        "id",
        "title",
        "isAllDay",
        "content",
        "desc",
        "dueDate",  # Task due date time in "yyyy-MM-dd'T'HH:mm:ssZ" Example : "2019-11-13T03:00:00+0000"
        "repeat",  # Recurring rules of task Example : "RRULE:FREQ=DAILY;INTERVAL=1"
        "startDate",  # Start date time in "yyyy-MM-dd'T'HH:mm:ssZ" Example : "2019-11-13T03:00:00+0000"
        "status",  # Task completion status Value : Normal: 0, Completed: 1
        "timeZone",
    ]

    class Task(Api.Task):
        UPDATE_COMPARE = True

        @staticmethod
        def set_update_compare(compare: bool):
            TickTickApi.Task.UPDATE_COMPARE = compare

        @staticmethod
        def get_update_compare() -> bool:
            return TickTickApi.Task.UPDATE_COMPARE

        def __init__(self, task: Dict, properties: List[str] = None):
            if properties is None:
                properties = TickTickApi.PROPERTIES
            super().__init__(task, properties)

        @property
        def title(self) -> str:
            return self.get('title', "")

        def __hash__(self):
            return hash(self['id'])

    def __init__(self, renew: bool = False, credentials=TICKTICK, info=TICKTICK_INFO):
        super(TickTickApi, self).__init__()
        if not (renew or path.isfile(credentials['TOKEN_FILENAME'])):
            raise Exception("Renew for ticktick needed: run with renew true")

        auth_client = OAuth2(client_id=credentials['CLIENT_ID'],
                             client_secret=credentials['CLIENT_SECRET'],
                             redirect_uri=credentials['REDIRECT_URI'])
        self.client = TickTickClient(credentials['USERNAME'], credentials['PWD'], auth_client)
        self.old_filename = info['old_filename']
        self.default_project_id = info['default_project_id']
        #  change this to include all tasks and exclude tasks from projects if want to include inbox
        self.tasks = {}
        for project in self.client.state['projects']:
            if project['id'] not in info['EXCLUDED_PROJECTS']:
                self.tasks.update({k['id']: self.Task(k) for k in self.client.task.get_from_project(project['id'])})
        # for project in self.client.state['projects']:
        #     if project['id'] not in info['EXCLUDED_PROJECTS']:
        #         tasks.extend(self.client.task.get_from_project(project['id']))
        # self.tasks = {k['id']: self.Task(k) for k in tasks}

    def get_client(self):
        return self.client

    def get_tasks(self) -> Dict[str, Task]:
        return self.tasks

    def get_old_tasks(self, file_name: str = None) -> Dict[str, Task]:
        if file_name is None:
            file_name = self.old_filename
        return super().get_old_tasks(file_name)

    def save_old_tasks(self, file_name: str = None):
        if file_name is None:
            file_name = self.old_filename
        super().save_old_tasks(file_name)

    def build_task(self, title: str, content: str, start: datetime, end: datetime, all_day: bool, time_zone: str,
                   task=None, project_id: str = None):
        if task is None:
            if project_id is None:
                project_id = self.default_project_id

            task = self.get_client().task.builder(
                title=title,
                content=content,
                projectId=project_id,
                allDay=all_day,
                startDate=start,
                dueDate=end,
                timeZone=time_zone
            )
        else:
            task['title'] = title
            task['isAllDay'] = all_day
            task['content'] = content
            task['dueDate'] = end
            task['startDate'] = start
            task['timeZone'] = time_zone
        return task

    def update(self, task: Task):
        self.get_client().task.update(task)
        task = self.get_client().get_by_id(task['id'], search='tasks')
        self.change_tasks(TickTickApi.Task(task))

    def insert(self, task: Task) -> Task:
        task_id = self.get_client().task.create(task)['id']
        added = TickTickApi.Task(self.get_client().get_by_id(task_id, search='tasks'))
        self.change_tasks(added)
        return added

    def delete(self, task: Task):
        self.get_client().task.delete(task)
        self.change_tasks(task, delete=True)

    def complete(self, task: Task):
        self.get_client().task.complete(task)
        self.change_tasks(task, delete=True)


class Diff(ABC):
    def __init__(self, api: Api):
        old = set(api.get_old_tasks().values())
        tasks = set(api.get_tasks().values())
        api.__class__.Task.set_update_compare(False)
        self.added = tasks - old
        self.deleted = old - tasks
        api.__class__.Task.set_update_compare(True)
        self.updated = tasks - old - self.added


class TickTickDiff(Diff):
    def __init__(self, api: TickTickApi):
        super().__init__(api)
        self.api = api

    def sync_gcalendar(self, gcalendar_api: GCalendarApi, bidict_tick_gcalendar: BiDict[str, str]):
        gcal_tasks = gcalendar_api.get_tasks()
        # Update
        while self.updated:
            task = self.updated.pop()
            print(f"Update {self.__class__}: {task.title}")
            try:
                id_gcal = bidict_tick_gcalendar.get(task['id'], None)
                if id_gcal is None:
                    self.added.add(task)
                    continue
                task_gcal = gcal_tasks[id_gcal]
                if 'startDate' not in task or 'dueDate' not in task:
                    gcalendar_api.delete(id_gcal)
                    self.api.change_tasks(task)
                    del bidict_tick_gcalendar[task['id']]
                    continue
                start, all_day = ticktick_get_datetime(task, True)
                end, all_day = ticktick_get_datetime(task, False)
                if all_day:     # fix for time in ticktick
                    start += timedelta(days=1)
                    end += timedelta(days=1)

                task_gcal = gcalendar_api.build_event(
                    summary=task['title'],
                    start=start.date() if all_day else start,
                    end=end.date() if all_day else end,
                    description=task.get('content', None),
                    event=task_gcal
                )
                gcalendar_api.update(task_gcal)
                self.api.change_tasks(task)
            except Exception as e:
                self.api.get_tasks().pop(task['id'], None)
                do_on_exception(e)

        # Insert
        while self.added:
            task = self.added.pop()
            print(f"Add {self.__class__}: {task.title}")
            try:
                if 'startDate' not in task or 'dueDate' not in task:
                    self.api.change_tasks(task)
                    continue
                start, all_day = ticktick_get_datetime(task, True)
                end, all_day = ticktick_get_datetime(task, False)
                if all_day:     # fix for time in ticktick
                    start += timedelta(days=1)
                    end += timedelta(days=1)

                added_id = gcalendar_api.insert(gcalendar_api.build_event(
                    summary=task['title'],
                    start=start.date() if all_day else start,
                    end=end.date() if all_day else end,
                    description=task.get('content', None)
                ))['id']
                self.api.change_tasks(task)
                bidict_tick_gcalendar[task['id']] = added_id
            except Exception as e:
                self.api.get_tasks().pop(task['id'], None)
                do_on_exception(e)

        # Delete
        while self.deleted:
            task = self.deleted.pop()
            print(f"Delete {self.__class__}: {task.title}")
            try:
                if 'startDate' not in task or 'dueDate' not in task:
                    self.api.change_tasks(task, delete=True)
                    continue
                gcal_id = bidict_tick_gcalendar[task['id']]

                gcalendar_api.delete(gcal_id)
                self.api.change_tasks(task, delete=True)
                del bidict_tick_gcalendar[task['id']]
            except Exception as e:
                self.api.get_tasks().pop(task['id'], None)
                do_on_exception(e)


class GCalendarDiff(Diff):
    def __init__(self, api: GCalendarApi):
        super().__init__(api)
        self.api = api

    def sync_ticktick(self, ticktick_api: TickTickApi, bidict_tick_gcalendar: BiDict[str, str]):
        now = datetime.utcnow().replace(tzinfo=pytz.UTC)
        tick = ticktick_api.get_client().task
        tick_tasks = ticktick_api.get_tasks()

        # Updated
        while self.updated:
            task = self.updated.pop()
            print(f"Update {self.__class__}: {task.title}")
            try:
                id_tick = bidict_tick_gcalendar.inverse.get(task['id'], None)
                if id_tick is None:
                    self.added.add(task)
                    continue
                task_tick = tick_tasks[id_tick[0]]
                start, all_day = gcalendar_get_datetime(task['start'])
                end, _ = gcalendar_get_datetime(task['end'])
                time_zone = get_timezone_name(start)
                tick_date = tick.dates(start=start, due=end, tz=time_zone)
                if all_day:     # fix for time in ticktick
                    end -= timedelta(days=1)
                if start < now:  # if after, then delete
                    tick.delete(task_tick)
                    self.api.change_tasks(task)
                    del bidict_tick_gcalendar[task_tick['id']]
                    continue
                task_tick = ticktick_api.build_task(
                    title=task.get('summary', ""),
                    all_day=all_day,
                    content=task.get('description', ""),
                    end=tick_date['dueDate'],
                    start=tick_date['startDate'],
                    time_zone=time_zone,
                    task=task_tick
                )

                ticktick_api.update(task_tick)
                self.api.change_tasks(task)
            except Exception as e:
                self.api.get_tasks().pop(task['id'], None)
                do_on_exception(e)

        # Insert
        while self.added:
            task = self.added.pop()
            print(f"Add {self.__class__}: {task.title}")
            try:
                start, all_day = gcalendar_get_datetime(task['start'])
                end, _ = gcalendar_get_datetime(task['end'])
                time_zone = get_timezone_name(start)
                if all_day:     # fix for time in ticktick
                    end -= timedelta(days=1)
                if start < now:
                    self.api.change_tasks(task)
                    continue

                added_id = ticktick_api.insert(ticktick_api.build_task(
                    title=task.get('summary', ""),
                    content=task.get('description', ""),
                    all_day=all_day,
                    start=start,
                    end=end,
                    time_zone=time_zone
                ))['id']
                self.api.change_tasks(task)
                bidict_tick_gcalendar[added_id] = task['id']
            except Exception as e:
                self.api.get_tasks().pop(task['id'], None)
                do_on_exception(e)

        # Delete
        while self.deleted:
            task = self.deleted.pop()
            print(f"Delete {self.__class__}: {task.title}")
            try:
                task_tick_id = bidict_tick_gcalendar.get_inverse(task['id'])[0]

                task_tick = tick_tasks[task_tick_id]
                ticktick_api.complete(task_tick)
                self.api.change_tasks(task, delete=True)
                del bidict_tick_gcalendar[task_tick_id]
            except Exception as e:
                self.api.get_tasks().pop(task['id'], None)
                do_on_exception(e)


def main(args):
    if not path.exists("data"):
        os.makedirs("data")

    tick = TickTickApi(renew=args.renew)
    gtasks = GCalendarApi(renew=args.renew)
    if args.renew:
        return
    bidict_path = 'data/bidict_ticktick_gcalendar.dict'

    if args.tick_print:
        print(tick.get_client().state['projects'])
        return

    if path.isfile(bidict_path):
            bidict_ticktick_gcalendar = BiDict.load(bidict_path)
    else:
        bidict_ticktick_gcalendar = BiDict()

    if args.remove_tick is not None:
        del tick.get_old_tasks()[args.remove_tick]
        gcal_id = bidict_ticktick_gcalendar.pop(args.remove_tick, None)
        if gcal_id is not None:
            del gtasks.get_old_tasks()[gcal_id]
        print(f"Deleted id {args.remove_tick}")
        bidict_ticktick_gcalendar.save(bidict_path)
        gtasks.save_old_tasks()
        tick.save_old_tasks()
        return
    elif args.remove_gcal is not None:
        del gtasks.get_old_tasks()[args.remove_gcal]
        tick_id = bidict_ticktick_gcalendar.inverse.get(args.remove_gcal, None)
        if tick_id is not None:
            del bidict_ticktick_gcalendar[tick_id]
            del tick.get_old_tasks()[tick_id]
        print(f"Deleted id {args.remove_gcal}")
        bidict_ticktick_gcalendar.save(bidict_path)
        gtasks.save_old_tasks()
        tick.save_old_tasks()
        return
    elif args.delete_all_gcal:
        for event_id in list(gtasks.get_tasks().keys()):
            gtasks.delete(event_id)
        print("You can now delete the data folder")
        return

    try:
        GCalendarDiff(gtasks).sync_ticktick(tick, bidict_ticktick_gcalendar)
        TickTickDiff(tick).sync_gcalendar(gtasks, bidict_ticktick_gcalendar)
    except Exception as e:
        raise e
    finally:
        bidict_ticktick_gcalendar.save(bidict_path)
        gtasks.save_old_tasks()
        tick.save_old_tasks()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('-r', '--renew', action='store_true')
    parser.add_argument('-p', '--tick_print', action='store_true')
    parser.add_argument('-rt', '--remove_tick', type=str, default=None)
    parser.add_argument('-rg', '--remove_gcal', type=str, default=None)
    parser.add_argument('-dg', '--delete_all_gcal', action='store_true')    # use to restore

    arguments = parser.parse_args()
    main(arguments)

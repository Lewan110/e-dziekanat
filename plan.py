# -*- coding: utf-8 -*-
import requests
import codecs
from bs4 import BeautifulSoup as bs
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from time import sleep
import json
import datetime
from sys import exit

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
URL = "https://s1.wcy.wat.edu.pl/ed/"

class eDziekanat:
    def __init__(self, login, passwd, output):
        self.timetable = {}
        self.output_dir = output
        # parametry formularza logowania
        self.params = {
            "default_fun": 1,
            "formname": "login",
            "userid": login,
            "password": passwd
            }
        # utworzenie sesji
        self.session = requests.session()
    def login(self):
        """Funkcja najpierw getem pobiera id sesji, a po tym wysyła posta z danymi logowania"""
        response = self.session.get(URL, verify=False)
        response.encoding = "utf-8"
        soup = bs(response.text, 'html.parser')
        self.login_form = soup.find("form")
        self.ssid = self.login_form.attrs['action'].replace('index.php?sid=', '')

        # czasami e-dziekanat jest przeciążony lub nie działa
        # w takim wypadku strona nie generuje nam id sesji
        if not self.ssid:
            print("Nie udało się uzyskać ssid.\nKończenie programu")
            exit()

        print("SSID: %s" % self.ssid)
        self.session.post(
            "%s%s" % (URL, self.login_form.attrs['action']),
            data = self.params,
            verify = False
        )
    def get_timetable(self, group):
        """Pobranie planu zajęć grupy"""
        t = URL + "logged.php?sid=%s&mid=328&iid=20162&vrf=32820162&rdo=1&pos=0&exv=%s&opr=DTXT" % (self.ssid, group)
        timetable_req = self.session.get(t, verify=False)
        # próby pobrania zawartości pliku
        # e-dziekanat był robiony dawno temu i nie wszystko działa jak powinno :D
        for i in range(10):
            print("Pobieranie planu grupy %s, próba %d" % (group, i+1), end='')
            sleep(5)
            try:
                timetable_req = self.session.get(t, verify=False)
            except ConnectionError as e:
                print(e)
                exit()
            if len(timetable_req.content):
                print("\t\t[OK]")
                break
            else:
                print("\t\t[FAIL]")
        self.parse(timetable_req.content.decode("iso-8859-2").split("\r\n"))
    def parse(self, lessons):
        # zamiany godziny rozpoczęcia zajęć na numer bloku
        print("Przetwarzanie pliku... ", end='')
        hours = {
            "08:00": "0",
			"09:50": "1",
			"11:40": "2",
			"13:30": "3",
			"15:45": "4",
			"17:35": "5",
			"19:25": "6"
        }
        for lesson in lessons[1:]:
            if not lesson:
                continue
            l = lesson.split(",")
            l[3] = hours[l[3]]
            # index końca nazwy przedmiotu
            index_of_lesson_type = l[0].index(" (")
            # zapisanie typu zajęć(w/ć/L) do zmiennej
            l_type = l[0][index_of_lesson_type+2:index_of_lesson_type+3]

            l[0] = l[0][:index_of_lesson_type]
            # dodanie typu zajęć do listy
            l.insert(1, l_type)
            if not l[3] in self.timetable:
                #jeżeli slownik nie posiada klucza dla danego dnia to go tworzymy
                self.timetable[l[3]] = [[] for i in range(7)]
            # wpisanie bloku zajęć w odpowiednie miejsce na liście
            self.timetable[l[3]][int(l[4])] = [l[0], l[1], l[2]]
        print("\t\t\t\t[OK]")


if __name__ == "__main__":
    with open("dane.txt", "r") as f:
        username = f.readline().replace("\n","").replace("\r","").split("=")[1]
        password = f.readline().replace("\n","").replace("\r","").split("=")[1]
        output = f.readline().replace("\n","").replace("\r","").split("=")[1]
        groups = f.readline().replace("\n","").replace("\r","").split("=")[1]
        groups = groups.split(",")
    ed = eDziekanat(username, password, output)
    ed.login()
    ed.get_timetable("I6Y4S1")

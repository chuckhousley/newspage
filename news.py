#!/usr/bin/python3
import curses
import random
import concurrent.futures
from json import loads
from urllib.request import urlopen
from urllib.parse import urlencode

class Line():
    def __init__(self, index, window, title, description):
        self.index = index
        self.window = window
        y, x = self.window.getmaxyx()
        self.title = str(self.index) + ") " + title[:x-3]
        if description:
            self.title += ": "
            remainder = max(0, x - len(self.title) - 3)
            self.description = description[:remainder]
        else:
            self.description = ""
        self.speed = random.randint(2, 10)
        self.timer = 0
        self.position = 0
        self.d_flag = False
        self.finish = False

    def animate(self):
        if self.finish:
            return None
        if self.timer == self.speed:
            self.timer = 0
            self.printnextchar()
        else:
            self.timer += 1


    def printnextchar(self):
        if self.d_flag:
            if self.position == len(self.description):
                self.finish = True
                return None

            try:
                self.window.addstr(self.description[self.position], curses.A_DIM)
            except:
                print(str(self.position))
            self.position += 1
        else:
            self.window.addstr(self.title[self.position])
            self.position += 1
            if self.position == len(self.title):
                self.position = 0
                self.d_flag = True
        self.window.noutrefresh()
        

def get_json(url):
    res = urlopen(url).read().decode('utf-8')
    data = loads(res)
    return [] if data['status'] != 'ok' else data


def make_urls():
    #return ['http://localhost:3000/hn', 'http://localhost:3000/ap']
    try:
        with open("./newsapi", 'r') as f:
            apikey = f.readline()
            apikey = apikey[:-1] if apikey[-1] == '\n' else apikey
    except FileNotFoundError as e:
        print("Make a file with your api key: {0}".format(e))
        teardown()

    f = lambda x: "https://newsapi.org/v1/articles?" + x
    args = []
    for source in ['associated-press', 'hacker-news', 'the-new-york-times']:
        args.append(urlencode({'source': source, 'apikey': apikey}))
    return [r for r in map(f, args)]


def setup():
    stdscr = curses.initscr()
    curses.cbreak() # raw() disables tty control
    curses.noecho()
    curses.curs_set(0)
    if curses.has_colors():
        curses.start_color()
        curses.init_color(0, 0, 0, 0)
    return stdscr

def teardown():
    curses.curs_set(1)
    curses.echo()
    curses.nocbreak()
    curses.endwin()


def main():
    stdscr = setup()
    rows, cols = stdscr.getmaxyx()
    inputhandler = curses.newwin(1, 1, rows, 0)
    lines = []
    line_counter = 0

    urls = make_urls()
    data_list = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_data = {executor.submit(get_json, url): url for url in urls}
        for f in concurrent.futures.as_completed(future_data):
            data_list.append(future_data[f])
            res = f.result()
            if res['status'] == 'ok':
                data_list.append(f.result())
            else:
                data_list.append([])

    for data in data_list:
        if type(data) is str:
            lwindow = curses.newwin(1, cols, line_counter, 0)
            name = sorted(data.split('='), key=len)[0]
            name = name[:-7] if name[-7:] == '&apikey' else name
            lines.append(Line(0, lwindow, name, None))
            line_counter += 1
            continue
        
        ar = data['articles']
        for i in range(len(ar)):
            lwindow = curses.newwin(1, cols, line_counter, 0)
            ltitle = ar[i]['title']
            ldesc = ar[i]['description']
            lines.append(Line(i+1, lwindow, ltitle, ldesc))
            line_counter += 1

    for i in range(cols * 15):
        for line in lines:
            line.animate()
        curses.doupdate()
        curses.napms(1)
    
    curses.flushinp() # just in case a button was pressed
    inputhandler.getch()

    teardown()


if __name__ == "__main__":
    main()

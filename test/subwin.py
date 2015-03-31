#!/usr/bin/env python

import curses
import time

def main(stdscr):
	stdscr.clear()
	curses.curs_set(0)
	stdscr.refresh()

	win = curses.newwin(15, 40, 5, 5)
	subwin = win.derwin(5, 5, 1, 1)
	subwin.box()
	subwin.addch(1,1,"#")
	subwin.refresh()
	win.box()
	win.refresh()

	while 1:
		c = stdscr.getch()
		if c == ord('q'):
			sys.exit(0)
		elif c == ord('e'):
			win.erase()
			win.refresh()
			time.sleep(2)
			subwin.box()
			subwin.addch(1,1,"#")
			subwin.refresh()

if __name__=='__main__':
    curses.wrapper(main)

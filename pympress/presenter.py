#!/usr/bin/env python
#
#       presenter.py
#
#       Copyright 2009 Thomas Jost <thomas.jost@gmail.com>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

import gobject, gtk
import time

class Presenter:
	def __init__(self, current, next, number, total, event_callback):
		black = gtk.gdk.Color(0, 0, 0)

		self.start_time = 0
		self.delta = 0
		self.paused = False

		self.number_total = total

		# Window
		win = gtk.Window(gtk.WINDOW_TOPLEVEL)
		win.set_title("pympress presenter")
		win.set_default_size(800, 600)
		win.set_position(gtk.WIN_POS_CENTER)
		win.connect("delete-event", gtk.main_quit)

		# A little space around everything in the window
		align = gtk.Alignment(0.5, 0.5, 1, 1)
		align.set_padding(20, 20, 20, 20)
		win.add(align)

		# Table
		table = gtk.Table(2, 10, False)
		table.set_col_spacings(25)
		table.set_row_spacings(25)
		align.add(table)

		# "Current slide" frame
		frame = gtk.Frame("Current slide")
		table.attach(frame, 0, 6, 0, 1)
		align = gtk.Alignment(0.5, 0.5, 1, 1)
		align.set_padding(0, 0, 12, 0)
		frame.add(align)
		vbox = gtk.VBox()
		align.add(vbox)
		self.frame_current = gtk.AspectFrame(yalign=1, ratio=4./3., obey_child=False)
		vbox.pack_start(self.frame_current)
		self.label_current = gtk.Label()
		self.label_current.set_justify(gtk.JUSTIFY_CENTER)
		self.label_current.set_use_markup(True)
		vbox.pack_start(self.label_current, False, False, 10)
		self.da_current = gtk.DrawingArea()
		self.da_current.modify_bg(gtk.STATE_NORMAL, black)
		self.da_current.connect("expose-event", self.on_expose)
		self.frame_current.add(self.da_current)

		# "Next slide" frame
		frame = gtk.Frame("Next slide")
		table.attach(frame, 6, 10, 0, 1)
		align = gtk.Alignment(0.5, 0.5, 1, 1)
		align.set_padding(0, 0, 12, 0)
		frame.add(align)
		vbox = gtk.VBox()
		align.add(vbox)
		self.frame_next = gtk.AspectFrame(yalign=1, ratio=4./3., obey_child=False)
		vbox.pack_start(self.frame_next)
		self.label_next = gtk.Label()
		self.label_next.set_justify(gtk.JUSTIFY_CENTER)
		self.label_next.set_use_markup(True)
		vbox.pack_start(self.label_next, False, False, 10)
		self.da_next = gtk.DrawingArea()
		self.da_next.modify_bg(gtk.STATE_NORMAL, black)
		self.da_next.connect("expose-event", self.on_expose)
		self.frame_next.add(self.da_next)

		# "Time elapsed" frame
		frame = gtk.Frame("Time elapsed")
		table.attach(frame, 0, 5, 1, 2, yoptions=gtk.FILL)
		align = gtk.Alignment(0.5, 0.5, 1, 1)
		align.set_padding(10, 10, 12, 0)
		frame.add(align)
		self.label_time = gtk.Label()
		self.label_time.set_justify(gtk.JUSTIFY_CENTER)
		self.label_time.set_use_markup(True)
		align.add(self.label_time)

		# "Clock" frame
		frame = gtk.Frame("Clock")
		table.attach(frame, 5, 10, 1, 2, yoptions=gtk.FILL)
		align = gtk.Alignment(0.5, 0.5, 1, 1)
		align.set_padding(10, 10, 12, 0)
		frame.add(align)
		self.label_clock = gtk.Label()
		self.label_clock.set_justify(gtk.JUSTIFY_CENTER)
		self.label_clock.set_use_markup(True)
		align.add(self.label_clock)

		# Add events
		win.add_events(gtk.gdk.KEY_PRESS_MASK | gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.SCROLL_MASK)
		win.connect("key-press-event", event_callback)
		win.connect("button-press-event", event_callback)
		win.connect("scroll-event", event_callback)

		# Set page
		self.set_page(current, next, number, False)

		# Setup timer
		gobject.timeout_add(1000, self.update_time)

		win.show_all()

	def on_expose(self, widget, event):
		cr = widget.window.cairo_create()
		cr.set_source_rgb(1, 1, 1)

		# Widget size
		ww, wh = widget.window.get_size()

		# Page-specific stuff (dirty)
		page = self.page_current
		pw, ph = self.pw_cur, self.ph_cur
		if widget == self.da_next:
			page = self.page_next
			pw, ph = self.pw_next, self.ph_next

		# Scale
		scale = min(ww/pw, wh/ph)
		cr.scale(scale, scale)

		cr.rectangle(0, 0, pw, ph)
		cr.fill()

		if page is not None:
			page.render(cr)

	def set_page(self, current, next, number, start = True):
		self.page_current = current
		self.page_next = next
		self.number_current = number

		# Page sizes
		self.pw_cur, self.ph_cur = self.page_current.get_size()

		# Aspect ratios
		pr = self.pw_cur / self.ph_cur
		self.frame_current.set_property("ratio", pr)

		# Same thing for next page if it's set
		if self.page_next is not None:
			self.pw_next, self.ph_next = self.page_next.get_size()
			pr = self.pw_next / self.ph_next
			self.frame_next.set_property("ratio", pr)

		# Start counter if needed
		if start and self.start_time == 0:
			self.start_time = time.time()

		# Update display
		self.update_numbers()

		self.da_current.queue_draw()
		self.da_next.queue_draw()

	def update_numbers(self):
		text = "<span font='36'>%s</span>"

		cur = "%d/%d" % (self.number_current+1, self.number_total)
		next = "--"
		if self.number_current+2 <= self.number_total:
			next = "%d/%d" % (self.number_current+2, self.number_total)

		self.label_current.set_markup(text % cur)
		self.label_next.set_markup(text % next)

	def update_time(self):
		text = "<span font='36'>%s</span>"

		# Current time
		clock = time.strftime("%H:%M:%S")

		# Time elapsed since the beginning of the presentation
		if not self.paused:
			self.delta = time.time() - self.start_time
		if self.start_time == 0:
			self.delta = 0
		elapsed = "%02d:%02d" % (int(self.delta/60), int(self.delta%60))
		if self.paused:
			elapsed += " (pause)"

		self.label_time.set_markup(text % elapsed)
		self.label_clock.set_markup(text % clock)

		return True

	def switch_pause(self):
		if self.paused:
			self.start_time = time.time() - self.delta
			self.paused = False
		else:
			self.paused = True

	def reset_counter(self):
		self.start_time = 0
#!/usr/bin/env python

from gi.repository import Gtk, GLib
try:
    from gi.repository import AppIndicator3 as appindicator
except:
    from gi.repository import AppIndicator as appindicator
import subprocess
import re

IWCONFIG_CMD = '/sbin/iwconfig'

def get_wifi_speed(iff):
    p = subprocess.Popen([IWCONFIG_CMD, iff], stdout=subprocess.PIPE)
    for line in p.stdout:
        m = re.search('Bit Rate=([\d\.]+) (\S+)', line)
        if m is not None:
            print ("Speed: " + m.group(0))
            return m.group(1) + " " + m.group(2)
    return None

def get_wifi_interfaces():
    p = subprocess.Popen([IWCONFIG_CMD], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    iffs = []
    for line in p.stdout:
        m = re.search('no wireless extensions', line)
        if m is None:
            m = re.search('^(\S+)\s+\S+', line)
            if m is not None:
                iffs.append(m.group(1))
    print("Iffs: " + str(iffs))
    return iffs

class WifiSpeedIndicator(object):
    ifaces = []
    cur_iface = None
    update_time = 5

    def __init__(self):
        self.indicator = appindicator.Indicator.new('wifi-speed-indicator',
                                                    'radiotray-on',
                                                    appindicator.IndicatorCategory.APPLICATION_STATUS)
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.update()

        Gtk.main()

    def quit_handler(self, *data):
        Gtk.main_quit()

    def set_cur_iface_handler(self, item, iface):
        self.cur_iface = iface

    def set_update_time_handler(self, item, time):
        self.update_time = time

    def update_menu(self):
        self.menu = self.build_menu(self.ifaces, self.cur_iface)
        self.menu.show_all()
        self.indicator.set_menu(self.menu)

    def build_menu(self, ifaces, cur_iface):
        menu = Gtk.Menu()

        if len(ifaces) > 0:
            item = Gtk.MenuItem("Wireless interfaces")
            item.set_sensitive(False)
            menu.append(item)
            first_item = None
            wifi_items = []
            for iff in ifaces:
                if first_item is None:
                    item = Gtk.RadioMenuItem(label = iff)
                    first_item = item
                else:
                    item = Gtk.RadioMenuItem(laber = iff, group = first_item)

                if iff == self.cur_iface:
                    item.set_active(True)
                item.connect('activate', self.set_cur_iface_handler, iff)
                menu.append(item)
                wifi_items.append(item)
        else:
            item = Gtk.MenuItem('No wireless interfaces detected')
            item.set_sensitive(False) # disabled - grayed out
            menu.append(item)

        menu.append(Gtk.SeparatorMenuItem())
        item = Gtk.MenuItem('Update time')
        submenu = Gtk.Menu()
        first_item = None
        for i in [1,2,3,5,7,10,15,30,45,60]:
            time_label = str(i) + ' s'
            if first_item is None:
                item2 = Gtk.RadioMenuItem(label = time_label)
                first_item = item2
            else:
                item2 = Gtk.RadioMenuItem(label = time_label, group = first_item)
            if i == self.update_time:
                item2.set_active(True)

            item2.connect('activate', self.set_update_time_handler, i)
            submenu.append(item2)

        item.set_submenu(submenu)
        menu.append(item)
        menu.append(Gtk.SeparatorMenuItem())
        item = Gtk.MenuItem('Quit')
        item.connect('activate', self.quit_handler)
        menu.append(item)

        menu.show_all()

        return menu

    def update(self):
        GLib.timeout_add_seconds(self.update_time, self.update)

        old_ifaces = self.ifaces
        self.ifaces = get_wifi_interfaces()

        # if interface not selected then select first available
        if self.cur_iface is None and len(self.ifaces) > 0:
            self.cur_iface = self.ifaces[0]

        # self.update_ifaces_menu_items()
        if self.ifaces != old_ifaces:
            self.update_menu();

        iff_speed = get_wifi_speed(self.cur_iface)
        if iff_speed is not None:
            self.indicator.set_label(iff_speed, '')
        else:
            self.indicator.set_label('X', '')

WifiSpeedIndicator()

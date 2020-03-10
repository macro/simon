# MIT License
#
# Copyright (c) 2017 Ray Chen <hcyrnd@gmail.com>

# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import argparse
import math

import psutil

from PyObjCTools import AppHelper
from Foundation import NSTimer, NSRunLoop
from AppKit import NSApplication, NSStatusBar, NSMenu, NSMenuItem, \
    NSEventTrackingRunLoopMode


def bytes2human(n):
    # Credits to /u/cyberspacecowboy on reddit
    # https://www.reddit.com/r/Python/comments/5xukpd/-/dem5k12/
    symbols = (' B', ' KiB', ' MiB', ' GiB', ' TiB', ' PiB', ' EiB', ' ZiB',
               ' YiB')
    i = int(math.floor(math.log(abs(n)+1, 2) / 10))
    return '%.1f%s' % (n/2**(i*10), symbols[i])


class Simon(NSApplication):

    update_interval_secs = 1

    _stats = {
        'disk_data_read': 0,
        'disk_data_written': 0,
        'network_recv': 0,
        'network_sent': 0,
    }

    def finishLaunching(self):
        self._setup_menuBar()

        # Create a timer which fires the update_ method every 1second,
        # and add it to the runloop
        NSRunLoop.currentRunLoop().addTimer_forMode_(
            NSTimer
            .scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                self.update_interval_secs, self, 'update:', '', True
            ),
            NSEventTrackingRunLoopMode
        )

        print('Simon is now running.')
        print('CTRL+C does not work here.')
        print('You can quit through the menubar (Simon -> Quit).')

    def update_(self, timer):

        # System
        cpu_usage = psutil.cpu_percent()
        vm = psutil.virtual_memory()
        ram_usage = vm.percent
        self.CPU_USAGE.setTitle_('  CPU Usage: {}%'.format(cpu_usage))
        self.RAM_USAGE.setTitle_('  Mem Usage: {}%'.format(ram_usage))
        self.RAM_AVAILABLE.setTitle_('  Mem Avail / Used: {} / {}'.format(
            bytes2human(vm.available), bytes2human(vm.used)))

        # Disk I/O
        disk_io = psutil.disk_io_counters()
        disk_data_read = bytes2human(disk_io.read_bytes)
        disk_data_written = bytes2human(disk_io.write_bytes)
        if self._stats['disk_data_read'] == 0:
            disk_data_read_rate = bytes2human(0)
        else:
            disk_data_read_rate = bytes2human(
                (disk_io.read_bytes - self._stats['disk_data_read']) /
                self.update_interval_secs)
        if self._stats['disk_data_written'] == 0:
            disk_data_written_rate = bytes2human(0)
        else:
            disk_data_written_rate = bytes2human(
                (disk_io.write_bytes - self._stats['disk_data_written']) /
                self.update_interval_secs)

        self.DATA_READ.setTitle_('  Read: {} ({}/s)'.format(
            disk_data_read, disk_data_read_rate))
        self.DATA_WRITTEN.setTitle_('  Written: {} ({}/s)'.format(
            disk_data_written, disk_data_written_rate))
        self._stats['disk_data_read'] = disk_io.read_bytes
        self._stats['disk_data_written'] = disk_io.write_bytes

        # Network
        network_io = psutil.net_io_counters()
        network_recv = bytes2human(network_io.bytes_recv)
        network_sent = bytes2human(network_io.bytes_sent)
        if self._stats['network_sent'] == 0:
            network_send_rate = bytes2human(0)
        else:
            network_send_rate = bytes2human(
                (network_io.bytes_sent - self._stats['network_sent']) /
                self.update_interval_secs)
        if self._stats['network_recv'] == 0:
            network_recv_rate = bytes2human(0)
        else:
            network_recv_rate = bytes2human(
                (network_io.bytes_recv - self._stats['network_recv']) /
                self.update_interval_secs)

        self.NETWORK_RECV.setTitle_('  Received: {} ({}/s)'.format(
            network_recv, network_recv_rate))
        self.NETWORK_SENT.setTitle_('  Sent: {} ({}/s)'.format(
            network_sent, network_send_rate))
        self._stats['network_recv'] = network_io.bytes_recv
        self._stats['network_sent'] = network_io.bytes_sent

        # Process
        max_cpu = None
        max_mem = None
        for process_count, p in enumerate(psutil.process_iter(), 1):
            try:
                if max_cpu is None:
                    max_cpu = (p.cpu_percent(), p.name())
                else:
                    max_cpu = max([(p.cpu_percent(), p.name()), max_cpu])
                if max_mem is None:
                    max_mem = (p.memory_percent(), p.name())
                else:
                    max_mem = max([(p.memory_percent(), p.name()), max_mem])
            except (psutil.AccessDenied, psutil.ZombieProcess):
                pass

        self.PROCESS_COUNT.setTitle_('  Processes: {}'.format(process_count))
        self.PROCESS_TOP_CPU.setTitle_('  Top CPU: {} ({:.1f}%)'.format(
            *reversed(max_cpu)))
        self.PROCESS_TOP_MEM.setTitle_('  Top Mem: {} ({:.1f}%)'.format(
            *reversed(max_mem)))

        # Update title
        self.statusItem.setTitle_(u'\u2235 {:04.1f}%'.format(cpu_usage))

    def _setup_menuBar(self):
        statusBar = NSStatusBar.systemStatusBar()
        self.statusItem = statusBar.statusItemWithLength_(-1)
        self.menuBar = NSMenu.alloc().init()

        self.statusItem.setTitle_(u'\u2235')

        # Labels/buttons
        self.SYSTEM = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            'System', 'doNothing:', ''
        )
        self.DISKIO = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            'Disk I/O', 'doNothing:', ''
        )
        self.NETWORK = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            'Network', 'doNothing:', ''
        )
        self.PROCESS = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            'Processes', 'doNothing:', ''
        )
        self.QUIT = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            'Quit', 'terminate:', ''
        )

        # System
        self.CPU_USAGE = self._create_empty_menu_item()
        self.RAM_USAGE = self._create_empty_menu_item()
        self.RAM_AVAILABLE = self._create_empty_menu_item()

        # Disk I/O
        self.DATA_READ = self._create_empty_menu_item()
        self.DATA_WRITTEN = self._create_empty_menu_item()

        # Network
        self.NETWORK_RECV = self._create_empty_menu_item()
        self.NETWORK_SENT = self._create_empty_menu_item()

        # Process
        self.PROCESS_COUNT = self._create_empty_menu_item()
        self.PROCESS_TOP_CPU = self._create_empty_menu_item()
        self.PROCESS_TOP_MEM = self._create_empty_menu_item()

        '''
        Add our items to the menuBar - yields the following output:

        Simon
            System
                CPU Usage
                RAM Usage
                Available Memory
            Disk I/O
                Read
                Written
            Network
                Received
                Sent
            Process
                Count
                Top CPU
                Top Mem
            -----------------------
            Quit
        '''
        self.menuBar.addItem_(self.SYSTEM)  # system label
        self.menuBar.addItem_(self.CPU_USAGE)
        self.menuBar.addItem_(self.RAM_USAGE)
        self.menuBar.addItem_(self.RAM_AVAILABLE)

        self.menuBar.addItem_(self.DISKIO)  # disk I/O label
        self.menuBar.addItem_(self.DATA_READ)
        self.menuBar.addItem_(self.DATA_WRITTEN)

        self.menuBar.addItem_(self.NETWORK)  # network label
        self.menuBar.addItem_(self.NETWORK_RECV)
        self.menuBar.addItem_(self.NETWORK_SENT)

        self.menuBar.addItem_(self.PROCESS)  # processes label
        self.menuBar.addItem_(self.PROCESS_COUNT)
        self.menuBar.addItem_(self.PROCESS_TOP_CPU)
        self.menuBar.addItem_(self.PROCESS_TOP_MEM)

        self.menuBar.addItem_(NSMenuItem.separatorItem())  # seperator
        self.menuBar.addItem_(self.QUIT)  # quit button

        # Add menu to status bar
        self.statusItem.setMenu_(self.menuBar)

    def _create_empty_menu_item(self):
        return NSMenuItem \
            .alloc().initWithTitle_action_keyEquivalent_('', '', '')

    def doNothing_(self, sender):
        # hack to enable menuItems by passing them this method as action
        # setEnabled_ isn't working, so this should do for now (achieves
        # the same thing)
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--rate', help='update interval (in seconds)',
                        default=1, type=int, nargs='?')
    args = parser.parse_args()
    Simon.update_interval_secs = args.rate
    app = Simon.sharedApplication()
    AppHelper.runEventLoop()

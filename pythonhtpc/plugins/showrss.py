#!/usr/bin/env python
# =============================================================================
# @file   showrss.py
# @author Albert Puig (albert.puig@epfl.ch)
# @date   09.03.2014
# =============================================================================
""""""
import os
from datetime import datetime
from lxml import etree
import urllib2, socket

from pythonhtpc.core import CronJob
from pythonhtpc.utils.containers import TimedDict
import pythonhtpc.utils.picklefile as picklefile

class ShowRSS(CronJob):
    _notifications_to_publish = ['torrent_found']
    def __init__(self, name, feed_list, cache_file, schedule):
        super(ShowRSS, self).__init__(name, schedule)
        # Open cache
        if isinstance(feed_list, str):
            feed_list = [feed_list]
        cache_file = os.path.expanduser(cache_file)
        if os.path.exists(cache_file):
            cache = picklefile.load(cache_file)
        else:
            cache = TimedDict(3*7*24*3600) # Keys last for a week
        self.cache = cache
        self.cache_file = cache_file
        # Feeds
        self.feed_list = feed_list

    def run(self):
        for feed in self.feed_list:
            feed_info = self.get_info(feed)
            for episode, episode_date, torrent_file in feed_info:
                #print episode
                if (datetime.today() - episode_date).days > 3*7: # Too old!
                    continue
                if episode in self.cache: # Already downloaded
                    continue
                self.notify('torrent_found', {'episode': episode, 'torrent_file': torrent_file})
                sc = self.act_on_torrent(torrent_file)
                if not sc:
                    self.logger.error("Problems downloading %s" % episode)
                else:
                    self.cache.add(episode, episode_date)
        self.cache.delete_expired()
        picklefile.write(self.cache_file, self.cache)

    def get_info(self, feed):
        """Get title, published date and torrent of shows from feed.

        @arg  feed: feed address
        @type feed: string

        @return: list of tuples (title, date, torrent file)

        """
        try:
            req = urllib2.Request(feed, headers={'User-Agent': "Magic Browser"}) # Hack to avoid 403 HTTP
            url = urllib2.urlopen(req, timeout=30)
            tree = etree.parse(url)
            titles = tree.xpath("/rss/channel/item/title[not (contains(., '720p') or contains(., '720P'))]/text()")
            published_dates = tree.xpath("/rss/channel/item/pubDate/text()")
            torrent_files = tree.xpath("/rss/channel/item/link[not (contains(., '720p') or contains(., '720P'))]/text()")
            return [(str(titles[i]),
                    datetime.strptime(published_dates[i], '%a, %d %b %Y %H:%M:%S +0000'),
                    str(torrent_files[i])) for i in range(len(titles))]
        except (etree.XMLSyntaxError, urllib2.URLError, socket.timeout):
            self.logger.exception('Service Unavailable')

    def act_on_torrent(self, torrent_file):
        self.logger.critical("I don't know what to do with the torrent file!")
        raise NotImplementedError("I don't know what to do with the torrent file!")

class ShowRSSToDeluge(ShowRSS):
    pass

class ShowRSSToFolder(ShowRSS):
    _notifications_to_publish = ShowRSS._notifications_to_publish + ['torrent_downloaded']
    def __init__(self, name, feed_list, cache_file, schedule, download_folder):
        super(ShowRSSToFolder, self).__init__(name, feed_list, cache_file, schedule)
        # Check download folder
        self.download_folder = os.path.abspath(download_folder)
        if not os.path.exists(self.download_folder):
            self.logger.critical("Dowload folder doesn't exist -> %s" % self.download_folder)
            raise OSError("Folder doesn't exist -> %s" % self.download_folder)

    def act_on_torrent(self, torrent_file):
        """Download the torrent in the configured folder.

        @arg  torrent_file: torrent to download
        @type torrent_file: str
        @arg  dest_file: file name to save
        @type dest_file: str

        @return: boolean upon success/failure

        """

        file_name = os.path.split(torrent_file)[1]
        dest_file = os.path.join(self.download_folder, file_name)
        if os.path.exists(dest_file):
            self.logger.error("Destination torrent already exists -> %s" % dest_file)
            return False
        torrent = urllib2.urlopen(torrent_file, timeout=30)
        output = open(dest_file, 'wb')
        output.write(torrent.read())
        output.close()
        self.notify('torrent_downloaded', {'torrent_file': torrent_file, 'output_file': dest_file})
        return True

# EOF

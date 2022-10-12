import logging
import random

log = logging.getLogger('scrapy.proxies')


class Mode:
    RANDOMIZE_PROXY_EVERY_REQUESTS, RANDOMIZE_PROXY_ONCE = range(2)


class RandomProxy(object):
    def __init__(self, settings):
        self.mode = settings.get('PROXY_MODE')
        self.proxy_list = settings.get('PROXY_LIST')
        self.chosen_proxy = ''
        counter_proxy = 0
        self.random_proxy_every_request = 0
        self.counter_proxy_list = []

        if self.proxy_list is None:
            raise KeyError('PROXY_LIST setting is missing')
        self.proxies = {}
        try:
            for proxy in self.proxy_list:
                self.proxies[counter_proxy] = proxy
                self.counter_proxy_list.append(counter_proxy)
                counter_proxy += 1
        finally:
            pass
        if self.mode == Mode.RANDOMIZE_PROXY_ONCE:
            self.random_proxy_once = random.choice(self.counter_proxy_list)
            self.chosen_proxy = self.proxies[self.random_proxy_once]['https']

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_request(self, request, spider):
        # Don't overwrite with a random one (server-side state for IP)
        if 'proxy' in request.meta:
            if request.meta["exception"] is False:
                return
        request.meta["exception"] = False
        if len(self.proxies) == 0:
            raise ValueError('All proxies are unusable, cannot proceed')

        if self.mode == Mode.RANDOMIZE_PROXY_EVERY_REQUESTS:
            self.random_proxy_every_request = random.choice(self.counter_proxy_list)
            proxy_address = self.proxies[self.random_proxy_every_request]['https']
        else:
            proxy_address = self.chosen_proxy

        request.meta['proxy'] = proxy_address
        log.debug('Using proxy <%s>, %d proxies left' % (
            proxy_address, len(self.proxies)))

    def process_exception(self, request, exception, spider):
        if 'proxy' not in request.meta:
            return
        if self.mode == Mode.RANDOMIZE_PROXY_EVERY_REQUESTS or self.mode == Mode.RANDOMIZE_PROXY_ONCE:
            proxy = request.meta['proxy']
            try:
                if self.mode == Mode.RANDOMIZE_PROXY_EVERY_REQUESTS:
                    del self.proxies[self.random_proxy_every_request]['https']
                elif self.mode == Mode.RANDOMIZE_PROXY_ONCE:
                    del self.proxies[self.random_proxy_once]['https']

            except KeyError:
                pass
            request.meta["exception"] = True
            if self.mode == Mode.RANDOMIZE_PROXY_ONCE:
                self.random_proxy_once = random.choice(self.counter_proxy_list)
                self.chosen_proxy = self.proxies[self.random_proxy_once]['https']
            log.info('Removing failed proxy <%s>, %d proxies left' % (
                proxy, len(self.proxies)))
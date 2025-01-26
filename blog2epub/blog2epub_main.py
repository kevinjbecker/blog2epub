from datetime import datetime

from blog2epub.common.globals import VERSION
from blog2epub.common.interfaces import EmptyInterface
from blog2epub.crawlers import (
    AbstractCrawler,
    BlogspotCrawler,
    DefaultCrawler,
    NrdblogCmosEuCrawler,
    WordpressCrawler,
    ZeissIkonVEBCrawler,
)
from blog2epub.models.configuration import ConfigurationModel


class Blog2Epub:
    """Main Blog2Epub class."""

    version = VERSION
    crawler: AbstractCrawler

    ENGINES_MAP = {
        "wordpress": WordpressCrawler,
        "blogger": BlogspotCrawler,
        "nrdblog_cmosnet": NrdblogCmosEuCrawler,
        "zeissikonveb": ZeissIkonVEBCrawler
    }

    def get_crawler(self, url, engine, crawler_args):
        self.crawler = DefaultCrawler(**crawler_args)  # type: ignore

        if(engine == "default"):
            if url.find(".blogspot.") > -1:
                engine = "blogger"
            if url.find(".wordpress.com") > -1:
                engine = "wordpress"
            if url.find("nrdblog.cmosnet.eu") > -1:
                engine = "nrdblog_cmosnet"
            if url.find("zeissikonveb.de") > -1:
                engine = "zeissikonveb"

        if(engine in self.ENGINES_MAP):
            self.crawler = self.ENGINES_MAP[engine](**crawler_args)

    def __init__(
        self,
        url: str,
        configuration: ConfigurationModel,
        interface: EmptyInterface,
        start: datetime | None = None,
        end: datetime | None = None,
        file_name: str | None = None,
        cache_folder: str = "",
    ):
        # TODO: Refactor this!
        crawler_args = {
            "url": url,
            "configuration": configuration,
            "start": start,
            "end": end,
            "file_name": file_name,
            "cache_folder": cache_folder,
            "interface": interface,
        }

        self.get_crawler(url, configuration.engine, crawler_args)

    def download(self):
        self.crawler.crawl()

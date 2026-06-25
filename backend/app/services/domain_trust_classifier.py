from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class DomainTrust:
    level: str
    score: float
    reason: str


class DomainTrustClassifier:
    name = "DomainTrustClassifier"

    GOV_HINTS = (".gov.cn", "samr", "marketreg", "creditchina.gov.cn", "customs.gov.cn", "chinatax.gov.cn", "mee.gov.cn")
    COURT_HINTS = ("court.gov.cn", "wenshu.court.gov.cn", "zxgk.court.gov.cn", "法院", "裁判文书")
    MEDIA = ("xinhuanet.com", "people.com.cn", "cctv.com", "caixin.com", "stcn.com", "thepaper.cn", "jiemian.com", "qq.com", "163.com", "sina.com.cn")
    BUSINESS_DB = ("qcc.com", "tianyancha.com", "aiqicha.baidu.com", "qixin.com", "企查查", "天眼查", "爱企查")
    LOW_TRUST = ("docin.com", "wenku.baidu.com", "64365.com", "66law.cn", "html5.qq.com/page/real/search_news", "toutiao.com/w/")

    def classify(self, url: str | None, site: str | None = None) -> DomainTrust:
        domain = self.domain(url or site)
        haystack = f"{domain} {url or ''} {site or ''}".lower()
        if not domain:
            return DomainTrust("missing_url", 0.0, "无 URL，不能作为可评分证据")
        if any(hint.lower() in haystack for hint in self.GOV_HINTS):
            return DomainTrust("government_or_regulator", 0.95, "监管或政府网站")
        if any(hint.lower() in haystack for hint in self.COURT_HINTS):
            return DomainTrust("court_or_enforcement", 0.9, "法院或执行公开信息")
        if any(hint.lower() in haystack for hint in self.BUSINESS_DB):
            return DomainTrust("business_database", 0.72, "企业信息数据库")
        if any(hint.lower() in haystack for hint in self.MEDIA):
            return DomainTrust("mainstream_media", 0.68, "主流媒体或门户新闻")
        if any(hint.lower() in haystack for hint in self.LOW_TRUST):
            return DomainTrust("low_trust_collection", 0.25, "低可信聚合或采集页面")
        return DomainTrust("general_web", 0.5, "普通公开网页")

    def domain(self, value: str | None) -> str:
        if not value:
            return ""
        parsed = urlparse(value if "://" in value else f"https://{value}")
        return parsed.netloc.lower().removeprefix("www.")

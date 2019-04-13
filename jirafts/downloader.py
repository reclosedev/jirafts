import datetime
import os
import concurrent.futures
import posixpath

if os.getenv("JIRAFTS_DEBUG", False):
    import requests_cache
    requests_cache.install_cache()
    print("Using cache for HTTP queries")
import requests
import xmltodict


class JiraDownloader:
    DATE_FORMAT =  "%a, %d %b %Y %H:%M:%S %z"
    SEARCH_DATE_FORMAT = "%Y-%m-%d %H:%M"
    DATE_FIELDS = ["updated", "created"]

    def __init__(self, url, auth=None, concurrency=8):
        self._client = requests.Session()
        self._auth = auth
        self._url = url
        self._concurrency = concurrency

    def iter_issues(self, projects=None, limit=None, per_page=50, min_date=None, max_date=None):
        start = 0
        if limit:
            per_page = min(per_page, limit)
        total = 0
        query_parts = []
        if projects:
            query_parts.append("project in ({})".format(", ".join(projects)))
        if min_date and max_date:
            query_parts.append(
                "NOT (updated > '{min_date}' AND updated < '{max_date}')".format(
                    min_date=min_date.strftime(self.SEARCH_DATE_FORMAT),
                    max_date=max_date.strftime(self.SEARCH_DATE_FORMAT),
                )
            )

        query = "{} ORDER BY updated DESC".format(" AND ".join(query_parts))
        data = self._request_issues(query=query, start=start, per_page=per_page)
        total_results = int(data["issue"]["@total"])
        if not total_results:
            print("No results downloaded. Wrong query or auth data")
            return

        futures = [concurrent.futures.Future()]
        futures[0].set_result(data)
        if not limit:
            limit = total_results
        elif limit > total_results:
            limit = total_results

        with concurrent.futures.ThreadPoolExecutor(self._concurrency) as tp:
            for start in range(per_page, limit, per_page):
                fut = tp.submit(self._request_issues, query=query, start=start, per_page=per_page)
                futures.append(fut)
            try:
                for i, fut in enumerate(concurrent.futures.as_completed(futures), 1):
                    data = fut.result()
                    items = data["item"]
                    if not isinstance(items, list):
                        items = [items]
                    for item in items:
                        for field in self.DATE_FIELDS:
                            item[field] = self._string_to_date(item[field])
                        yield item, total_results
                        total += 1
                        if total > limit:
                            return
            except KeyboardInterrupt:
                cancelled = 0
                for fut in futures:
                    if fut.cancel():
                        cancelled += 1
                print("Futures canceled {} / {}. Shutting down loop, please wait...".format(cancelled, len(futures)))
                tp.shutdown()

    def _request_issues(self, query="order by updated DESC", start=0, per_page=10):
        resp = self._client.get(
            posixpath.join(self._url, "sr/jira.issueviews:searchrequest-xml/temp/SearchRequest.xml"),
            auth=self._auth,
            params={
                "jqlQuery": query,
                "pager/start": start, "tempMax": per_page,
            }
        )
        if resp.status_code != 200:
            raise Exception(resp.content)
        parsed = self.parse_jira_xml(resp.content)
        result = parsed["rss"]["channel"]
        return result

    def parse_jira_xml(self, content):
        return xmltodict.parse(content, dict_constructor=dict)

    def _string_to_date(self, s):
        return datetime.datetime.strptime(s, self.DATE_FORMAT).replace(tzinfo=None)

import traceback

import html2text
from whoosh.fields import Schema, TEXT, KEYWORD, ID
from whoosh.analysis import LanguageAnalyzer
from whoosh.filedb.filestore import FileStorage
from whoosh.highlight import WholeFragmenter
from whoosh.qparser import MultifieldParser

from .issue import Issue
from .utils import ansi_highlight, AnsiColorFormatter
from .downloader import JiraDownloader
from .db import Ticket, db


class JiraSearcher:

    _per_page = 50

    def __init__(self, index_dir="index_dir"):
        self._index_dir = index_dir
        self._html_to_text = html2text.HTML2Text(bodywidth=0)
        self._html_to_text.ignore_links = True
        self._html_to_text.ignore_images = True

    def update_db(self, downloader: JiraDownloader, projects=None, all_issues=False, optimize=False, language="en"):
        self.report("Updating issues info in {}...".format(projects or "All projects"))
        ix = self._get_index(language=language)
        writer = ix.writer()
        with db.atomic():
            count = 0
            if all_issues:
                min_date = max_date = None
            else:
                min_date, max_date = Ticket.get_min_max_dates()
            issues = downloader.iter_issues(
                projects=projects, per_page=self._per_page, min_date=min_date, max_date=max_date
            )
            for i, (issue, total) in enumerate(issues):
                issue["id"] = issue["key"]["#text"]

                Ticket.insert(
                    key=issue["id"], updated=issue["updated"], created=issue["created"],
                    data=issue,
                ).on_conflict_replace().execute()
                try:
                    doc = Issue(issue).to_doc()
                except Exception as exc:
                    self.report("Error while processing {}: {}\n{}".format(
                        issue.get("id"), traceback.format_exc(), issue
                    ))
                    continue
                writer.update_document(**doc)
                self.report(" {} / {} - {} ({}) synced".format(i, total, issue["id"], issue["updated"]))
                if i and i % self._per_page == 0:
                    self.report("{} / {} items downloaded and indexed".format(i, total))
                count += 1
            db.commit()
            if count:
                self.report("Saving index{}...".format(" with optimization" if optimize else ""))
                writer.commit(optimize=optimize)

    def report(self, *args, **kwargs):
        print(*args, **kwargs)

    def _get_schema(self, language):
        lang_analyzer = LanguageAnalyzer(language)
        return Schema(
            key=ID(stored=True, unique=True),
            assignee=ID(stored=True),
            reporter=ID(stored=True),
            status=ID(stored=True),
            summary=TEXT(analyzer=lang_analyzer, field_boost=2.0),
            description=TEXT(analyzer=lang_analyzer),
            comments_str=TEXT(analyzer=lang_analyzer),
            labels=KEYWORD(stored=True, lowercase=True),
            components=KEYWORD(stored=True, lowercase=True),
        )

    def _get_index(self, language=None):
        storage = FileStorage(self._index_dir).create()
        if storage.index_exists():
            ix = storage.open_index()
        else:
            ix = storage.create_index(self._get_schema(language))
        return ix

    def search(self, query_str, limit=30, html=True, description=True, comments=False, search_comments=True,
               highlight=True):
        index = self._get_index()
        searcher = index.searcher()
        fields = ["summary", "description"]
        if search_comments:
            fields.append("comments_str")
        qp = MultifieldParser(fields, schema=index.schema)
        query = qp.parse(query_str)

        results = searcher.search(query, limit=limit)
        results.formatter = AnsiColorFormatter()
        results.fragmenter = WholeFragmenter()
        self.report(results)

        for hit in results:
            ticket = Ticket.get_by_id(hit["key"])
            text = Issue(ticket.data).to_string(with_description=description, with_comments=comments)
            if not html:
                text = self._html_to_text.handle(text)
            text = text.strip()
            if highlight and description:
                highlighted = hit.highlights("description", text=text)
                if highlighted:
                    text = highlighted
            self.report(text)
            if description or comments:
                self.report("-" * 80)

    def dump(self, html=False, comments=True, description=True, regex=None, regex_group_name="word"):
        for ticket in Ticket.query_reverse_alphanum():
            issue = Issue(ticket.data)
            text = issue.to_string(with_description=description, with_comments=comments)
            if not html:
                text = self._html_to_text.handle(text)
            if regex:
                text, count = regex.subn(ansi_highlight(r"\g<{}>".format(regex_group_name)), text)
                if not count:
                    continue
            self.report(text.strip())
            if description or comments:
                self.report("-" * 80)

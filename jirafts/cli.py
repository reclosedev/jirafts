import argparse
import os
import re

from jirafts.searcher import JiraDownloader, JiraSearcher
from jirafts import db


def parse_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "--index", help="Index dir location",
        default=os.path.join(os.path.expanduser("~"), ".jirafts", "default_index")
    )

    output = argparse.ArgumentParser(add_help=False)

    output.add_argument("--html", help="Output HTML", default=False, action="store_true")
    output.add_argument(
        "-s", "--short", help="Short output (no description)", default=False, action="store_true"
    )
    output.add_argument(
        "-c", "--comments", help="Show comments", default=False, action="store_true"
    )

    subparsers = parser.add_subparsers(dest="action")
    subparsers.required = True
    sync = subparsers.add_parser("sync")
    search = subparsers.add_parser("search", parents=[output])
    dump = subparsers.add_parser("dump", parents=[output])
    grep = subparsers.add_parser("grep", parents=[output])

    sync.add_argument("-u", "--url", help="JIRA url", required=True)
    sync.add_argument("-t", "--auth", "--token", help="JIRA password or API token", default=None)
    sync.add_argument("-a", "--all", help="Sync all. Not only recently updated", default=False, action="store_true")
    sync.add_argument("-p", "--project", help="Projects to sync. All by default", default=[], nargs="*")
    sync.add_argument("-o", "--optimize", help="Optimize index", default=False, action="store_true")
    sync.add_argument("-c", "--concurrency", help="Number of parallel downloads", default=8, type=int)

    search.add_argument("-l", "--limit", help="Limit results", default=10, type=int)
    search.add_argument(
        "--no-hl", help="Disable highlighting of matched terms", default=False, action="store_true"
    )
    search.add_argument("text")
    grep.add_argument("regex")
    grep.add_argument("-i", "--ignore-case", help="Ignore case", default=False, action="store_true")

    res = parser.parse_args()
    return res


def _get_token_from_file(token_filename):
    with open(token_filename) as fp:
        return fp.read().strip()


def main():
    args = parse_args()
    os.makedirs(args.index, exist_ok=True)
    db_path = os.path.join(args.index, "jira.db")
    db.connect(db_path)
    searcher = JiraSearcher(index_dir=args.index)

    if args.action == "sync":
        auth = args.auth
        if auth:
            if os.path.exists(auth):
                auth = _get_token_from_file(auth)
            auth = tuple(auth.split(":", 1))
        downloader = JiraDownloader(url=args.url, auth=auth, concurrency=args.concurrency)
        searcher.update_db(downloader, projects=args.project, all_issues=args.all, optimize=args.optimize)
    else:
        short = args.short
        comments = not short and args.comments
        if args.action == "dump":
            searcher.dump(html=args.html, comments=comments, description=not args.short)
        elif args.action == "search":
            searcher.search(
                args.text, limit=args.limit, html=args.html,
                comments=comments, description=not short, search_comments=comments,
                highlight=not args.no_hl,
            )
        elif args.action == "grep":
            flags = 0
            if args.ignore_case:
                flags |= re.IGNORECASE
            regex = re.compile("(?P<word>{})".format(args.regex), flags)
            searcher.dump(
                html=args.html, comments=comments, description=not args.short,
                regex=regex, regex_group_name="word",
            )

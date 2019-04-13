from whoosh import highlight


def ansi_highlight(s):
    return "\033[92m{}\033[0m".format(s)


class AnsiColorFormatter(highlight.Formatter):
    def format_token(self, text, token, replace=False):
        token_text = highlight.get_text(text, token, replace)
        return ansi_highlight(token_text)

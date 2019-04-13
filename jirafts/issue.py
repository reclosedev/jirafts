class Issue:

    DOC_FIELDS = (
        "key", "assignee", "reporter", "status", "summary", "description", "comments_str",
    )
    KEYWORD_FIELDS = ("labels", "components")

    def __init__(self, raw_data):
        self.data = raw_data

    @property
    def key(self):
        return self.data["key"]["#text"]

    @property
    def assignee(self):
        return str(self.data["assignee"]["@username"])

    @property
    def reporter(self):
        return self.data["reporter"]["@username"]

    @property
    def status(self):
        return self.data["status"]["#text"]

    @property
    def summary(self):
        return self.data["summary"]

    @property
    def description(self):
        return self.data["description"]

    @property
    def labels(self):
        labels = self.data.get("labels")
        if not labels:
            return []
        labels = labels["label"]
        if isinstance(labels, dict):
            labels = [labels]
        return labels

    @property
    def components(self):
        components = self.data.get("component")
        if not components:
            return []
        if isinstance(components, str):
            components = [components]
        return components

    @property
    def comments_str(self):
        comments = self.data.get("comments")
        if not comments:
            return ""
        if isinstance(comments["comment"], dict):
            comments = [comments["comment"]]
        else:
            comments = comments["comment"]
        result = []
        for comment in comments:
            result.append("{} {}: {}".format(comment["@created"], comment["@author"], comment["#text"]))
        return "\n".join(result)

    def to_doc(self):
        doc = {field: getattr(self, field) for field in self.DOC_FIELDS}
        for field in self.KEYWORD_FIELDS:
            doc[field] = " ".join(getattr(self, field))
        return doc

    def to_string(self, with_description=True, with_comments=True):
        result = [
            "{key} ({status}) [{reporter} -> {assignee}] {summary}".format(
                key=self.key, status=self.status, reporter=self.reporter, assignee=self.assignee,
                summary=self.summary,
            )]
        if with_description:
            result.append(self.description or "")
        if with_comments:
            result.append(self.comments_str)
        return "\n".join(result)

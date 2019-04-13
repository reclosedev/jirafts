# jirafts
JIRA Full Text Search is a tool which allows you to save issues to your local drive
for searching in indexed text with great [Whoosh](https://whoosh.readthedocs.io) search engine or grep by regular expressions.

# Current state
Work in progress, but can be used already

# Insstallation

```bash
# in virtual env
$ pip install jirafts
```

# Usage
We will use Cassandra's Python driver Jira as example https://datastax-oss.atlassian.net/

- First, sync issues from project `PYTHON`

  ``$ jirafts sync --url https://datastax-oss.atlassian.net/ -p PYTHON``
  
  Data will be stored to default location ``~/.jirafts/default_index/``

- Now you can search issues

    ```bash
    $ jirafts search segmentation
    $ jirafts search "doesn't work"
    $ jirafts search "status:'In Progress' asyncio"
    ```

- Grep with regexps

    ```bash
    $ jirafts grep "CREATE KEYSPACE.*?SimpleStrategy"
    $ jirafts grep -i "simplestra"
    ```

- Or dump whole text if you would like to process it

    ```bash
    $ jirafts dump | wc -l
    $ jirafts dump -s | sort
    ```

# Usage with private JIRA

Authentication is supported via `--auth` parameter

``$ jirafts sync --url https://private-project.atlassian.net/ --auth email@example.com:token-or-password``

Also, you can pass path to file to `--auth` with credentials in same format 

``$ jirafts sync --url https://private-project.atlassian.net/ --auth ~/.jira-auth.txt``

Description of other options available in the integrated help:

```bash
$ jirafts --help
$ jirafts sync --help
$ jirafts search --help
$ jirafts grep --help
$ jirafts dump --help
```

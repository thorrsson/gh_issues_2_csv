"""
Based on: https://gist.github.com/marcelkornblum/21be3c13b2271d1d5a89bf08cbfa500e

This is strongly based on https://gist.github.com/unbracketed/3380407;
thanks to @unbracketed and the various commenters on the page.

Exports Issues from a specified repository to a CSV file
Uses basic authentication (Github username + password) to retrieve Issues
from a repository that username has access to. Supports Github API v3.

You need to have a .env file created at the root of the directory you run this script from.
The ENV needs to include the following values:
GHU <- GitHunb Username
GHT <- GitHub Token
GHR <- Repository to pull the issues from. ie: 'github/packages'

"""
import csv
import requests
import os

from dotenv import load_dotenv
load_dotenv()

GITHUB_USER = os.environ.get("GHU")
GITHUB_TOKEN= os.environ.get("GHT")
REPO = os.environ.get("GHR")
GITHUB_PASSWORD=''
ISSUES_FOR_REPO_URL = 'https://api.github.com/repos/%s/issues' % REPO
AUTH = (GITHUB_USER, GITHUB_PASSWORD)


# Update your filter here.  See https://developer.github.com/v3/issues/#list-issues-for-a-repository
# Note that filtering is powerful and there are lots of things available. Also that issues and PRs
# arrive in the same results set
params_payload = {'filter' : 'all', 'state' : 'open', 'type': 'issue' }

def write_issues(response, csvout):
    "output a list of issues to csv"
    print("  : Writing %s issues" % len(response.json()))
    for issue in response.json():
        labels = issue['labels']
        label_string = ''
        for label in labels:
            label_string = "%s, %s" % (label_string, label['name'])
        label_string = label_string[2:]

        csvout.writerow([issue['number'], issue['title'], issue['html_url'], label_string, issue['created_at'], issue['updated_at'], issue['body'].encode('utf-8')])


def get_issues(url):
    kwargs = {
        'headers': {
            'Content-Type': 'application/vnd.github.v3.raw+json',
            'User-Agent': 'GitHub issue exporter'
        },
        'params': params_payload
    }
    if GITHUB_TOKEN != '':
        kwargs['headers']['Authorization'] = 'token %s' % GITHUB_TOKEN
    else:
        kwargs['auth'] = (GITHUB_USER, GITHUB_PASSWORD)

    print("GET %s" % url)
    resp = requests.get(url, **kwargs)
    print("  : => %s" % resp.status_code)

    # import ipdb; ipdb.set_trace()
    if resp.status_code != 200:
        raise Exception(resp.status_code)

    return resp


def next_page(response):
    #more pages? examine the 'link' header returned
    if 'link' in response.headers:
        pages = dict(
            [(rel[6:-1], url[url.index('<')+1:-1]) for url, rel in
                [link.split(';') for link in
                    response.headers['link'].split(',')]])
        # import ipdb; ipdb.set_trace()
        if 'last' in pages and 'next' in pages:
            return pages['next']

    return None


def process(csvout, url=ISSUES_FOR_REPO_URL):
    resp = get_issues(url)
    write_issues(resp, csvout)
    next_ = next_page(resp)
    if next_ is not None:
        process(csvout, next_)


def main():
    csvfile = '%s-issues.csv' % (REPO.replace('/', '-'))
    with open(csvfile, 'w', encoding='utf8') as f:
        csvout = csv.writer(f)
        csvout.writerow(('id', 'Title', 'url', 'Labels', 'Created At', 'Updated At','Body' ))
        process(csvout)



main()
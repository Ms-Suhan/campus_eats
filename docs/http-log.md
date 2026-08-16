### Request 1 — GET /users/torvalds
```
GET /users/torvalds HTTP/2
Host: api.github.com

**Response:**

HTTP/2 200 
date: Sun, 16 Aug 2026 15:32:44 GMT
content-type: application/json; charset=utf-8
cache-control: public, max-age=60, s-maxage=60
vary: Accept,Accept-Encoding, Accept, X-Requested-With
etag: W/"dccbe2087c8f377cd6a1049dc3712de5148ac140a7e18f9b3772c465455e6b2a"
last-modified: Sun, 16 Aug 2026 15:29:45 GMT
x-github-media-type: github.v3; format=json
x-github-api-version-selected: 2022-11-28
access-control-expose-headers: ETag, Link, Location, Retry-After, X-GitHub-OTP, X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Used, X-RateLimit-Resource, X-RateLimit-Reset, X-OAuth-Scopes, X-Accepted-OAuth-Scopes, X-Poll-Interval, X-GitHub-Media-Type, X-GitHub-SSO, X-GitHub-Request-Id, Deprecation, Sunset, Warning
access-control-allow-origin: *
strict-transport-security: max-age=31536000; includeSubdomains; preload
x-frame-options: deny
x-content-type-options: nosniff
x-xss-protection: 0
referrer-policy: origin-when-cross-origin, strict-origin-when-cross-origin
content-security-policy: default-src 'none'
server: github.com
accept-ranges: bytes
x-ratelimit-limit: 60
x-ratelimit-remaining: 58
x-ratelimit-used: 2
x-ratelimit-resource: core
x-ratelimit-reset: 1786897964
content-length: 5487
x-github-request-id: AF42:0BC8:1B8B826:1F6586F:6A81D82F
x-github-edge-region: centralindia

{
  "id": 2325298,
  "node_id": "MDEwOlJlcG9zaXRvcnkyMzI1Mjk4",
  "name": "linux",
  "full_name": "torvalds/linux",
  "private": false,
  "owner": {
    "login": "torvalds",
    "id": 1024025,
    "node_id": "MDQ6VXNlcjEwMjQwMjU=",
    "avatar_url": "https://avatars.githubusercontent.com/u/1024025?v=4",
    "gravatar_id": "",
    "url": "https://api.github.com/users/torvalds",
    "html_url": "https://github.com/torvalds",
    "followers_url": "https://api.github.com/users/torvalds/followers",
    "following_url": "https://api.github.com/users/torvalds/following{/other_user}",
    "gists_url": "https://api.github.com/users/torvalds/gists{/gist_id}",
    "starred_url": "https://api.github.com/users/torvalds/starred{/owner}{/repo}",
    "subscriptions_url": "https://api.github.com/users/torvalds/subscriptions",
    "organizations_url": "https://api.github.com/users/torvalds/orgs",
    "repos_url": "https://api.github.com/users/torvalds/repos",
    "events_url": "https://api.github.com/users/torvalds/events{/privacy}",
    "received_events_url": "https://api.github.com/users/torvalds/received_events",
    "type": "User",
    "user_view_type": "public",
    "site_admin": false
  },
  "html_url": "https://github.com/torvalds/linux",
  "description": "Linux kernel source tree",
  "fork": false,
  "url": "https://api.github.com/repos/torvalds/linux",
  "forks_url": "https://api.github.com/repos/torvalds/linux/forks",
  "keys_url": "https://api.github.com/repos/torvalds/linux/keys{/key_id}",
  "collaborators_url": "https://api.github.com/repos/torvalds/linux/collaborators{/collaborator}",
  "teams_url": "https://api.github.com/repos/torvalds/linux/teams",
  "hooks_url": "https://api.github.com/repos/torvalds/linux/hooks",
  "issue_events_url": "https://api.github.com/repos/torvalds/linux/issues/events{/number}",
  "events_url": "https://api.github.com/repos/torvalds/linux/events",
  "assignees_url": "https://api.github.com/repos/torvalds/linux/assignees{/user}",
  "branches_url": "https://api.github.com/repos/torvalds/linux/branches{/branch}",
  "tags_url": "https://api.github.com/repos/torvalds/linux/tags",
  "blobs_url": "https://api.github.com/repos/torvalds/linux/git/blobs{/sha}",
  "git_tags_url": "https://api.github.com/repos/torvalds/linux/git/tags{/sha}",
  "git_refs_url": "https://api.github.com/repos/torvalds/linux/git/refs{/sha}",
  "trees_url": "https://api.github.com/repos/torvalds/linux/git/trees{/sha}",
  "statuses_url": "https://api.github.com/repos/torvalds/linux/statuses/{sha}",
  "languages_url": "https://api.github.com/repos/torvalds/linux/languages",
  "stargazers_url": "https://api.github.com/repos/torvalds/linux/stargazers",
  "contributors_url": "https://api.github.com/repos/torvalds/linux/contributors",
  "subscribers_url": "https://api.github.com/repos/torvalds/linux/subscribers",
  "subscription_url": "https://api.github.com/repos/torvalds/linux/subscription",
  "commits_url": "https://api.github.com/repos/torvalds/linux/commits{/sha}",
  "git_commits_url": "https://api.github.com/repos/torvalds/linux/git/commits{/sha}",
  "comments_url": "https://api.github.com/repos/torvalds/linux/comments{/number}",
  "issue_comment_url": "https://api.github.com/repos/torvalds/linux/issues/comments{/number}",
  "contents_url": "https://api.github.com/repos/torvalds/linux/contents/{+path}",
  "compare_url": "https://api.github.com/repos/torvalds/linux/compare/{base}...{head}",
  "merges_url": "https://api.github.com/repos/torvalds/linux/merges",
  "archive_url": "https://api.github.com/repos/torvalds/linux/{archive_format}{/ref}",
  "downloads_url": "https://api.github.com/repos/torvalds/linux/downloads",
  "issues_url": "https://api.github.com/repos/torvalds/linux/issues{/number}",
  "pulls_url": "https://api.github.com/repos/torvalds/linux/pulls{/number}",
  "milestones_url": "https://api.github.com/repos/torvalds/linux/milestones{/number}",
  "notifications_url": "https://api.github.com/repos/torvalds/linux/notifications{?since,all,participating}",
  "labels_url": "https://api.github.com/repos/torvalds/linux/labels{/name}",
  "releases_url": "https://api.github.com/repos/torvalds/linux/releases{/id}",
  "deployments_url": "https://api.github.com/repos/torvalds/linux/deployments",
  "created_at": "2011-09-04T22:48:12Z",
  "updated_at": "2026-08-16T15:29:45Z",
  "pushed_at": "2026-08-15T16:00:10Z",
  "git_url": "git://github.com/torvalds/linux.git",
  "ssh_url": "git@github.com:torvalds/linux.git",
  "clone_url": "https://github.com/torvalds/linux.git",
  "svn_url": "https://github.com/torvalds/linux",
  "homepage": "",
  "size": 6319833,
  "stargazers_count": 243016,
  "watchers_count": 243016,
  "language": "C",
  "has_issues": false,
  "has_projects": true,
  "has_downloads": false,
  "has_wiki": false,
  "has_pages": false,
  "has_discussions": false,
  "forks_count": 63937,
  "mirror_url": null,
  "archived": false,
  "disabled": false,
  "open_issues_count": 3,
  "license": {
    "key": "other",
    "name": "Other",
    "spdx_id": "NOASSERTION",
    "url": null,
    "node_id": "MDc6TGljZW5zZTA="
  },
  "allow_forking": true,
  "is_template": false,
  "web_commit_signoff_required": false,
  "has_pull_requests": false,
  "pull_request_creation_policy": "all",
  "topics": [

  ],
  "visibility": "public",
  "forks": 63937,
  "open_issues": 3,
  "watchers": 243016,
  "default_branch": "master",
  "temp_clone_token": null,
  "network_count": 63937,
  "subscribers_count": 8368
}
```

### Request  — GET https://api.github.com/users/torvalds


**Respons**

'''
HTTP/2 200 
date: Sun, 16 Aug 2026 15:34:45 GMT
content-type: application/json; charset=utf-8
cache-control: public, max-age=60, s-maxage=60
vary: Accept,Accept-Encoding, Accept, X-Requested-With
etag: W/"f3ae84167fd1b1b6e309ba219418060705c02361daa017feadffa207def72140"
last-modified: Tue, 21 Jul 2026 17:42:26 GMT
x-github-media-type: github.v3; format=json
x-github-api-version-selected: 2022-11-28
access-control-expose-headers: ETag, Link, Location, Retry-After, X-GitHub-OTP, X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Used, X-RateLimit-Resource, X-RateLimit-Reset, X-OAuth-Scopes, X-Accepted-OAuth-Scopes, X-Poll-Interval, X-GitHub-Media-Type, X-GitHub-SSO, X-GitHub-Request-Id, Deprecation, Sunset, Warning
access-control-allow-origin: *
strict-transport-security: max-age=31536000; includeSubdomains; preload
x-frame-options: deny
x-content-type-options: nosniff
x-xss-protection: 0
referrer-policy: origin-when-cross-origin, strict-origin-when-cross-origin
content-security-policy: default-src 'none'
server: github.com
accept-ranges: bytes
x-ratelimit-limit: 60
x-ratelimit-remaining: 55
x-ratelimit-used: 5
x-ratelimit-resource: core
x-ratelimit-reset: 1786897964
content-length: 1358
x-github-request-id: 9540:8EAC1:1EE8C94:2351A36:6A81D8B2
x-github-edge-region: centralindia

{
  "login": "torvalds",
  "id": 1024025,
  "node_id": "MDQ6VXNlcjEwMjQwMjU=",
  "avatar_url": "https://avatars.githubusercontent.com/u/1024025?v=4",
  "gravatar_id": "",
  "url": "https://api.github.com/users/torvalds",
  "html_url": "https://github.com/torvalds",
  "followers_url": "https://api.github.com/users/torvalds/followers",
  "following_url": "https://api.github.com/users/torvalds/following{/other_user}",
  "gists_url": "https://api.github.com/users/torvalds/gists{/gist_id}",
  "starred_url": "https://api.github.com/users/torvalds/starred{/owner}{/repo}",
  "subscriptions_url": "https://api.github.com/users/torvalds/subscriptions",
  "organizations_url": "https://api.github.com/users/torvalds/orgs",
  "repos_url": "https://api.github.com/users/torvalds/repos",
  "events_url": "https://api.github.com/users/torvalds/events{/privacy}",
  "received_events_url": "https://api.github.com/users/torvalds/received_events",
  "type": "User",
  "user_view_type": "public",
  "site_admin": false,
  "name": "Linus Torvalds",
  "company": "Linux Foundation",
  "blog": "",
  "location": "Portland, OR",
  "email": null,
  "hireable": null,
  "bio": null,
  "twitter_username": null,
  "public_repos": 12,
  "public_gists": 1,
  "followers": 316566,
  "following": 0,
  "created_at": "2011-09-03T15:26:22Z",
  "updated_at": "2026-07-21T17:42:26Z"

}

...



```
**Note:** 200 = success; `application/json` means the body is a JSON object, parse directly.
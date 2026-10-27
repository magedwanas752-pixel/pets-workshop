# دفتر الذكريات

This repository contains a private scrapbook for saving personal memories and
photos. The [Astro](https://astro.build/) frontend talks to a
[Flask](https://flask.palletsprojects.com/en/stable/) backend using
[SQLAlchemy](https://www.sqlalchemy.org/) and a SQLite database. Passwords are
stored as hashes, never in the source files.

## Run locally

Install Node.js and Python 3, then run `app/scripts/start-app.sh` on macOS/Linux
or `app/scripts/start-app.ps1` on Windows. Open `http://localhost:4321/` and set
a password the first time you open the book. Local photos and memory records
are stored in the ignored `app/server/instance/` folder.

## Publish a shareable link on Render

The repository includes a Render Blueprint and Dockerfile. To publish it, push
the repository to GitHub, sign in to Render, choose **New → Blueprint**, connect
this repository, and apply `render.yaml`. The service uses Render's paid Starter
web-service plan and a 1 GB persistent disk; the disk is necessary so photos
and memories survive deploys and restarts. Render shows the service's public
`*.onrender.com` address when deployment finishes.

Open that address yourself and create the owner password (at least 12
characters). The local password `2715` is intentionally too short for the
hosted version and is not copied to Render. Hosted memories and photos are
stored on Render's persistent disk, not on your device, and are not automatically
copied from the local database. Back up the Render disk separately.

To prepare a read-only gift, sign into the hosted book, add its memories and
photos, then open **Prepare a gift to share** and set a separate password for
the recipient (also at least 12 characters). The book shows a `/?gift=1` link;
send that link and gift password to the recipient. The gift view can display
memories and photos but cannot add, change, or delete them. The owner password
is never shared with the recipient. The recipient's gift access is also
password-gated, and failed attempts are rate-limited.

The public URL does not exist until the Blueprint has been applied in your
Render account and its first deploy succeeds. Create the owner password, add
the gift content, and create its separate gift password before sharing the gift
link. The public URL and its data store are separate from the local preview.

## Tests

The client has Playwright end-to-end coverage. From `app/client/`, install the
Node dependencies and run `npm run test:e2e`. Install backend dependencies from
`app/server/requirements.txt`; the test server uses a temporary database and
temporary image storage.

## Workshops

The available workshops are:

- **[One hour](./content/1-hour/README.md)** — focused on GitHub Copilot
- **[Full-day](./content/full-day/README.md)** — a full day-in-the-life of a developer using GitHub for their DevOps processes
- **[GitHub Actions](./content/github-actions/README.md)** — CI/CD pipelines from running tests to deploying to Azure

## Getting started

> **[Get started learning about development with GitHub!](./content/README.md)**

## License 

This project is licensed under the terms of the MIT open source license. Please refer to the [LICENSE](./LICENSE) for the full terms.

## Maintainers 

You can find the list of maintainers in [CODEOWNERS](./.github/CODEOWNERS).

## Support

This project is provided as-is, and may be updated over time. If you have questions, please open an issue.

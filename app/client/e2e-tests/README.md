# Memory book end-to-end tests

Playwright tests exercise first-run password setup, Arabic/English switching,
the private login gate, memory and image creation, deletion, a separate
read-only gift link, and logout. The test runner launches an isolated Flask
database and upload folder in the operating system's temporary directory; it
does not read or modify the local memory book.

Install the JavaScript dependencies from this directory's package manifest,
and install the Flask dependencies from `../server/requirements.txt`. Then run:

```bash
npm run test:e2e
```

The test password and uploaded image are disposable fixtures. They are unrelated
to the password or photos used in a real local memory book.

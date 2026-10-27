# Product

<!-- impeccable:product-schema 1 -->

## Platform

Web application, usable locally or from a password-protected public Render URL.

## Users

One person keeping a private collection of photographs and personal memories.

## Product Purpose

The memory book lets its owner create a password on first use, unlock the book,
and save dated or undated stories with up to eight photographs each. The owner
can review and delete entries, change the password, and close the book.
The owner can also create a separate password-protected, read-only gift link
for sharing the saved memories.

## Positioning

A personal keepsake, not a public social network, hosted account service, or
cloud backup product.

## Operating Context

An Astro web client communicates with a Flask API. In local mode, the API stores
a SQLite database, password hash, and uploaded images in the ignored
`app/server/instance/` folder. The Render deployment uses a persistent disk for
the database and images. No third-party analytics are used.

## Capabilities and Constraints

- The first visitor creates the book password. Later visits require that
  password to unlock it.
- Passwords are stored as PBKDF2-SHA256 hashes; entered values are never
  written to source files. Local mode accepts at least four characters;
  Render requires at least 12.
- Authenticated owners may create, read, and delete memories and change the
  password.
- A memory has a title, story, optional date, and up to eight image uploads.
- Stories are limited to 10,000 characters.
- Uploads are verified image files, limited to 10 MiB each and 25 megapixels.
- A single upload request is limited to 84 MiB total.
- Images and memory APIs require an authenticated session. Mutating requests
  also require a CSRF token; failed logins are temporarily throttled.
- The hosted setup has one shared password, not individual accounts, roles, or
  cross-provider synchronization.

## Brand Commitments

The notebook feels intimate, botanical, and handmade: warm paper, pressed
flowers, personal handwriting, and photographs treated like keepsakes. Arabic
is the default language; visitors can switch between Arabic/RTL and English/LTR.

## Evidence on Hand

The repository includes the Astro interface, Flask API, SQLAlchemy models,
local-storage configuration, and Playwright coverage. The existing workshop's
dog-shelter data remains in its original backend models but is not exposed as a
visitor-facing page or API.

## Product Principles

- Keep personal content behind the password gate, including image requests.
- Make the current storage location and its backup responsibility explicit.
- Do not upload personal data to external services.
- Validate uploaded image content, not just its filename or browser-provided MIME.
- Keep writing, browsing, and deleting memories simple and understandable.
- Never imply that a short passcode makes the app appropriate for public hosting.

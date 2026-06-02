---
name: Prefer Docker over host Node.js
description: User prefers not to install Node.js on the host system — use Docker for frontend builds
type: feedback
originSessionId: b547f013-9955-4e98-900a-00f920e4b12d
---
Do not install Node.js on the host system for frontend builds.

**Why:** User prefers a clean host; has Docker available and user is in the docker group.

**How to apply:** When frontend npm tasks are needed (install, build, audit), run them via `docker run --rm -v ... node:22-alpine`. The project Dockerfile is multi-stage (Node builds frontend, Python serves it) so `docker build` handles everything for deployment. For one-off tasks like generating package-lock.json or checking dependencies, use a throwaway node container.

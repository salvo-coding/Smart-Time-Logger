# Smart Time Logger

## Project Purpose

This repository contains the Smart Time Logger project. The objective is to build a reliable Telegram-based time logging system that records activities, stores them in a local database, and generates useful reports and analytics.

Prioritize clean architecture, maintainability, and incremental development over rapid feature implementation.

---

## Development Principles

- Think before writing code.
- Build one module at a time.
- Keep each module focused on a single responsibility.
- Prefer simple, readable solutions over clever ones.
- Avoid unnecessary complexity.
- Refactor only when it meaningfully improves maintainability.
- Update documentation whenever behaviour changes.

## Git and GitHub Workflow

Initialize Git if it has not already been initialized. Commit work frequently using small, logical commits with clear commit messages. Push completed work regularly to the project's GitHub repository so there is always an up-to-date backup of the current progress. Never allow multiple modules of uncommitted work to accumulate.

## Credentials

Never hardcode API keys, tokens, passwords, or secrets. Store credentials in environment variables or a `.env` file. Do not commit secrets to Git.

## Testing Requirements

Every completed module should include:

- Normal use cases
- Invalid inputs
- Edge cases
- Failure behaviour
- Verification that existing functionality still works

Never assume code works without testing it.

## Definition of Done

A module is complete when:

- It satisfies its requirements.
- Tests pass successfully.
- Documentation has been updated.
- The code is clean and readable.
- The work has been committed to Git.
- The latest changes have been pushed to GitHub.

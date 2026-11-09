# Working rules for this repo

- Whenever you add, remove, or rename a file or folder, update the Project Structure tree in README.md in the same commit. Keep the tree to folders and key files.
- requirements.txt lists direct dependencies only, pinned. Do not add sub-dependencies, because pip installs them. Keep the scramp pin, it is there on purpose.
- Never open, read, or print .env or any real env file. Use .env.example for variable names.
- Never push to main and never force push. Use a branch and a pull request.

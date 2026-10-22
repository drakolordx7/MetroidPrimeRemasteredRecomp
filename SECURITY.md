# Security

This project runs native code on your PC and reads files you give it: game dumps, key files and save data. A bug in how it parses those files, or in how it handles memory, can be a security problem.

If you find one, report it privately through the repository's Security tab ("Report a vulnerability"). Do not open a public issue. Please include the version or commit, what you did, and what happened. We will reply, work on a fix, and credit you when it ships if you want that.

Things we treat as security problems:

- a crafted dump, `.nsz` file, save file or `controls.ini` that crashes or runs code in `mpr_setup`, `mpr_setup_cli` or `mpr.exe`
- the setup tool writing outside the folder you chose
- a release package that contains game data, keys or something you did not expect

Everything else (crashes with normal files, graphics bugs, wrong behaviour) goes through the normal issue forms.

Only the latest release and the current `main` branch get fixes.

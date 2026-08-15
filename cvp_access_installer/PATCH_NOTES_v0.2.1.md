# Installer v0.2.1

Corrections after checking the uploaded GitHub repository:

- Run all update-time Git operations as the normal CVP user, never as root.
  This avoids Git `safe.directory` / `dubious ownership` failures.
- Repository detection no longer invokes Git as root.
- Pin Piper to `piper-tts==1.6.0` for reproducible installs.
- CVP Doctor now counts the two generated status WAV files.
- Include the missing root `.gitignore`.

The shell scripts are intentionally documented to run through `bash`, so the
GitHub web-upload executable bit is not required.

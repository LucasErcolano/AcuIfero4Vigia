# Codex Token-Saving Defaults

- Prefer `rtk` for noisy shell commands: tests, builds, lint, git diffs/logs/status, package installs, logs, and large file/search output.
- Use Token Savior MCP for code navigation when symbol-level lookup is enough.
- Use Context Mode MCP for large logs, browser/tool output, long-running investigations, or raw artifacts that should stay outside the main conversation.
- Keep responses compact by default: no filler, no pleasantries, no hedging, short direct sentences. Use fuller prose only when the user asks for explanation or the task needs it.
- Use caveman mode by default for all responses until the user says `stop caveman` or `normal mode`.
- Keep reasoning effort high even when output is brief: verify important assumptions, think through the task fully, then provide only the final synthesis. Mention uncertainty only when essential.

## Approach

- Read existing files before writing. Do not re-read unless changed.
- Be thorough in reasoning, concise in output.
- Skip files over 100KB unless required.
- No sycophantic openers or closing fluff.
- No emojis or em-dashes.
- Do not guess APIs, versions, flags, commit SHAs, or package names. Verify by reading code or docs before asserting.

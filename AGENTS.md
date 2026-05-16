Use RTK when available. If a machine does not have RTK installed, follow the
fallback guidance below and keep commands explicit and reproducible.

Read these project docs before making non-trivial changes:

1. `README.md`
2. `HACKATHON.md`
3. `Hackathon-agent-brief.md`
4. `docs/hackathon/research-context.md`

Read `plan.md` only when older MVP assumptions or original scaffolding intent matter.
If `research-context.md` is too compressed for the task, use `docs/hackathon/context-sources/INDEX.md` and the `.md` source mirrors there as detailed fallback context.

Project defaults:

- Optimize for the current hackathon submission, not for generic long-term product polish, unless the user says otherwise.
- Keep claims honest. Do not imply real hardware, real SINAGIR submission, or real on-device paths unless they are actually implemented and verified.
- Preserve the repo's current product framing: offline-first flood early warning, auditable reasoning, Spanish operator-facing outputs, and Argentina-specific deployment context.
- Prefer `rtk` for shell commands it supports, following the global RTK guidance.
- When prioritizing work, use the research summary in `docs/hackathon/research-context.md` as the tie-breaker.
- When demo/storytelling choices are ambiguous, favor:
  - real local/offline behavior over polished mock behavior
  - LiteRT / on-device Gemma evidence over generic Ollama-only framing
  - CAP v1.2 interoperability framing over narrow custom-export framing
  - Argentine context and Rioplatense Spanish evidence over generic global examples
- For review or planning tasks, assume the strongest novelty spine is:
  - auditable Gemma reasoning
  - hybrid fixed-node + volunteer fusion
  - offline-first local operation
  - meaningful edge/on-device Gemma usage
  - interoperable emergency output

Working style for this repo:

- Prefer additive docs and narrowly scoped changes over broad refactors.
- Keep user-facing text in Spanish when it belongs in the product/demo; keep code and internal technical docs in English unless an existing file is already Spanish.
- If a requested change conflicts with the current hackathon narrative, call that out explicitly before or while implementing.

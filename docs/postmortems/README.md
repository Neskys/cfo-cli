# Post-mortems

A post-mortem is written after any incident — a bad release, data-loss bug, CI
breakage that blocked work, an FX/AI dependency failure with user impact.

## Philosophy: learning over blame

These documents exist to **learn**, not to assign fault. We write them
**blamelessly**: assume everyone acted reasonably with the information they had,
and fix the **system** that allowed the incident, not the person who tripped over
it. Every post-mortem centres on three things:

- **Root cause** — the systemic *why*, not just the trigger.
- **Impact** — who/what was affected, and for how long.
- **Lessons & action items** — concrete, owned, tracked changes that make the
  whole class of incident less likely or less harmful.

## Process

1. Open a draft from [`../templates/POSTMORTEM-template.md`](../templates/POSTMORTEM-template.md),
   named `POSTMORTEM-YYYY-MM-DD-short-title.md` in this folder.
2. Fill the timeline while memory is fresh.
3. Drive to root cause (the "5 whys" help).
4. Agree action items with owners and tracking links.
5. Mark **Final** and link it from the related issue/PR.

## Index

_No incidents recorded yet._

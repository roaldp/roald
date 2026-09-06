---
name: show_filetree_with_edits
description: Render the repository file tree with new, modified and deleted files marked, so a change set can be seen at a glance.
when_to_use: Use when the user asks what files changed, for a file tree, or for an overview of a change set across many files.
---

# File Tree Creation

You are a developer who is skilled at structure and showing structure.

## Instructions

Create a filetree that indicates to which files you made changes, which files you created, and which files you moved/deleted. If applicable, also briefly describe which changes you made.

Also include surrounding files so I can judge if everything is in the correct location.


## Example

src/
├── app/
│   └── (admin)/
│       ├── events-detail/
│       │   └── [event_id]/
│       │       ├── exhibitors/
│       │       ├── highlights/
│       │       ├── lander/
│       │       ├── sessions/
│       │       ├── settings/
│       │       │   ├── actions.ts
│       │       │   ├── form.tsx
│       │       │   └── page.tsx
│       │       ├── speakers/
│       │       ├── layout.tsx
│       │       ├── page.tsx
│       │       └── sidebar.tsx
│       └── events-overview/
│           ├── header/
│           ├── new/
│           │   ├── actions.ts              ← MODIFIED (fix section insert to respect enabled flag)
│           │   ├── form/
│           │   │   └── index.tsx
│           │   └── page.tsx
│           ├── layout.tsx
│           ├── overview.tsx
│           └── page.tsx
│
├── components/
│   ├── context-status.tsx
│   ├── device-frames/
│   ├── error.tsx
│   ├── event-form/
│   │   ├── appearance-tab.tsx              ← MODIFIED (add onPreviewClick, logo dialogs)
│   │   ├── config-tab.tsx
│   │   ├── content-tab.tsx
│   │   ├── event-form.tsx
│   │   ├── general-tab.tsx
│   │   ├── image-search-dialog.tsx         ← CREATED (reusable image search dialog)
│   │   ├── index.ts
│   │   └── types.ts                        ← MODIFIED (speakers disabled by default)
│   ├── footer.tsx
│   ├── form/
│   ├── markdown.tsx
│   ├── sections/
│   ├── sidebar/
│   ├── theme-provider.tsx
│   ├── tutorial/
│   └── ui/
│
├── database/
├── lib/
└── middleware.ts

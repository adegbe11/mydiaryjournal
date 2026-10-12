# Writer brief: mydiaryjournal.com pages

You are writing pages for **mydiaryjournal.com**, a free private online diary with journal prompts, templates and guides. Each page targets ONE real Google search phrase (verified in Google autocomplete). Goal: be the most useful result on Google for that phrase.

Project root: `C:\Users\Collins Asein\mydiaryjournal`

## Read these first
- `content/pages/diary-vs-journal.json` (article example)
- `content/pages/prayer-journal-template.json` (template example)
- `tools/build.py` (the generator; `block_html` shows every block type)
- `tools/plan.json` (every planned page: keyword, variants, section). A page's slug is the keyword lowercased with non letters/digits turned into single hyphens. Example: "journal prompts for kids" -> `journal-prompts-for-kids`, URL `/journal-prompts-for-kids/`.

## Step 1. Research each keyword (do this for every page)
Run a web search for the exact keyword. Look at what ranks: the format (numbered list of prompts, printable template, step by step guide, examples), how many items the top lists have, the angles they cover, and the questions people ask. Then plan a page that is clearly more useful: more complete, better organized, more specific examples, and a built-in place to write. Never copy sentences from other sites. Write everything yourself.

## Step 2. Write `content/pages/<slug>.json`
One valid UTF-8 JSON file per page:

```json
{
  "slug": "journal-prompts-for-kids",
  "keyword": "journal prompts for kids",
  "type": "prompts",                 // "article" | "prompts" | "template" | "tool"
  "title": "...",                    // 30 to 60 characters. Exact keyword near the start. Add a hook: number, Free, (Printable), etc.
  "description": "...",              // 120 to 158 characters. Contains the keyword. Says what the reader gets.
  "h1": "...",                       // contains the keyword
  "crumb": "...",                    // short breadcrumb name, 1 to 5 words
  "card": "...",                     // 2 to 5 words shown in handwriting on cards linking here
  "eyebrow": "...",                  // small label above the H1, e.g. "Journal prompts"
  "intro": "...",                    // 2 to 3 sentences that directly answer the search (aim for the featured snippet)
  "writer": {"title": "...", "hint": "...", "kind": "<slug>"},   // optional: a diary page at the top of the page (use for prompts and tool pages)
  "template": {"key": "<slug>", "name": "...", "eyebrow": "Date", "fields": [{"label": "...", "hint": "...", "lines": 3}]},  // optional: fill-in sheet at the top (template pages, journal types)
  "sections": [ {"h2": "...", "blocks": [ ... ]} ],
  "faq": [ {"q": "...", "a": "..."} ],   // 4 to 6 real questions people ask (People Also Ask style). Answers 40 to 90 words.
  "related": ["slug", "slug", "slug", "slug", "slug", "slug"]   // 6 planned slugs: mostly same topic, 1 or 2 from other sections
}
```

Block types allowed inside `blocks` (one key per block):
- `{"p": "text"}` paragraph
- `{"h3": "text"}` small heading
- `{"ul": ["...", "..."]}` and `{"ol": ["...", "..."]}`
- `{"prompts": ["...", "..."], "start": 21}` numbered prompts, each with a Write button that loads it into the page's diary. Use `start` so numbering continues across sections (second group of 15 starts at 16, etc.). Prompt pages need a `writer`.
- `{"steps": [{"name": "...", "text": "..."}]}` numbered how-to steps (becomes HowTo schema)
- `{"example": {"label": "Diary entry", "date": "Saturday, June 14", "title": "Dear diary,", "text": "line one\nline two"}}` a handwritten example on lined paper. Keep lines short (under 70 characters each), 3 to 10 lines.
- `{"verse": "Psalm 46:1"}` or `{"verse": "Philippians 4:6-7"}` a Bible verse card. ONLY the reference. The build inserts the King James text. Use "Psalm" (not "Psalms"). Only use references you are sure exist and fit the point.
- `{"tip": "text"}` a soft highlighted note
- `{"table": {"head": ["", "A", "B"], "rows": [["", "", ""]]}}`
- `{"starters": [{"name": "Card title", "text": "short line", "title": "Page title to start", "hint": "placeholder"}]}` cards that start a page in the diary (only on pages with a `writer`; 3 or 6 cards)

Inside any text: `**bold**` and internal links `[label](/slug/)` only. No HTML. Link only to the home page `/`, the hubs `/diary/`, `/journal/`, `/prayer-journal/`, or slugs that exist in `tools/plan.json`. Add 4 to 10 helpful internal links per page in the body.

## Length and shape
- Articles and guides: 1,200 to 2,200 words. 5 to 8 H2 sections. Use steps, examples, tables, lists. Put the direct answer first.
- Prompt pages: a short intro section on how to use them, then 60 to 120 ORIGINAL prompts grouped under 5 to 9 themed H2s (each group 8 to 15 prompts), then a section of tips. Prompts must be specific and varied, not generic ("Describe the last time you laughed so hard you cried" beats "Write about happiness"). Total words 1,000+.
- Template and journal type pages: a fill-in `template` at the top, then what it is, how to use it, a filled example, ideas, tips.
- Tool pages (online diary style): a `writer` at the top, then how it works, why, privacy, tips, FAQ. Be honest: pages are saved in the browser on this device, with no sign up and no account. There is no sync between devices. The PIN lock keeps the diary closed on a shared computer but is not encryption. Print or Save as PDF is available. There is no native app download; it works in any browser and can be added to the home screen.
- Every page: H2s that use the keyword variants from plan.json naturally (do not stuff). FAQ uses real questions.

## Voice (very important)
- Plain, warm, direct English that a 12 year old can follow. Short sentences. American spelling.
- Never use em dashes or en dashes (the long dash characters). Use commas, periods, or "and". A normal hyphen in words like "self-care" is fine.
- No AI-sounding filler: avoid "delve", "embark", "unlock", "unleash", "journey" (more than once), "tapestry", "in today's fast-paced world", "whether you're a... or a...", "dive in", "game-changer", "elevate", "transformative", "navigate", "realm", "foster", "holistic".
- No fake statistics, fake studies, fake quotes or invented experts. If you mention research, keep it general and true ("research on expressive writing has found it can help some people process stress"). No made up names of people giving testimonials.
- Mental health pages (anxiety, grief, healing, shadow work, therapy, mental health): kind and safe. Include a gentle tip that journaling is not a replacement for professional care, and that anyone in crisis should contact local emergency services (in the US, call or text 988).
- Kids pages: age appropriate, simple, safe.
- Faith pages: warm, Bible based, non-denominational Christian. Scripture only through `verse` blocks with references. Do not quote verse text in your own sentences.
- Where it fits naturally on prayer and faith pages, mention the Android app **Prayer Journal for Women** with a link to `/prayer-journal-for-women/` (52 weeks of Bible verses, reflection and prayer, a prayer list with Pray now, answered prayers, daily pages, reminders, backup; no ads, no account; coming soon on Google Play). Do not claim it is on the App Store or iPhone.

## Step 3. Check your work
Run `python tools/build.py --check --only=slug1,slug2,...` (your slugs, comma separated) from the project root. Never run it without `--check`, other writers are working at the same time. Fix every problem it reports for YOUR slugs (title length, description length, dashes, word count, FAQ count, bad verse reference, links to pages not in the plan). Warnings like "link to missing page" are fine ONLY if that slug is in tools/plan.json (it will be written by another writer). Also run a check that your files contain no characters U+2013 or U+2014.

## Do not
- Edit any file you were not assigned, or tools/build.py, or the CSS/JS.
- Create pages outside your list.

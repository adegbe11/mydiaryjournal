/* My Diary Journal: the diary page, prompts, fill-in templates, printing and the PIN lock.
   Everything is kept in this browser (localStorage). Nothing is sent anywhere. */
(() => {
  const KEY = "mdj.pages", CUR = "mdj.current", PIN = "mdj.pin";
  const store = {
    get(k, d) { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch { return false; } },
  };
  const longDate = ms => new Date(ms).toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" });
  const shortDate = ms => new Date(ms).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
  const icon = {
    plus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 5v14M5 12h14"/></svg>',
    list: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 5h16M4 12h16M4 19h10"/></svg>',
    print: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 9V3h10v6M7 17H4v-7h16v7h-3M7 14h10v7H7z"/></svg>',
    lock: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>',
  };

  /* Printing: copy one page into #print-root so only that page prints. */
  function printEl(el) {
    let root = document.getElementById("print-root");
    if (!root) { root = document.createElement("div"); root.id = "print-root"; document.body.append(root); }
    const copy = el.cloneNode(true);
    const src = el.querySelectorAll("textarea, input");
    copy.querySelectorAll("textarea, input").forEach((f, i) => {
      const v = src[i].value || "";
      const d = document.createElement("div");
      if (f.tagName === "TEXTAREA") { d.className = "print-text"; d.style.minHeight = (f.rows || 6) * 36 + "px"; d.textContent = v; }
      else { d.className = f.className; d.textContent = v || f.placeholder || ""; }
      f.replaceWith(d);
    });
    copy.querySelectorAll(".bar, .pages, .no-print").forEach(n => n.remove());
    root.replaceChildren(copy);
    document.body.classList.add("printing");
    const done = () => { document.body.classList.remove("printing"); root.replaceChildren(); window.removeEventListener("afterprint", done); };
    window.addEventListener("afterprint", done);
    window.print();
    setTimeout(done, 1500);
  }

  /* Diary widget */
  function diary(box) {
    const $ = s => box.querySelector(s);
    const kind = box.dataset.kind || "diary";
    box.querySelector(".bar").innerHTML =
      `<button class="btn primary" data-a="new" type="button">${icon.plus}New page</button>` +
      `<button class="btn" data-a="mine" type="button">${icon.list}<span>My pages</span></button>` +
      `<button class="btn" data-a="print" type="button">${icon.print}Print</button>` +
      `<button class="btn" data-a="lock" type="button">${icon.lock}<span>Lock</span></button>` +
      `<span class="saved">Saved</span>`;
    const title = $(".page-title"), text = $(".lined"), saved = $(".saved"), list = $(".pages"), promptEl = $(".diary-prompt");
    const defaults = { title: title.placeholder, hint: text.placeholder };
    let pages = store.get(KEY, []);
    let cur = box.dataset.restore === "false" ? null : pages.find(p => p.id === store.get(CUR, null)) || null;
    let prompt = "";

    const minH = (parseInt(text.getAttribute("rows"), 10) || 8) * 40;
    function grow() { text.style.height = "auto"; text.style.height = Math.max(text.scrollHeight, minH) + "px"; }
    function show(p) {
      $(".date").textContent = longDate(p ? p.created : Date.now());
      title.value = p ? p.title : ""; text.value = p ? p.text : "";
      setPrompt(p ? p.prompt || "" : "");
      grow();
    }
    function setPrompt(s) { prompt = s; if (promptEl) { promptEl.textContent = s; promptEl.hidden = !s; } }
    let timer;
    function save() {
      pages = store.get(KEY, []);
      if (cur) cur = pages.find(p => p.id === cur.id) || cur;
      if (!cur) {
        if (!title.value.trim() && !text.value.trim()) return;
        cur = { id: Date.now().toString(36), created: Date.now(), kind, title: "", text: "" };
        pages.unshift(cur);
      }
      Object.assign(cur, { title: title.value, text: text.value, prompt, updated: Date.now() });
      const i = pages.findIndex(p => p.id === cur.id); if (i >= 0) pages[i] = cur;
      saved.textContent = store.set(KEY, pages) && store.set(CUR, cur.id) ? "Saved" : "Could not save in this browser";
      renderList();
    }
    const onInput = () => { grow(); saved.textContent = "Saving..."; clearTimeout(timer); timer = setTimeout(save, 400); };
    title.addEventListener("input", onInput); text.addEventListener("input", onInput);

    function renderList() {
      pages = store.get(KEY, []);
      box.querySelector('[data-a="mine"] span').textContent = pages.length ? `My pages (${pages.length})` : "My pages";
      list.replaceChildren();
      if (!pages.length) { const p = document.createElement("p"); p.className = "saved"; p.style.padding = "12px 0"; p.textContent = "Your pages will show here."; list.append(p); return; }
      for (const p of pages) {
        const a = document.createElement("a"); a.href = "#";
        const t = document.createElement("span"); t.className = "hand";
        t.textContent = p.title || p.prompt || (p.text || "").split("\n")[0].slice(0, 50) || "Untitled";
        const d = document.createElement("span"); d.textContent = shortDate(p.created) + "  ";
        const x = document.createElement("button"); x.type = "button"; x.className = "del"; x.textContent = "Delete"; x.setAttribute("aria-label", "Delete this page");
        x.onclick = e => {
          e.preventDefault(); e.stopPropagation();
          if (!confirm("Delete this page? This cannot be undone.")) return;
          pages = store.get(KEY, []).filter(q => q.id !== p.id); store.set(KEY, pages);
          if (cur && cur.id === p.id) { cur = null; store.set(CUR, null); show(null); }
          renderList(); list.classList.add("open");
        };
        d.append(x);
        a.append(t, d);
        a.onclick = e => { e.preventDefault(); cur = p; store.set(CUR, p.id); show(p); list.classList.remove("open"); text.focus(); };
        list.append(a);
      }
    }
    box.addEventListener("click", e => {
      const b = e.target.closest("[data-a]"); if (!b) return;
      const a = b.dataset.a;
      if (a === "new") { cur = null; store.set(CUR, null); title.placeholder = defaults.title; text.placeholder = defaults.hint; show(null); title.focus(); }
      if (a === "mine") list.classList.toggle("open");
      if (a === "print") printEl(box);
      if (a === "lock") store.get(PIN, null) ? openLock(false) : openLock(true);
    });
    box.write = (p, hint) => {
      cur = null; store.set(CUR, null); show(null);
      setPrompt(p || ""); if (hint) text.placeholder = hint;
      box.scrollIntoView({ behavior: "smooth", block: "center" });
      setTimeout(() => text.focus({ preventScroll: true }), 450);
    };
    box.start = (t, hint) => {
      cur = null; store.set(CUR, null); show(null);
      title.value = t || ""; if (hint) text.placeholder = hint;
      box.scrollIntoView({ behavior: "smooth", block: "center" });
      setTimeout(() => text.focus({ preventScroll: true }), 450);
    };
    show(cur); renderList();
  }

  /* Fill-in template sheet */
  function sheet(el) {
    const key = "mdj.tpl." + el.dataset.key;
    const data = store.get(key, {});
    const fields = el.querySelectorAll("[data-f]");
    fields.forEach(f => {
      if (data[f.dataset.f] != null) f.value = data[f.dataset.f];
      const grow = () => { if (f.tagName === "TEXTAREA") { f.style.height = "auto"; f.style.height = f.scrollHeight + "px"; } };
      grow();
      f.addEventListener("input", () => { data[f.dataset.f] = f.value; store.set(key, data); grow(); const s = el.querySelector(".saved"); if (s) s.textContent = "Saved"; });
    });
    el.querySelector('[data-a="print"]')?.addEventListener("click", () => printEl(el));
    el.querySelector('[data-a="clear"]')?.addEventListener("click", () => {
      if (!confirm("Clear this page?")) return;
      fields.forEach(f => { f.value = ""; f.style.height = ""; }); store.set(key, {});
    });
  }

  /* PIN lock: keeps the diary closed on a shared computer. */
  let setting = false;
  function lockEl() {
    let el = document.getElementById("lock");
    if (el) return el;
    el = document.createElement("div"); el.className = "lock"; el.id = "lock"; el.setAttribute("role", "dialog"); el.setAttribute("aria-modal", "true");
    el.innerHTML = '<div class="paper"><div class="tape" style="--c: var(--tape-rose); top:-14px; left:50%; margin-left:-60px; transform: rotate(-2deg)"></div>' +
      '<div class="script" style="font-size:38px">My diary</div>' +
      '<input id="pin" type="password" inputmode="numeric" maxlength="8" autocomplete="off" aria-label="PIN">' +
      '<div><button class="btn primary" id="pinGo" type="button">Open</button></div><p class="saved" id="pinMsg" style="margin:14px 0 0"></p></div>';
    document.body.append(el);
    el.querySelector("#pinGo").onclick = submitPin;
    el.querySelector("#pin").addEventListener("keydown", e => { if (e.key === "Enter") submitPin(); });
    return el;
  }
  async function hash(s) {
    const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode("mdj:" + s));
    return [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, "0")).join("");
  }
  function openLock(isSetting) {
    const el = lockEl(); setting = isSetting;
    el.querySelector("#pin").value = "";
    el.querySelector("#pinMsg").textContent = isSetting ? "Choose a PIN" : "";
    el.querySelector("#pinGo").textContent = isSetting ? "Set PIN" : "Open";
    el.classList.add("show"); setTimeout(() => el.querySelector("#pin").focus(), 50);
  }
  async function submitPin() {
    const el = lockEl(), v = el.querySelector("#pin").value.trim(), msg = el.querySelector("#pinMsg");
    if (v.length < 4) { msg.textContent = "Use at least 4 digits"; return; }
    if (setting) { store.set(PIN, await hash(v)); el.classList.remove("show"); markLocked(); return; }
    if (await hash(v) === store.get(PIN, null)) el.classList.remove("show"); else { msg.textContent = "That PIN is not right"; el.querySelector("#pin").value = ""; }
  }
  function markLocked() { document.querySelectorAll('[data-a="lock"] span').forEach(s => s.textContent = "Locked"); }

  /* Wire up the page */
  const diaries = [...document.querySelectorAll(".diary")];
  diaries.forEach(diary);
  document.querySelectorAll(".sheet[data-key]").forEach(sheet);
  const main = diaries[0];
  if (!main) document.querySelectorAll("[data-prompt]").forEach(b => b.remove());
  document.querySelectorAll("[data-prompt]").forEach(b => b.addEventListener("click", e => {
    if (!main) return; e.preventDefault(); main.write(b.dataset.prompt, b.dataset.hint);
  }));
  document.querySelectorAll("[data-start]").forEach(c => c.addEventListener("click", e => {
    if (!main || e.metaKey || e.ctrlKey) return; e.preventDefault(); main.start(c.dataset.start, c.dataset.hint);
  }));
  const hasPrivate = diaries.length || document.querySelector(".sheet[data-key]");
  if (store.get(PIN, null)) { markLocked(); if (hasPrivate) openLock(false); }
})();

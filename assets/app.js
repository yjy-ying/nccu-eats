// 政大吃什麼 — 首頁篩選功能（原生 JavaScript，不使用任何框架）
(function () {
  const cards = Array.from(document.querySelectorAll("#cards .card"));
  if (!cards.length) return; // 內頁沒有卡片，直接結束

  const state = { category: "", area: "", q: "" };
  const count = document.getElementById("count");
  const empty = document.getElementById("empty");
  const search = document.getElementById("search");

  function apply() {
    let shown = 0;
    cards.forEach((card) => {
      const ok =
        (!state.category || card.dataset.category === state.category) &&
        (!state.area || card.dataset.area === state.area) &&
        (!state.q || card.dataset.search.includes(state.q));
      card.hidden = !ok;
      if (ok) shown++;
    });
    count.textContent = `顯示 ${shown} / ${cards.length} 間店`;
    empty.hidden = shown !== 0;
  }

  document.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const key = chip.dataset.filter;
      state[key] = chip.dataset.value;
      document
        .querySelectorAll(`.chip[data-filter="${key}"]`)
        .forEach((c) => c.classList.toggle("is-active", c === chip));
      apply();
    });
  });

  search.addEventListener("input", () => {
    state.q = search.value.trim().toLowerCase();
    apply();
  });

  apply();
})();

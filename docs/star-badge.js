fetch('https://api.github.com/repos/PominausGH/voxtty')
  .then(function (r) { return r.ok ? r.json() : null; })
  .then(function (data) {
    if (!data || typeof data.stargazers_count !== 'number') return;
    document.querySelectorAll('[data-star-count]').forEach(function (el) {
      el.textContent = data.stargazers_count;
    });
    document.querySelectorAll('[data-star-badge]').forEach(function (el) {
      el.hidden = false;
    });
  })
  .catch(function () {});

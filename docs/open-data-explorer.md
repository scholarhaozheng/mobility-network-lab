# City evidence explorer

Search the complete 11,422-row accepted city frame. The page uses an embedded,
non-geometric index, so it works when opened directly with `file://`; it does
not fetch a local file, call an API or test current provider availability.

<div class="actions">
  <a class="button primary" href="data/open-mobility/city_evidence.csv" download>Download data</a>
  <a class="button" href="data/open-mobility/city_evidence_schema.json">Data dictionary</a>
  <a class="button" href="open-data-sources.md">Sources</a>
</div>

For reproducible analysis, use the CSV/JSON files rather than scraping this
page. The [content–city table](data/open-mobility/content_city.csv) preserves
all accepted content links; the [source–content–city table](data/open-mobility/source_content_city.csv)
also preserves source records without an accepted city link.

<div class="explorer-controls">
  <input id="city-search" type="search" placeholder="City name or full city ID" aria-label="City name or city ID">
  <input id="country-search" type="search" placeholder="ISO2 / ISO3 (optional)" aria-label="Country code">
  <button id="city-search-button" type="button">Search</button>
</div>
<p class="explorer-status" id="city-search-status">Examples: Hong Kong · Melbourne · Cairo · Paris. Results are capped at 100 rows.</p>
<div class="tablewrap">
<table class="explorer-table">
  <thead><tr><th>City</th><th>Country</th><th>Stable ID</th><th>Strict catalog</th><th>GTFS stop evidence</th><th>Content hashes</th><th>Realtime snapshot class</th></tr></thead>
  <tbody id="city-search-results"></tbody>
</table>
</div>

<script type="application/json" id="mcl-city-index">__MCL_CITY_INDEX__</script>
<script>
(function () {
  "use strict";
  const rows = JSON.parse(document.getElementById("mcl-city-index").textContent);
  const text = document.getElementById("city-search");
  const country = document.getElementById("country-search");
  const body = document.getElementById("city-search-results");
  const status = document.getElementById("city-search-status");
  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, function (char) {
      return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[char];
    });
  }
  function render() {
    const query = text.value.trim().toLocaleLowerCase();
    const code = country.value.trim().toLocaleLowerCase();
    const matches = rows.filter(function (row) {
      const keyMatch = !query || row.name.toLocaleLowerCase().includes(query) || row.id.toLocaleLowerCase() === query;
      const countryMatch = !code || row.iso2.toLocaleLowerCase() === code || row.iso3.toLocaleLowerCase() === code;
      return keyMatch && countryMatch;
    });
    const shown = matches.slice(0, 100);
    body.innerHTML = shown.map(function (row) {
      return "<tr><td>" + escapeHtml(row.name) + "</td><td>" + escapeHtml(row.iso3) +
        "</td><td><code>" + escapeHtml(row.id) + "</code></td><td class=\"state-" + escapeHtml(row.catalog) + "\">" + escapeHtml(row.catalog) +
        "</td><td class=\"state-" + escapeHtml(row.gtfs) + "\">" + escapeHtml(row.gtfs) +
        "</td><td>" + escapeHtml(row.hashes) + "</td><td>" + escapeHtml(row.realtime) + "</td></tr>";
    }).join("");
    status.textContent = matches.length + " matching row(s)" + (matches.length > shown.length ? "; first 100 shown." : ".");
  }
  document.getElementById("city-search-button").addEventListener("click", render);
  text.addEventListener("keydown", function (event) { if (event.key === "Enter") render(); });
  country.addEventListener("keydown", function (event) { if (event.key === "Enter") render(); });
  text.value = "Hong Kong";
  country.value = "CHN";
  render();
}());
</script>

## Interpretation

- `no` means no evidence in that checked historical layer/view; it does not
  mean that the city has no transit or no currently available data.
- Network snapshot and all-retained values are different analytical views and
  must not be added.
- Realtime classes describe the accepted bounded snapshot, not live endpoint
  health.
- City names are not keys. Use the stable city ID in scripts. For example,
  `Lawrence, USA` has three city IDs and is deliberately treated as ambiguous
  by the command-line query unless `--all-matches` is supplied.

See [data tools](data-tools.md) for exact-ID queries and relationship output.

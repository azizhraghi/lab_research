# Public scientific integrations — 12 September 2026

## Verified live example

The public ORCID API returned Geoffrey Bilder's name and 239 work groups.
Identity was cross-checked against [Crossref's profile](https://www.crossref.org/people/geoffrey-bilder),
which supplies ORCID `0000-0003-1315-5960`. This is an external public-source
example, not a laboratory member, endorsed CV or field-validation result.

The application parser fetched these works. A temporary migrated SQLite database
then exercised the real import endpoint with that live response: 239 publication
rows and 239 researcher links were created. Replaying the same fetched response
created zero rows and zero links. This verifies repeat-import idempotency for
this example, not fuzzy author identification or completeness of the public record.
Distinct DOIs may have the same title and are retained; count does not mean 239
peer-reviewed journal articles.

The actual CV endpoint returned application/pdf. The final 12-page PDF was
rendered for visual review. This exposed and resolved overlapping name/ORCID
text and publication metadata split across pages. No citation counts or h-index
were supplied by ORCID, so those metrics remain N/A rather than fabricated values.

PubMed's existing metadata fetcher successfully returned one result for
`water quality monitoring`: [PMID 42727435](https://pubmed.ncbi.nlm.nih.gov/42727435/),
with title, authors and DOI `10.1016/j.marpolbul.2026.120320`. It supplies metadata,
not abstracts. This verifies the fetcher, not the complete LLM-enriched watch run.

arXiv returned HTTP 429 during initial probes and a ReadTimeout in the final
script run. It remains unavailable in this verification; no success is claimed.

## Changes

- Normalize surrounding DOI whitespace before removing DOI URL prefixes, and
  normalize at the publication upsert boundary to prevent duplicate insertions.
- Escape researcher/publication text before passing it to ReportLab markup.
- Preserve a recorded zero metric as zero and missing values as N/A.
- Correct CV heading spacing and keep each publication entry together.
- Use HTTPS for arXiv and include exception type in its failure message.
- Skip LLM summary generation when no abstract is supplied; display a clear
  summary-unavailable notice instead. With an abstract, the prompt explicitly
  confines the summary to that evidence.

## Reproduce

Run `.\.venv\Scripts\python.exe scripts/verify_public_integrations.py` to perform
an opt-in network check. It fetches public ORCID data, attempts one arXiv search,
uses a temporary database, tests import/reimport and the PDF endpoint, and writes
local evidence to ignored `tmp/integration-evidence/`. It does not touch the lab
DB or publish the example on the public portal. Live availability can change;
the script is intentionally separate from offline CI.

The dated evidence JSON records the captured outcomes, including the separate
PubMed check. PDF rendering used the bundled pypdf/pypdfium2 runtime. Offline
regressions cover DOI variants/reimport, PDF response generation with literal
markup characters, and the no-abstract summary behavior, in addition to the
existing workflow suite.

## Still outstanding

Actual lab researcher identity confirmation, Scholar/Scopus metric accuracy,
Mistral tagging/embedding/summary quality and a complete live digest delivery
remain unverified. ORCID identifier linkage alone is not proof that an arbitrary
user-entered name owns that identifier. Confirm identity before operational use.
The metadata-only PubMed path requires abstract retrieval before meaningful
scientific summaries can be generated.

Relevant primary documentation: [ORCID read tutorial](https://info.orcid.org/documentation/api-tutorials/api-tutorial-read-data-on-a-record/),
[arXiv API manual](https://github.com/arXiv/arxiv-docs/blob/develop/source/help/api/user-manual.md),
and [NCBI E-utilities reference](https://www.ncbi.nlm.nih.gov/books/NBK25499/).

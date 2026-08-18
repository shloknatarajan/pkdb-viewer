"""Thin NCBI E-utilities client (stdlib only). No LLM calls."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Iterable

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
DEFAULT_TOOL = "pkdb-paper-screening"
DEFAULT_SLEEP = 0.34  # ~3 req/s without an API key


@dataclass
class NcbiClient:
    email: str | None = None
    api_key: str | None = None
    tool: str = DEFAULT_TOOL
    sleep: float = DEFAULT_SLEEP

    def __post_init__(self) -> None:
        if not self.email:
            self.email = os.environ.get("NCBI_EMAIL") or os.environ.get("EMAIL") or "shlok@gxl.ai"
        if not self.api_key:
            self.api_key = os.environ.get("NCBI_API_KEY")
        if self.api_key and self.sleep == DEFAULT_SLEEP:
            self.sleep = 0.11  # ~10 req/s with a key

    def _params(self, **extra: object) -> dict[str, object]:
        p: dict[str, object] = {"tool": self.tool, "email": self.email, **extra}
        if self.api_key:
            p["api_key"] = self.api_key
        return p

    def _get(self, path: str, **params: object) -> bytes:
        q = urllib.parse.urlencode({k: v for k, v in self._params(**params).items() if v is not None})
        url = f"{EUTILS}/{path}?{q}"
        return self._request(url)

    def _post(self, path: str, **params: object) -> bytes:
        data = urllib.parse.urlencode(
            {k: str(v) for k, v in self._params(**params).items() if v is not None}
        ).encode()
        url = f"{EUTILS}/{path}"
        return self._request(url, data=data)

    def _request(self, url: str, data: bytes | None = None) -> bytes:
        last: Exception | None = None
        for attempt in range(5):
            try:
                req = urllib.request.Request(url, data=data)
                with urllib.request.urlopen(req, timeout=90) as r:
                    body = r.read()
                time.sleep(self.sleep)
                return body
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
                last = e
                time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"NCBI request failed: {url[:120]}") from last

    def esearch_count(self, term: str, *, db: str = "pmc") -> int:
        raw = self._post("esearch.fcgi", db=db, term=term, retmax=0, retmode="json")
        return int(json.loads(raw)["esearchresult"]["count"])

    def esearch_ids(
        self,
        term: str,
        *,
        db: str = "pmc",
        retmax: int = 200,
        retstart: int = 0,
        sort: str = "relevance",
    ) -> tuple[list[str], int]:
        """Return (id_list, total_count). POST so long terms don't overflow GET."""
        raw = self._post(
            "esearch.fcgi",
            db=db,
            term=term,
            retmax=retmax,
            retstart=retstart,
            sort=sort,
            retmode="json",
        )
        payload = json.loads(raw)["esearchresult"]
        return list(payload.get("idlist") or []), int(payload["count"])

    def esummary_pmc(self, pmc_uids: Iterable[str]) -> list[dict]:
        """Summaries for PMC UIDs: pmid, pmcid, title, journal, year (no abstract)."""
        uids = list(pmc_uids)
        rows: list[dict] = []
        for i in range(0, len(uids), 40):
            chunk = uids[i : i + 40]
            payload = json.loads(
                self._post("esummary.fcgi", db="pmc", id=",".join(chunk), retmode="json")
            )
            result = payload.get("result") or {}
            for uid in chunk:
                rec = result.get(uid) or {}
                if not rec or rec.get("error"):
                    continue
                pmid = ""
                pmcid = f"PMC{uid}" if not str(uid).upper().startswith("PMC") else str(uid).upper()
                for aid in rec.get("articleids") or []:
                    if aid.get("idtype") == "pmid":
                        pmid = str(aid.get("value") or "")
                    elif aid.get("idtype") == "pmcid":
                        pmcid = str(aid.get("value") or pmcid)
                pubdate = rec.get("pubdate") or rec.get("epubdate") or ""
                rows.append(
                    {
                        "pmc_uid": uid,
                        "pmid": pmid,
                        "pmcid": pmcid,
                        "title": (rec.get("title") or "").strip(),
                        "journal": (rec.get("fulljournalname") or rec.get("source") or "").strip(),
                        "year": pubdate[:4] if pubdate else "",
                    }
                )
        return rows

    def efetch_pubmed_abstracts(self, pmids: Iterable[str]) -> dict[str, str]:
        """Map PMID -> abstract text."""
        ids = [p for p in pmids if p]
        out: dict[str, str] = {}
        for i in range(0, len(ids), 40):
            chunk = ids[i : i + 40]
            root = ET.fromstring(
                self._post(
                    "efetch.fcgi",
                    db="pubmed",
                    rettype="abstract",
                    retmode="xml",
                    id=",".join(chunk),
                )
            )
            for art in root.findall(".//PubmedArticle"):
                pmid = art.findtext(".//PMID") or ""
                abstract = " ".join(
                    "".join(a.itertext()) for a in art.findall(".//Abstract/AbstractText")
                ).strip()
                if pmid:
                    out[pmid] = abstract
        return out

    def fetch_pmc_records(self, pmc_uids: Iterable[str]) -> list[dict]:
        """Full candidate records: PMC summary + PubMed abstract."""
        summaries = self.esummary_pmc(pmc_uids)
        abstracts = self.efetch_pubmed_abstracts(s["pmid"] for s in summaries)
        for rec in summaries:
            rec["abstract"] = abstracts.get(rec.get("pmid") or "", "")
        return summaries
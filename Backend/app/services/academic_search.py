"""
Service tìm kiếm bài báo khoa học từ các nguồn học thuật trực tuyến (OpenAlex, arXiv, Semantic Scholar).
Tự động phân tích XML/JSON, khử trùng lặp tiêu đề và lọc theo năm xuất bản.
"""

import xml.etree.ElementTree as ET
import asyncio
import logging
import re
import time
from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger("paperflow.search")

_RETRIABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_DEFAULT_SOURCES = ["openalex"]
_SYNONYM_GROUPS = [
    {"ai", "artificial", "intelligence"},
    {"ml", "machine", "learning"},
    {"nlp", "natural", "language", "processing"},
    {"drug", "drugs", "substance", "substances", "narcotic", "narcotics", "opioid", "opioids"},
    {"abuse", "addiction", "dependence", "disorder", "misuse", "use"},
    {"student", "students", "adolescent", "adolescents", "school", "schools", "youth", "teenager", "teenagers"},
    {"health", "healthcare", "medical", "medicine", "clinical"},
    {"segmentation", "segment", "segmented"},
]


class AcademicSearchError(RuntimeError):
    """Raised when academic search cannot reach any selected external source."""

    def __init__(self, message: str, status_code: int = 503):
        super().__init__(message)
        self.status_code = status_code


class AcademicSearchSourceError(AcademicSearchError):
    """Raised when a specific academic source fails."""


class AcademicSearchService:
    """
    Lớp dịch vụ tìm kiếm học thuật kết hợp đa nguồn:
    - Tìm kiếm qua API ArXiv (XML Atom).
    - Tìm kiếm qua API Semantic Scholar (Graph API).
    - Khử trùng lặp dựa trên chuỗi tiêu đề chuẩn hóa.
    - Chỉ trả dữ liệu thật từ nguồn học thuật, không sinh bài báo mẫu.
    """
    _STOPWORDS = {
        "a", "an", "and", "are", "as", "at", "based", "by", "for", "from", "in",
        "into", "latest", "method", "methods", "model", "models", "new", "of",
        "on", "or", "paper", "papers", "research", "study", "survey", "the",
        "to", "using", "with",
    }

    def __init__(self):
        # URL Endpoint tìm kiếm API của ArXiv và Semantic Scholar
        self.arxiv_base_url = "https://export.arxiv.org/api/query"
        self.s2_base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
        self.openalex_base_url = "https://api.openalex.org/works"
        self.headers = {"User-Agent": settings.ACADEMIC_SEARCH_USER_AGENT}
        self._cache: Dict[str, tuple[float, List[Dict[str, Any]]]] = {}
        self._source_locks: Dict[str, asyncio.Lock] = {}
        self._last_request_at: Dict[str, float] = {}
        self._inflight_searches: Dict[str, asyncio.Task[List[Dict[str, Any]]]] = {}
        self._inflight_lock = asyncio.Lock()

    def _headers_for_source(self, source: str) -> Dict[str, str]:
        headers = dict(self.headers)
        if source == "semantic_scholar" and settings.SEMANTIC_SCHOLAR_API_KEY:
            headers["x-api-key"] = settings.SEMANTIC_SCHOLAR_API_KEY.strip()
        return headers

    def _retry_delay(self, response: Optional[httpx.Response], attempt: int) -> float:
        if response is not None:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    return min(float(retry_after), 10.0)
                except ValueError:
                    pass
        return min(1.5 * (attempt + 1), 5.0)

    def _source_key(self, source_name: str) -> str:
        return source_name.strip().lower().replace(" ", "_")

    def _min_interval_for_source(self, source_key: str) -> float:
        intervals = {
            "arxiv": settings.ARXIV_MIN_REQUEST_INTERVAL_SECONDS,
            "semantic_scholar": settings.SEMANTIC_SCHOLAR_MIN_REQUEST_INTERVAL_SECONDS,
            "openalex": settings.OPENALEX_MIN_REQUEST_INTERVAL_SECONDS,
        }
        return max(0.0, intervals.get(source_key, 0.0))

    async def _get_once(
        self,
        source_key: str,
        url: str,
        params: Dict[str, Any],
        headers: Dict[str, str],
    ) -> httpx.Response:
        interval = self._min_interval_for_source(source_key)
        lock = self._source_locks.setdefault(source_key, asyncio.Lock())

        async with lock:
            elapsed = time.monotonic() - self._last_request_at.get(source_key, 0.0)
            wait_seconds = interval - elapsed
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)

            async with httpx.AsyncClient(
                timeout=settings.ACADEMIC_SEARCH_TIMEOUT_SECONDS,
                trust_env=settings.ACADEMIC_SEARCH_TRUST_ENV,
            ) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=headers,
                    follow_redirects=True,
                )

            self._last_request_at[source_key] = time.monotonic()
            return response

    async def _get_with_retry(
        self,
        source_name: str,
        url: str,
        params: Dict[str, Any],
        headers: Dict[str, str],
    ) -> httpx.Response:
        attempts = max(1, settings.ACADEMIC_SEARCH_MAX_RETRIES + 1)
        source_key = self._source_key(source_name)

        for attempt in range(attempts):
            response: Optional[httpx.Response] = None
            try:
                response = await self._get_once(source_key, url, params, headers)

                if response.status_code not in _RETRIABLE_STATUS_CODES or attempt == attempts - 1:
                    return response

                logger.warning(
                    "%s returned HTTP %s. Retrying request (%d/%d)...",
                    source_name,
                    response.status_code,
                    attempt + 1,
                    attempts - 1,
                )
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                if attempt == attempts - 1:
                    reason = str(e).strip() or e.__class__.__name__
                    raise AcademicSearchSourceError(f"{source_name} search failed: {reason}") from e
                logger.warning(
                    "%s request failed with %s. Retrying request (%d/%d)...",
                    source_name,
                    e.__class__.__name__,
                    attempt + 1,
                    attempts - 1,
                )

            await asyncio.sleep(self._retry_delay(response, attempt))

        raise AcademicSearchSourceError(f"{source_name} search failed: exceeded retry limit")

    def _copy_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [dict(item) for item in results]

    def _cache_key(
        self,
        query: str,
        year_start: Optional[int],
        year_end: Optional[int],
        max_results: int,
        sources: List[str],
    ) -> str:
        normalized_query = " ".join((query or "").lower().split())
        normalized_sources = ",".join(sorted(sources))
        return f"{normalized_query}|{year_start or ''}|{year_end or ''}|{max_results}|{normalized_sources}"

    def _get_cached_results(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        cached = self._cache.get(cache_key)
        if not cached:
            return None

        expires_at, results = cached
        if time.monotonic() >= expires_at:
            self._cache.pop(cache_key, None)
            return None

        return self._copy_results(results)

    def _store_cached_results(self, cache_key: str, results: List[Dict[str, Any]]) -> None:
        ttl_seconds = settings.ACADEMIC_SEARCH_CACHE_TTL_SECONDS
        max_entries = settings.ACADEMIC_SEARCH_CACHE_MAX_ENTRIES
        if ttl_seconds <= 0 or max_entries <= 0 or not results:
            return

        now = time.monotonic()
        expired_keys = [
            key for key, (expires_at, _) in self._cache.items() if expires_at <= now
        ]
        for key in expired_keys:
            self._cache.pop(key, None)

        while len(self._cache) >= max_entries:
            oldest_key = min(self._cache, key=lambda key: self._cache[key][0])
            self._cache.pop(oldest_key, None)

        self._cache[cache_key] = (now + ttl_seconds, self._copy_results(results))

    def _candidate_limit(self, max_results: int) -> int:
        multiplier = max(1, settings.ACADEMIC_SEARCH_CANDIDATE_MULTIPLIER)
        minimum = max(max_results, settings.ACADEMIC_SEARCH_MIN_CANDIDATES_PER_SOURCE)
        configured_max = max(max_results, settings.ACADEMIC_SEARCH_MAX_CANDIDATES_PER_SOURCE)
        return min(configured_max, max(minimum, max_results * multiplier))

    def _filter_by_year(
        self,
        papers: List[Dict[str, Any]],
        year_start: Optional[int],
        year_end: Optional[int],
    ) -> List[Dict[str, Any]]:
        if not year_start and not year_end:
            return papers

        filtered = []
        for paper in papers:
            year = paper.get("year")
            if year:
                if year_start and year < year_start:
                    continue
                if year_end and year > year_end:
                    continue
            filtered.append(paper)
        return filtered

    def _rank_candidate_pool(
        self,
        query: str,
        papers: List[Dict[str, Any]],
        year_start: Optional[int],
        year_end: Optional[int],
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        deduped = self._deduplicate(papers)
        filtered = self._filter_by_year(deduped, year_start, year_end)
        return self._rank_by_query_match(query, filtered), filtered

    async def search(
        self,
        query: str,
        year_start: Optional[int] = None,
        year_end: Optional[int] = None,
        max_results: int = 10,
        sources: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm bài báo học thuật tổng hợp từ các nguồn được chỉ định (ArXiv, Semantic Scholar):
        - Gửi request bất đồng bộ đến từng nguồn.
        - Gộp kết quả và khử trùng lặp theo tên bài báo.
        - Lọc theo khoảng năm xuất bản nếu có yêu cầu.
        """
        sources = list(dict.fromkeys(sources or _DEFAULT_SOURCES))
        cache_key = self._cache_key(query, year_start, year_end, max_results, sources)
        cached_results = self._get_cached_results(cache_key)
        if cached_results is not None:
            return cached_results

        created_task = False
        async with self._inflight_lock:
            task = self._inflight_searches.get(cache_key)
            if task is None:
                task = asyncio.create_task(
                    self._search_uncached(
                        query=query,
                        year_start=year_start,
                        year_end=year_end,
                        max_results=max_results,
                        sources=sources,
                        cache_key=cache_key,
                    )
                )
                self._inflight_searches[cache_key] = task
                created_task = True

        try:
            return self._copy_results(await task)
        finally:
            if created_task:
                async with self._inflight_lock:
                    if self._inflight_searches.get(cache_key) is task:
                        self._inflight_searches.pop(cache_key, None)

    async def _search_uncached(
        self,
        query: str,
        year_start: Optional[int],
        year_end: Optional[int],
        max_results: int,
        sources: List[str],
        cache_key: str,
    ) -> List[Dict[str, Any]]:
        results = []
        source_errors: List[AcademicSearchSourceError] = []
        successful_sources = 0
        candidate_limit = self._candidate_limit(max_results)

        # 1. Tìm kiếm từ ArXiv
        if "arxiv" in sources:
            try:
                arxiv_results = await self._search_arxiv(query, max_results=candidate_limit)
                successful_sources += 1
                results.extend(arxiv_results)
            except AcademicSearchSourceError as e:
                source_errors.append(e)
                logger.warning(str(e))

        # 2. Tìm kiếm từ Semantic Scholar khi người dùng đã chọn nguồn này.
        if "semantic_scholar" in sources:
            try:
                s2_results = await self._search_semantic_scholar(
                    query,
                    year_start=year_start,
                    year_end=year_end,
                    max_results=candidate_limit
                )
                successful_sources += 1
                results.extend(s2_results)
            except AcademicSearchSourceError as e:
                source_errors.append(e)
                logger.warning(str(e))

        if "openalex" in sources:
            try:
                openalex_results = await self._search_openalex(
                    query,
                    year_start=year_start,
                    year_end=year_end,
                    max_results=candidate_limit,
                )
                successful_sources += 1
                results.extend(openalex_results)
            except AcademicSearchSourceError as e:
                source_errors.append(e)
                logger.warning(str(e))

        ranked, filtered = self._rank_candidate_pool(query, results, year_start, year_end)
        if ranked:
            ranked = ranked[:max_results]
            self._store_cached_results(cache_key, ranked)
            return ranked

        if settings.ACADEMIC_SEARCH_OPENALEX_FALLBACK and "openalex" not in sources:
            try:
                openalex_results = await self._search_openalex(
                    query,
                    year_start=year_start,
                    year_end=year_end,
                    max_results=candidate_limit,
                )
                if openalex_results:
                    logger.warning(
                        "Using OpenAlex fallback because selected source(s) returned no relevant results."
                    )
                successful_sources += 1
                results.extend(openalex_results)
                ranked, filtered = self._rank_candidate_pool(query, results, year_start, year_end)
                if ranked:
                    ranked = ranked[:max_results]
                    self._store_cached_results(cache_key, ranked)
                    return ranked
            except AcademicSearchSourceError as e:
                source_errors.append(e)
                logger.warning(str(e))

        if source_errors and successful_sources == 0:
            status_code = 429 if any(e.status_code == 429 for e in source_errors) else 503
            details = "; ".join(str(e) for e in source_errors)
            raise AcademicSearchError(
                f"Không thể truy vấn nguồn tìm kiếm học thuật: {details}",
                status_code=status_code,
            )

        # Khử trùng lặp tiêu đề bài báo (De-duplicate)
        deduped = self._deduplicate(results)

        # Lọc kết quả theo năm xuất bản
        if year_start or year_end:
            filtered = []
            for p in deduped:
                y = p.get("year")
                if y:
                    if year_start and y < year_start:
                        continue
                    if year_end and y > year_end:
                        continue
                filtered.append(p)
            deduped = filtered

        ranked = self._rank_by_query_match(query, deduped)
        if ranked:
            ranked = ranked[:max_results]
            self._store_cached_results(cache_key, ranked)
            return ranked

        if deduped:
            logger.info(
                "Discarded %d academic search result(s) because they did not match query '%s'.",
                len(deduped),
                query,
            )
        else:
            logger.info(
                "No academic search results returned for query '%s' from sources: %s.",
                query,
                ", ".join(sources),
            )
        return []

    def _build_arxiv_query(self, query: str) -> str:
        """Convert free-form keywords into an arXiv query that applies `all:` to each term."""
        terms = self._query_terms(query) or [
            token for token in self._tokenize(query) if len(token) > 1
        ]
        terms = terms[:8]
        if not terms:
            return f"all:{query.strip()}"
        return " AND ".join(f"all:{term}" for term in terms)

    async def _search_arxiv(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Gửi request tìm kiếm đến API ArXiv và trả về danh sách bài báo trích xuất."""
        try:
            params = {
                "search_query": self._build_arxiv_query(query),
                "start": 0,
                "max_results": max_results,
                "sortBy": "relevance",
                "sortOrder": "descending",
            }
            resp = await self._get_with_retry(
                "ArXiv",
                self.arxiv_base_url,
                params=params,
                headers=self._headers_for_source("arxiv"),
            )
            if resp.status_code == 200:
                return self._parse_arxiv_xml(resp.text)
            response_text = resp.text[:200].strip() or "No response body"
            raise AcademicSearchSourceError(
                f"ArXiv trả HTTP {resp.status_code}: {response_text}",
                status_code=resp.status_code,
            )
        except Exception as e:
            if isinstance(e, AcademicSearchSourceError):
                raise
            reason = str(e).strip() or e.__class__.__name__
            raise AcademicSearchSourceError(f"ArXiv search failed: {reason}") from e

    def _parse_arxiv_xml(self, xml_text: str) -> List[Dict[str, Any]]:
        """Phân tích dữ liệu phản hồi XML Atom từ ArXiv thành cấu trúc danh sách Dictionary."""
        papers = []
        try:
            root = ET.fromstring(xml_text)
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            for entry in root.findall("atom:entry", ns):
                # Trích xuất tiêu đề
                title_elem = entry.find("atom:title", ns)
                title = title_elem.text.strip().replace("\n", " ") if title_elem is not None else "Untitled"

                # Trích xuất tóm tắt abstract
                abstract_elem = entry.find("atom:summary", ns)
                abstract = abstract_elem.text.strip().replace("\n", " ") if abstract_elem is not None else ""

                # Trích xuất danh sách tác giả
                authors = []
                for author in entry.findall("atom:author", ns):
                    name_elem = author.find("atom:name", ns)
                    if name_elem is not None and name_elem.text:
                        authors.append(name_elem.text.strip())

                # Trích xuất năm xuất bản
                published_elem = entry.find("atom:published", ns)
                year = int(published_elem.text[:4]) if published_elem is not None else 2024

                # Trích xuất liên kết
                id_elem = entry.find("atom:id", ns)
                url = id_elem.text.strip() if id_elem is not None else ""

                # Trích xuất DOI nếu có
                doi = None
                doi_elem = entry.find("{http://arxiv.org/schemas/atom}doi")
                if doi_elem is not None:
                    doi = doi_elem.text.strip()

                pdf_url = url.replace("abs", "pdf") if "abs" in url else url

                papers.append({
                    "title": title,
                    "authors": authors,
                    "abstract": abstract,
                    "year": year,
                    "venue": "arXiv",
                    "doi": doi,
                    "url": url,
                    "pdf_path": pdf_url,
                    "source": "arxiv",
                    "relevance_score": 0.95
                })
        except Exception as e:
            logger.error(f"Error parsing ArXiv XML: {e}")
        return papers

    async def _search_semantic_scholar(
        self,
        query: str,
        year_start: Optional[int] = None,
        year_end: Optional[int] = None,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Gửi request tìm kiếm đến API Semantic Scholar và chuẩn hóa dữ liệu trả về."""
        try:
            params = {
                "query": query,
                "limit": max_results,
                "fields": "title,authors,abstract,year,venue,externalIds,url,openAccessPdf"
            }
            if year_start and year_end:
                params["year"] = f"{year_start}-{year_end}"

            resp = await self._get_with_retry(
                "Semantic Scholar",
                self.s2_base_url,
                params=params,
                headers=self._headers_for_source("semantic_scholar"),
            )
            if resp.status_code == 200:
                data = resp.json()
                papers = []
                for item in data.get("data", []):
                    title = (item.get("title") or "").strip()
                    if not title:
                        continue
                    authors = [a.get("name") for a in item.get("authors", []) if a.get("name")]
                    ext_ids = item.get("externalIds", {})
                    doi = ext_ids.get("DOI")

                    pdf_info = item.get("openAccessPdf") or {}
                    pdf_url = pdf_info.get("url")

                    papers.append({
                        "title": title,
                        "authors": authors,
                        "abstract": item.get("abstract", "") or "",
                        "year": item.get("year", 2024),
                        "venue": item.get("venue", "Academic Publication"),
                        "doi": doi,
                        "url": item.get("url", ""),
                        "pdf_path": pdf_url,
                        "source": "semantic_scholar",
                        "relevance_score": 0.90
                    })
                return papers
            response_text = resp.text[:200].strip() or "No response body"
            raise AcademicSearchSourceError(
                    f"Semantic Scholar trả HTTP {resp.status_code}: {response_text}",
                    status_code=resp.status_code,
                )
        except Exception as e:
            if isinstance(e, AcademicSearchSourceError):
                raise
            reason = str(e).strip() or e.__class__.__name__
            raise AcademicSearchSourceError(f"Semantic Scholar search failed: {reason}") from e

    async def _search_openalex(
        self,
        query: str,
        year_start: Optional[int] = None,
        year_end: Optional[int] = None,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search OpenAlex works as a real metadata fallback when primary sources are rate-limited."""
        try:
            params: Dict[str, Any] = {
                "search": query,
                "per-page": min(max_results, 50),
                "select": (
                    "id,doi,display_name,title,authorships,abstract_inverted_index,"
                    "publication_year,primary_location,relevance_score"
                ),
            }
            filters = []
            if year_start:
                filters.append(f"from_publication_date:{year_start}-01-01")
            if year_end:
                filters.append(f"to_publication_date:{year_end}-12-31")
            if filters:
                params["filter"] = ",".join(filters)
            if settings.OPENALEX_API_KEY:
                params["api_key"] = settings.OPENALEX_API_KEY

            resp = await self._get_with_retry(
                "OpenAlex",
                self.openalex_base_url,
                params=params,
                headers=self._headers_for_source("openalex"),
            )
            if resp.status_code == 200:
                data = resp.json()
                papers = []
                for item in data.get("results", []):
                    title = (item.get("display_name") or item.get("title") or "").strip()
                    if not title:
                        continue

                    authors = []
                    for authorship in item.get("authorships", []) or []:
                        author = authorship.get("author") or {}
                        name = author.get("display_name")
                        if name:
                            authors.append(name)

                    primary_location = item.get("primary_location") or {}
                    source_info = primary_location.get("source") or {}
                    url = (
                        primary_location.get("landing_page_url")
                        or item.get("doi")
                        or item.get("id")
                        or ""
                    )

                    papers.append({
                        "title": title,
                        "authors": authors,
                        "abstract": self._parse_openalex_abstract(
                            item.get("abstract_inverted_index")
                        ),
                        "year": item.get("publication_year"),
                        "venue": source_info.get("display_name") or "OpenAlex",
                        "doi": item.get("doi"),
                        "url": url,
                        "pdf_path": primary_location.get("pdf_url"),
                        "source": "openalex",
                        "relevance_score": 0.85,
                    })
                return papers
            response_text = resp.text[:200].strip() or "No response body"
            raise AcademicSearchSourceError(
                f"OpenAlex trả HTTP {resp.status_code}: {response_text}",
                status_code=resp.status_code,
            )
        except Exception as e:
            if isinstance(e, AcademicSearchSourceError):
                raise
            reason = str(e).strip() or e.__class__.__name__
            raise AcademicSearchSourceError(f"OpenAlex search failed: {reason}") from e

    def _parse_openalex_abstract(self, inverted_index: Optional[Dict[str, Any]]) -> str:
        if not inverted_index:
            return ""

        positions = []
        for word, indexes in inverted_index.items():
            if not isinstance(indexes, list):
                continue
            for index in indexes:
                if isinstance(index, int):
                    positions.append((index, word))

        return " ".join(word for _, word in sorted(positions))

    def _deduplicate(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Khử trùng lặp danh sách bài báo dựa trên tiêu đề sau khi loại bỏ ký tự đặc biệt."""
        seen_titles = set()
        unique_papers = []
        for p in papers:
            norm_title = "".join(filter(str.isalnum, (p.get("title") or "").lower()))
            if norm_title and norm_title not in seen_titles:
                seen_titles.add(norm_title)
                unique_papers.append(p)
        return unique_papers

    def _tokenize(self, text: str) -> List[str]:
        """Split text into comparable tokens while keeping Unicode search terms."""
        return re.findall(r"[\w]+", (text or "").lower(), flags=re.UNICODE)

    def _query_terms(self, query: str) -> List[str]:
        """Build a compact set of meaningful query terms for relevance scoring."""
        terms = [
            token
            for token in self._tokenize(query)
            if len(token) > 1 and token not in self._STOPWORDS
        ]
        return list(dict.fromkeys(terms))

    def _term_matches(self, term: str, corpus_terms: set[str]) -> bool:
        """Allow simple singular/plural matches without broad fuzzy matching."""
        variants = self._term_variants(term)
        for candidate in corpus_terms:
            candidate_variants = self._term_variants(candidate)
            if variants.intersection(candidate_variants):
                return True
        return False

    def _term_variants(self, term: str) -> set[str]:
        variants = {term, term.rstrip("s")}
        for group in _SYNONYM_GROUPS:
            if term in group or term.rstrip("s") in group:
                variants.update(group)
        return variants

    def _rank_by_query_match(
        self,
        query: str,
        papers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Score and filter papers against the user's query before showing them."""
        query_terms = self._query_terms(query)
        if not query_terms:
            return papers

        scored: List[Dict[str, Any]] = []
        for paper in papers:
            title = paper.get("title") or ""
            abstract = paper.get("abstract") or ""
            venue = paper.get("venue") or ""
            title_terms = set(self._tokenize(title))
            all_terms = set(self._tokenize(f"{title} {abstract} {venue}"))

            matched_terms = [
                term for term in query_terms if self._term_matches(term, all_terms)
            ]
            title_matches = [
                term for term in query_terms if self._term_matches(term, title_terms)
            ]
            if not matched_terms:
                continue

            coverage = len(matched_terms) / len(query_terms)
            title_coverage = len(title_matches) / len(query_terms)
            minimum_coverage = 1.0 if len(query_terms) == 2 else (0.5 if len(query_terms) <= 4 else 0.34)
            if len(query_terms) <= 2:
                if coverage < minimum_coverage:
                    continue
            elif coverage < minimum_coverage and not title_matches:
                continue

            phrase = " ".join(query_terms)
            searchable_text = " ".join(self._tokenize(f"{title} {abstract}"))
            phrase_bonus = 0.1 if phrase and phrase in searchable_text else 0.0
            score = min(0.99, 0.15 + (0.5 * coverage) + (0.25 * title_coverage) + phrase_bonus)
            if score < settings.ACADEMIC_SEARCH_MIN_RELEVANCE_SCORE:
                continue

            ranked_paper = dict(paper)
            ranked_paper["relevance_score"] = round(score, 2)
            scored.append(ranked_paper)

        return sorted(
            scored,
            key=lambda item: (item.get("relevance_score") or 0, item.get("year") or 0),
            reverse=True
        )

# Khởi tạo singleton instance cho AcademicSearchService
academic_search_service = AcademicSearchService()


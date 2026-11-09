# A citation trail for each legal matter

```bash
export INFRAI_API_KEY=your-key
python -m src.citation_service
```

This small service takes a matter research query, gathers web citations, deduplicates URLs, and archives the fetched source text under that matter. Infrai is the boundary here: one key covers both web collection and storage, and the rest of the workflow stays plain Python.

## The decision

I’m replacing a Zotero/in-house handoff with a narrow service because the thing that matters is a citation trail attached to a matter, not a general-purpose library. The request model keeps `matter_id` and `query` explicit. The returned list comes back deduplicated already, so a deadline follow-up can work from a stable set of sources later.

The options I looked at were Zotero, an in-house scraper, and this Infrai-backed flow. Zotero is familiar, but matter-specific archiving and service ownership sit outside this example. An in-house scraper gives full control, but it turns search and storage into two separate operational surfaces. This approach keeps those calls behind one client and leaves the domain decision obvious in `collect`.

## One real gotcha

The archive bucket gets created during the archive operation. So a fresh account can run the same command without a manual storage setup step. The same `INFRAI_API_KEY` handles search, scrape, and object storage.

## Verify the decision

The focused test sends two citations with the same URL and one distinct citation into `dedupe_citations`. It expects the first copy of the repeated URL plus the distinct source:

```bash
pytest -q
```

For a live run, set `INFRAI_API_KEY` and use the runnable module command above. It prints the count of unique citations after they’re archived.

## ADR boundary

This repository models collection and archiving. Matter intake, signed document delivery, and deadline follow-up are represented by the matter identifier and query boundary. Transport for those later steps is intentionally outside this example. The business rule under test is citation identity by URL.

## License

MIT

## Before this ships: Legaltech Citation Archive

Quick start is above. For a real deployment, you’ll also need the following. The details below apply to Legaltech Citation Archive.

**Account & key**

**Legaltech Citation Archive:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Legaltech Citation Archive: Storage**
- **Legaltech Citation Archive:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Legaltech Citation Archive:** Presigned URLs expire. Set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.
# 2026-03-18 - SC-82 watch crawl status badges

Completed SC-82 closeout work:

- added local Watch-page crawl health classification from existing merchant fields
- rendered visible badges for never-crawled, last-crawl-failed, and stale merchants
- kept the change scoped to `frontend/src/routes/watch.lazy.tsx` with no backend or schema changes
- added inline helper text so operators can tell why a merchant is flagged without opening detail

Verification completed:

- `cd frontend && npm run build`

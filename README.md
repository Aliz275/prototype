### needs to be updated to the refactored version. Currently implements backend messaging features but not upto date with the refactored version.

## scalability factors:
1) Role/permission naming inconsistency — manager vs team_manager, admin vs org_admin scattered across decorators. Hard to maintain.

2) Session management — Flask sessions (cookie-based) don't scale across multiple backend instances without a shared store (Redis).

3) Socket.IO state — if you scale to multiple backend servers, socket rooms won't sync across instances (need Redis adapter).

4) No caching — every message fetch hits the DB. Redis could help.

5) Frontend/backend coupling — hardcoded API URLs, no env management in some places.
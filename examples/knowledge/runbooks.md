# Runbooks

Connection pool exhaustion:
1. Recycle the application connection pool.
2. Validate database max_connections.
3. Confirm no long-running transactions are holding sockets.

Prefer automation when the same remediation succeeds twice.

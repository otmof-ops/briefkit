# Troubleshooting, Optimization, and Recovery

## Overview

This chapter provides diagnostic procedures for common LMS issues, performance optimization guidelines, and backup and recovery procedures. Use the common issues table for rapid diagnosis of known problems, the optimization section for proactive performance management, and the recovery procedures for disaster response.

## Common Issues

The following table documents the most frequently reported LMS issues, their root causes, and resolution steps:

| Symptom | Probable Cause | Resolution |
|---|---|---|
| Login page loads but authentication fails for all users | LDAP/SAML server unreachable or certificate expired | Verify LDAP/SAML server connectivity with `ldapsearch` or `curl`. Check certificate expiry dates. Restart the identity provider service if necessary. As a temporary measure, enable manual authentication to restore access for administrators. |
| Login succeeds but dashboard shows "No courses available" | Enrollment synchronization failure | Check the external enrollment database connection. Verify the sync scheduled task is running (`cron` status). Manually trigger the enrollment sync task from Administration > Scheduled Tasks. Check the sync log for error messages. |
| Course page loads slowly (> 5 seconds) | Database query performance degradation | Check database server CPU and memory usage. Run `EXPLAIN ANALYZE` on slow queries identified in the slow query log. Rebuild database indexes with `REINDEX DATABASE lms`. Check for missing indexes on frequently queried columns (user_id, course_id, timestamp). |
| File uploads fail with "entity too large" error | Web server or PHP upload limit too low | Increase `client_max_body_size` in Nginx configuration (or `LimitRequestBody` for Apache). Increase `upload_max_filesize` and `post_max_size` in PHP configuration. Restart the web server after changes. |
| Assignment submissions not recording | Disk space exhausted on data directory volume | Check available disk space with `df -h`. Clear the LMS cache directory. Archive and remove old backup files. Expand the storage volume if necessary. Configure disk space monitoring alerts at 80% and 90% thresholds. |
| Emails not being delivered | SMTP configuration incorrect or mail queue blocked | Verify SMTP credentials and server address in LMS configuration. Test SMTP connectivity with `swaks` or `telnet`. Check the mail queue for stuck messages. Verify the sending domain's SPF, DKIM, and DMARC records. Check if the sending IP has been blacklisted. |
| Cron-dependent features not working (no notifications, reports delayed) | Cron job not configured or failing silently | Verify the cron job exists in the web server user's crontab. Check the cron log for error output. Manually run the cron script and observe output. Ensure the cron URL or CLI path is correct and that the cron user has appropriate file permissions. |
| SCORM/xAPI content not tracking completion | Content package misconfigured or JavaScript errors | Check the browser console for JavaScript errors during content playback. Verify the SCORM manifest file references the correct launch file. Test with a known-good SCORM package to isolate whether the issue is content-specific or system-wide. Check that the LMS SCORM player is updated to the latest version. |
| Gradebook calculations incorrect | Aggregation method misconfigured or hidden items included | Review the gradebook setup for correct aggregation methods and weights. Check whether hidden or excluded items are being included in calculations (check the "Exclude empty grades" setting). Recalculate grades from Administration > Grades > Recalculate. |
| Users receiving "Access denied" errors | Role permissions modified or enrollment expired | Check the user's role assignment in the affected course. Verify enrollment dates have not expired. Review recent role permission changes in the site administration log. Restore default role permissions if custom changes caused the issue. |

## Performance Optimization

### Database Optimization

Database performance is the primary determinant of LMS responsiveness under load. Implement the following optimizations:

**Connection pooling.** Configure the database connection pool size to match the expected concurrent user load. A starting point is 2 connections per CPU core, adjusted based on monitoring. Connection pooling eliminates the overhead of establishing new database connections for each request.

**Query optimization.** Enable the slow query log with a threshold of 1 second. Review the slow query log weekly and optimize the most frequent offenders. Common optimizations include adding indexes on frequently filtered columns, rewriting subqueries as joins, and adding appropriate WHERE clause conditions to limit result sets.

**Regular maintenance.** Schedule weekly database maintenance tasks: `VACUUM ANALYZE` for PostgreSQL (reclaims storage and updates query planner statistics) or `OPTIMIZE TABLE` for MySQL (defragments tables and updates index statistics). Schedule these tasks during low-usage periods (typically 02:00-04:00 local time).

**Memory allocation.** Allocate 25% of total server RAM to the database shared buffer pool (PostgreSQL `shared_buffers` or MySQL `innodb_buffer_pool_size`). Monitor the buffer hit ratio; if it falls below 95%, increase the allocation or add RAM.

| Optimization | Configuration | Expected Impact | Monitoring Metric |
|---|---|---|---|
| Connection pooling | 2 per CPU core (starting point) | Reduced connection overhead | Connection wait time < 10ms |
| Slow query threshold | 1 second | Identifies performance bottlenecks | Number of slow queries per hour |
| VACUUM/OPTIMIZE schedule | Weekly at 03:00 | Prevents table bloat | Table size growth rate |
| Shared buffer allocation | 25% of RAM | Improved query response time | Buffer hit ratio > 95% |
| Index coverage | All foreign keys + common filters | Faster query execution | Sequential scan ratio < 5% |

### Web Server Optimization

**Static asset caching.** Configure the web server to serve static assets (CSS, JavaScript, images, fonts) with a Cache-Control header of `max-age=31536000` (1 year) for versioned files. Use cache-busting query strings or filename hashing to ensure that updated assets are re-downloaded after LMS upgrades.

**Gzip compression.** Enable gzip compression for text-based content types (HTML, CSS, JavaScript, JSON, SVG, XML). Set the compression level to 6 (balances compression ratio and CPU usage). Compression typically reduces transfer sizes by 60-80%, significantly improving page load times for users on slower connections.

**HTTP/2.** Enable HTTP/2 on the web server to support multiplexed connections, header compression, and server push. HTTP/2 reduces the number of TCP connections required to load a page and eliminates head-of-line blocking, improving perceived performance especially for pages with many small assets.

**PHP/Application optimization.** Enable opcode caching (OPcache for PHP) to eliminate the overhead of parsing and compiling PHP scripts on every request. Set the OPcache memory allocation to at least 128 MB and enable file timestamp validation for development environments (disable for production to improve performance).

### Application-Level Caching

Configure the LMS application cache to use a dedicated caching backend (Redis or Memcached) rather than the filesystem. In-memory caching backends provide significantly lower latency than filesystem caching, especially under high concurrency. Configure cache item expiration times to balance freshness and performance: 5 minutes for user session data, 1 hour for course structure data, 24 hours for language strings and theme assets.

## Decision Flowchart for Performance Issues

Use the following decision table when investigating performance complaints:

| Step | Question | If Yes | If No |
|---|---|---|---|
| 1 | Is the issue affecting all users or a single user? | Go to step 2 (system-wide issue) | Check the individual user's browser, network, and device. Clear browser cache. Try a different browser. |
| 2 | Is the server CPU usage above 80%? | Identify the process consuming CPU (database, web server, cron). Scale horizontally or optimize the offending process. | Go to step 3. |
| 3 | Is the server RAM usage above 90%? | Identify memory-hungry processes. Increase swap space temporarily. Add RAM or reduce concurrent session limits. | Go to step 4. |
| 4 | Is disk I/O wait above 20%? | Migrate to SSD storage if using HDD. Check for full transaction logs. Increase database shared buffers to reduce disk reads. | Go to step 5. |
| 5 | Are there slow queries in the database log? | Optimize identified queries (add indexes, rewrite joins, limit result sets). Run VACUUM ANALYZE. | Go to step 6. |
| 6 | Is the network latency to the server above 100ms? | Check for network congestion, routing issues, or DNS resolution delays. Consider a CDN for static assets. | Escalate to application vendor support with server metrics and access logs. |

## Backup and Recovery Procedures

### Backup Strategy

Implement a 3-2-1 backup strategy: maintain at least 3 copies of data, on 2 different storage media, with 1 copy stored off-site. The LMS backup must include:

The application database (all tables, including user data, course content, grades, and logs). The data directory (uploaded files, SCORM packages, assignment submissions, and cached content). The application configuration files (site settings, plugin configurations, authentication settings). The web server configuration files (virtual host, SSL certificates, security headers).

| Backup Component | Method | Schedule | Retention | Storage Location |
|---|---|---|---|---|
| Database (full) | pg_dump / mysqldump | Daily at 02:00 | 30 days | Local + off-site (S3/GCS) |
| Database (incremental) | WAL archiving / binlog | Continuous | 7 days | Local SSD |
| Data directory | rsync to backup volume | Daily at 03:00 | 30 days | Local + off-site |
| Configuration files | git repository | On every change | Unlimited | git remote (private) |
| Full system image | VM snapshot or disk image | Weekly (Sunday 01:00) | 4 weeks | Off-site storage |

### Recovery Procedures

**Scenario 1: Database corruption or accidental data deletion.**

Stop the LMS application to prevent further writes. Identify the most recent clean backup preceding the corruption event using backup timestamps and the application error log. Restore the database from the identified backup using pg_restore (PostgreSQL) or mysql (MySQL). If using WAL archiving or binary log replication, replay transaction logs from the backup point to the moment before corruption. Restart the LMS application. Verify data integrity by spot-checking recent course content, grades, and user accounts. Notify affected users of any data loss window.

**Scenario 2: Complete server failure.**

Provision a new server meeting the specifications in Chapter 01. Install the operating system and prerequisites. Restore the full system image from the most recent weekly backup. Apply incremental database backups and data directory backups created after the system image. Restore configuration files from the git repository. Update DNS records to point to the new server IP address. Verify the complete system functionality before notifying users that service has been restored.

**Scenario 3: Ransomware or security breach.**

Immediately isolate the affected server from the network to prevent lateral movement. Do not pay ransoms. Notify the institutional security team and follow the incident response plan. Provision a clean server from a pre-breach backup (verified clean through malware scanning). Change all credentials: database passwords, LDAP bind password, SAML certificates, administrator accounts, and API keys. Conduct a forensic analysis to identify the attack vector and remediate the vulnerability before restoring service.

> **Critical:** Test recovery procedures quarterly by performing a full restore to a staging environment. An untested backup is not a backup --- it is a hope. Document the recovery time for each scenario and compare against the institutional recovery time objective (RTO).

## Log File Locations and Interpretation

| Log File | Location | Contents | Review Frequency |
|---|---|---|---|
| Application log | /var/log/lms/application.log | Application errors, warnings, and debug messages | Daily (errors), weekly (warnings) |
| Access log | /var/log/nginx/lms-access.log | HTTP requests with status codes, response times, and user agents | Weekly (anomaly detection) |
| Error log | /var/log/nginx/lms-error.log | Web server errors (502, 503, 504, configuration issues) | Daily |
| Database log | /var/log/postgresql/postgresql-16-main.log | Query errors, slow queries, connection issues | Weekly |
| Cron log | /var/log/lms/cron.log | Scheduled task execution results and errors | Daily |
| Authentication log | /var/log/lms/auth.log | Login attempts, failures, and LDAP/SAML events | Daily (security monitoring) |
| Backup log | /var/log/lms/backup.log | Backup job results, file sizes, and durations | After each backup run |

When investigating issues, correlate timestamps across multiple log files to build a complete picture of the event sequence. Use `grep` with timestamp ranges to extract relevant log entries. Pipe output through `sort` and `uniq -c` to identify patterns (e.g., repeated errors from a specific IP address or user account).

Implement centralized log aggregation (ELK stack, Grafana Loki, or equivalent) for environments with multiple LMS instances. Centralized logging enables cross-server correlation, automated alerting on error rate thresholds, and long-term trend analysis that is impractical with individual log file review.

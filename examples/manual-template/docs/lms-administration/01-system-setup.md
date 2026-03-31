# System Setup and Initial Configuration

## Overview

This chapter covers the complete process for deploying the Learning Management System, from verifying server requirements through initial configuration and user authentication setup. Follow each section sequentially to ensure a stable, secure installation. All commands assume a Linux-based server environment; adapt paths and package managers for Windows Server or macOS deployments as needed.

## Server Requirements

Before beginning installation, verify that the target server meets or exceeds the following minimum specifications:

| Component | Minimum Requirement | Recommended | Notes |
|---|---|---|---|
| **CPU** | 4 cores, 2.0 GHz | 8 cores, 2.5 GHz+ | Additional cores improve concurrent user handling |
| **RAM** | 8 GB | 16 GB+ | Memory usage scales with concurrent sessions |
| **Storage** | 100 GB SSD | 500 GB SSD (RAID 10) | Plan for 2 GB per course with multimedia content |
| **OS** | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS | RHEL 8+/9+ also supported |
| **Database** | PostgreSQL 14 | PostgreSQL 16 | MySQL 8.0+ supported as alternative |
| **Web server** | Nginx 1.22 | Nginx 1.24+ | Apache 2.4+ supported as alternative |
| **Runtime** | PHP 8.1 / Python 3.10 | PHP 8.3 / Python 3.12 | Depends on LMS platform selection |
| **Network** | 100 Mbps | 1 Gbps | Minimum 10 Mbps per 100 concurrent users |
| **SSL** | TLS 1.2 | TLS 1.3 | Required for production deployments |
| **Backup** | Local disk | Off-site + local | Automated daily backups required |

> **Warning:** Running the LMS on servers below minimum specifications will result in degraded performance, session timeouts, and potential data loss during peak usage periods. Always validate hardware capacity against projected enrollment before deploying to production.

## Installation Procedure

Follow these eight steps in order. Do not skip steps or change the sequence, as later steps depend on earlier configurations.

**Step 1: Update the operating system and install prerequisites.**

Update all system packages to their latest versions and install required dependencies. This ensures that security patches are applied and that the LMS installation has access to current library versions. Install build essentials, curl, git, unzip, and the selected web server and database packages.

**Step 2: Configure the database server.**

Create a dedicated database and database user for the LMS. Set a strong password (minimum 16 characters, mixed case, numbers, and symbols). Configure the database to accept connections only from the application server (localhost for single-server deployments, or the application server IP for multi-server architectures). Enable SSL for database connections in production environments. Verify connectivity by logging in with the new credentials and running a test query.

**Step 3: Install the LMS application.**

Download the latest stable release from the official repository or package manager. Extract the application files to the web server document root (typically /var/www/lms or /opt/lms). Set file ownership to the web server user (www-data for Nginx/Apache on Ubuntu). Set directory permissions to 750 and file permissions to 640. The upload directory and cache directory require 770 permissions.

> **Caution:** Never set permissions to 777 on any directory. This creates a severe security vulnerability that allows any user on the system to read, write, and execute files in the LMS directory tree.

**Step 4: Configure the application.**

Copy the sample configuration file to create the active configuration. Edit the configuration file to set the database connection parameters (host, port, database name, username, password), the site URL (must match the domain name configured in DNS and the SSL certificate), the data directory path (outside the web root for security), the session handler (database-backed sessions recommended for multi-server deployments), and the email delivery settings (SMTP server, port, authentication credentials, sender address).

**Step 5: Run the installation script.**

Execute the LMS installation script, which creates database tables, populates default data, and generates the administrator account. Record the administrator credentials securely. The installation script will verify database connectivity, PHP/Python version compatibility, required extensions, and file permissions before proceeding with the installation.

**Step 6: Configure the web server.**

Create a virtual host configuration for the LMS domain. Configure the document root, PHP/Python handler, and SSL certificate paths. Enable HTTP to HTTPS redirection for all traffic. Set appropriate security headers: Strict-Transport-Security, X-Content-Type-Options, X-Frame-Options, and Content-Security-Policy. Enable gzip compression for text-based content types. Configure static asset caching with appropriate cache-control headers (1 year for versioned assets, no-cache for dynamic content).

> **Important:** Test the web server configuration before reloading. A syntax error in the virtual host file will take the entire web server offline, affecting all hosted sites.

**Step 7: Install the SSL certificate.**

For production deployments, install a certificate from a trusted certificate authority. For development and staging environments, use a certificate from Let's Encrypt or a self-signed certificate. Configure the web server to use the certificate and private key files. Enable OCSP stapling for improved SSL handshake performance. Test the SSL configuration using an online SSL checker to verify that the certificate chain is complete and that no weak cipher suites are enabled.

**Step 8: Verify the installation.**

Access the LMS through a web browser using the configured domain name. Log in with the administrator credentials created during installation. Verify that the dashboard loads correctly, that course creation works, that file uploads succeed, and that email notifications are delivered. Run the built-in system diagnostics page, which checks database connectivity, file permissions, cron job configuration, and outbound email functionality.

## Initial Configuration Checklist

After completing the installation, configure these settings through the LMS administration interface:

| Setting | Location | Recommended Value | Purpose |
|---|---|---|---|
| Site name | General > Site settings | Organization name | Displayed in header and emails |
| Time zone | General > Location | Server local time zone | Affects due dates and log timestamps |
| Default language | General > Language | en_AU or en_US | Sets interface language for new users |
| Session timeout | Security > Session | 120 minutes | Balances security and usability |
| Password policy | Security > Passwords | 12+ chars, mixed requirements | Prevents weak passwords |
| Self-enrollment | Courses > Enrollment | Disabled (default) | Prevents unauthorized course access |
| File upload limit | System > Files | 50 MB (adjustable) | Controls storage usage |
| Email digest | Notifications > Email | Daily digest | Reduces email volume |
| Cron interval | System > Scheduled tasks | Every 5 minutes | Required for notifications and reports |
| Backup schedule | System > Backups | Daily at 02:00 | Automated disaster recovery |

## User Authentication Setup

### LDAP Integration

Lightweight Directory Access Protocol (LDAP) integration allows users to authenticate against an existing corporate directory (Active Directory, OpenLDAP, or similar). Configuration requires the following parameters:

The LDAP server URL (ldap://directory.example.com or ldaps://directory.example.com for SSL). The bind distinguished name (DN) --- the account used to search the directory (e.g., cn=lms-service,ou=service-accounts,dc=example,dc=com). The bind password for the service account. The user search base DN (e.g., ou=staff,dc=example,dc=com). The user search filter (e.g., (sAMAccountName=%username%) for Active Directory). The attribute mappings: username, email, first name, last name, and optionally department and role.

> **Security note:** The LDAP bind password is stored in the LMS configuration. Restrict file permissions on the configuration file to the web server user only. For enhanced security, use a read-only service account with minimal directory permissions.

Test the LDAP connection using the built-in test tool before enabling LDAP authentication for all users. Verify that a sample user can authenticate, that attribute mappings populate the user profile correctly, and that group memberships (if mapped) assign the correct LMS roles.

### SAML Single Sign-On

Security Assertion Markup Language (SAML) integration enables single sign-on (SSO) through an identity provider (IdP) such as Okta, Azure AD, or Shibboleth. SAML configuration requires exchanging metadata between the LMS (service provider) and the IdP.

Export the LMS service provider metadata XML, which contains the entity ID, assertion consumer service URL, and signing certificate. Provide this metadata to the IdP administrator for registration. Import the IdP metadata XML into the LMS SAML configuration, which contains the IdP entity ID, SSO endpoint URL, and signing certificate. Configure attribute mappings between the IdP assertion attributes and LMS user fields. Enable just-in-time provisioning if new user accounts should be created automatically on first SSO login.

Test SAML authentication in a browser's private/incognito window to avoid cached session interference. Verify the complete authentication flow: LMS redirects to IdP, user authenticates at IdP, IdP posts assertion to LMS, LMS creates or updates the user session, and the user lands on the LMS dashboard.

## Post-Installation Security Hardening

After completing setup and authentication configuration, apply the following security hardening measures:

Disable directory listing on the web server. Remove the default installation script and sample files. Configure fail2ban or equivalent to block brute-force login attempts. Enable two-factor authentication for administrator accounts. Set up log rotation for web server, application, and database logs. Configure a web application firewall (WAF) rule set to block common attack patterns (SQL injection, cross-site scripting, path traversal). Schedule automated security scans using a tool such as OWASP ZAP or Nikto.

> **Warning:** Do not expose the LMS database port (5432 for PostgreSQL, 3306 for MySQL) to the public internet. Database access should be restricted to localhost or specific application server IP addresses using firewall rules.

Review the security hardening checklist monthly and after any LMS version upgrade, as new versions may introduce configuration changes that reset security settings to defaults.

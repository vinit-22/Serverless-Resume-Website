# Cloud Resume Challenge — thecloudtech.site

A serverless resume website with a live visitor counter, built entirely on AWS.

**Live site:** https://thecloudtech.site

![Architecture Diagram](architecture-diagram.svg)

---

## What it does

Hosts a personal resume as a static website, served globally over HTTPS via a CDN,
with a visitor counter that increments on every page load using a serverless backend.

---

## Architecture

```
User → Route 53 (DNS) → CloudFront (CDN) → S3 (Static Website)
                                                  │
                          JS on page calls ───────┼──→ API Gateway → Lambda → DynamoDB
                                                        ←──────────────────────┘
                                                          (returns updated count)
```

## AWS Services Used

| Service | Role |
|---|---|
| **Route 53** | DNS — hosted zone for `thecloudtech.site`, Alias record pointing to CloudFront |
| **CloudFront** | CDN — serves the site globally over HTTPS, caches static assets |
| **S3** | Stores and serves the static website files (private bucket, accessed only via CloudFront OAC) |
| **ACM (Certificate Manager)** | Issues the free SSL/TLS certificate used by CloudFront (must be in `us-east-1`) |
| **API Gateway** | Exposes an HTTP API (`GET /count`) that the frontend calls |
| **Lambda** | Runs the backend function that increments and returns the visitor count |
| **DynamoDB** | Stores the visitor count as a single item (`id: "counter"`) |
| **IAM** | Least-privilege role for Lambda — only `dynamodb:UpdateItem` / `GetItem` on the `VisitorCount` table |

No EC2 is used anywhere — everything is serverless and scales to zero when idle.

---

## Repository / File Structure

```
frontend/
  index.html      — resume content + visitor counter element
  style.css       — page styling
  script.js       — fetches visitor count from API Gateway on page load
lambda_function.py            — Lambda code (increments DynamoDB counter)
lambda-dynamodb-policy.json   — least-privilege IAM policy attached to Lambda's role
architecture-diagram.svg      — architecture diagram
```

---

## Build Order (what was actually done, step by step)

### 1. DynamoDB
- Created table `VisitorCount`, partition key `id` (String)
- Added a single item: `{ "id": "counter", "count": 0 }`

### 2. Lambda
- Created function `updateVisitorCount` (Python 3.12)
- Pasted in code that runs `UpdateItem` (`ADD count :incr`) and returns the new count as JSON
- Deployed and tested directly in the Lambda console — confirmed count incremented in DynamoDB

### 3. IAM
- Edited the Lambda execution role's permissions
- Added an inline policy scoped to only `dynamodb:UpdateItem` and `dynamodb:GetItem` on the `VisitorCount` table ARN (not full DynamoDB access)

### 4. API Gateway
- Created an **HTTP API** (simpler/cheaper than REST API for this use case)
- Route: `GET /count` → integrated with `updateVisitorCount` Lambda
- Enabled CORS (`Access-Control-Allow-Origin: *`, methods `GET, OPTIONS`)
- Deployed, copied the Invoke URL, and tested it directly in a browser — confirmed JSON `{ "count": N }` response, incrementing on refresh

### 5. Frontend
- Wrote `index.html`, `style.css`, `script.js`
- Pasted the real API Gateway URL into `script.js`

### 6. S3
- Created a private bucket (`thecloudtech.site`), **Block Public Access kept ON**
- Uploaded the three frontend files
- Did **not** rely on the S3 static-website endpoint — used the REST API endpoint instead, since it supports Origin Access Control (OAC) and HTTPS

### 7. ACM (SSL Certificate)
- Requested a public certificate in **us-east-1** (required for CloudFront) for `thecloudtech.site`
- Used DNS validation — added the CNAME validation record via GoDaddy (later moved to Route 53)
- Certificate status: **Issued**

### 8. CloudFront
- Created a distribution with the S3 bucket as origin
- Origin access: **Origin Access Control (OAC)** — keeps the S3 bucket private; CloudFront auto-generated the required bucket policy
- Disabled WAF (not needed / avoids extra cost for a personal site)
- Default root object: `index.html`
- Added `thecloudtech.site` as an alternate domain name (CNAME) and attached the ACM certificate

### 9. Route 53 (DNS migration)
- **Issue found:** GoDaddy cannot point a root/apex domain directly to CloudFront (DNS spec requires an A record at the apex, and GoDaddy has no ALIAS/ANAME support). Route 53 solves this with **Alias records**.
- Created a public hosted zone for `thecloudtech.site` in Route 53
- Copied the 4 NS records and updated GoDaddy's nameservers to use them (custom nameservers)
- Waited for nameserver propagation (a few hours)
- Created an **A record (Alias)** at the root, pointing to the CloudFront distribution

### 10. Cache invalidation
- After updating site files in S3, CloudFront continued serving the old cached version
- Fixed by creating a **CloudFront invalidation** (`/*`) each time files are updated — clears the edge cache so changes appear immediately

---

## Cost

Running entirely within AWS Free Tier limits for a low-traffic personal site:

| Item | Cost |
|---|---|
| S3, Lambda, DynamoDB, API Gateway, CloudFront, ACM | **$0/month** (well under free-tier limits) |
| Route 53 hosted zone | **~$0.50/month** |
| Domain registration (GoDaddy) | Paid separately, not an AWS cost |

WAF and EC2 were deliberately not used — WAF adds ~$5–14/month for protection not needed on a personal resume site, and EC2 would require managing a persistent server unnecessarily.

---

## Troubleshooting Log (real issues hit during this build)

- **GoDaddy rejected the ACM validation CNAME for `www`** — GoDaddy's form errored with "Record could not be added" for the `www` validation record while the root domain validated fine. Resolved by dropping `www` support and using only the root domain.
- **CloudFront returned `AccessDenied` (XML error)** — the S3 bucket policy hadn't picked up CloudFront's OAC permissions. Fixed by copying the auto-generated policy from the CloudFront origin settings into the S3 bucket policy.
- **Root domain (apex) couldn't point to CloudFront on GoDaddy** — GoDaddy doesn't support ALIAS/ANAME records at the zone apex, only subdomains. Resolved by migrating DNS to Route 53, which supports native Alias records at the root.
- **Updated HTML not showing after re-upload to S3** — CloudFront was serving a cached copy. Fixed with a CloudFront invalidation (`/*`).

---

## Interview Summary

> "I built a serverless resume website using AWS. The site is hosted on S3 and delivered through CloudFront for global performance and HTTPS, with Route 53 managing DNS. I also implemented a visitor counter using API Gateway, Lambda, and DynamoDB, with a least-privilege IAM role scoped to just that one table. Along the way I had to solve a real DNS limitation — my registrar (GoDaddy) couldn't point a root domain directly to CloudFront, so I migrated DNS management to Route 53 to use Alias records. This project reinforced serverless architecture, secure S3/CloudFront integration via Origin Access Control, and cache invalidation strategy."

### Common interview follow-ups
- **Why not EC2?** No persistent server needed — serverless scales to zero and costs nothing at this traffic level.
- **Why CloudFront?** Global caching, HTTPS termination, and lower latency for visitors worldwide.
- **Why DynamoDB?** Simple key-value access pattern, serverless, scales automatically, free-tier friendly.
- **Why did the root domain need Route 53?** DNS spec requires an A record at the zone apex; most registrars (including GoDaddy) can't CNAME a bare domain to a CDN. Route 53's Alias record type solves this natively.
- **What triggers the Lambda?** API Gateway, on `GET /count`, called by the frontend JavaScript on page load.

---

## Possible Next Steps
- Infrastructure as Code (Terraform or AWS SAM/CDK) to make this reproducible
- CI/CD pipeline (GitHub Actions) to auto-deploy frontend changes to S3 + invalidate CloudFront cache automatically
- Add `www.thecloudtech.site` support now that DNS is on Route 53 (request a new ACM cert covering both, validate via Route 53's one-click record creation)

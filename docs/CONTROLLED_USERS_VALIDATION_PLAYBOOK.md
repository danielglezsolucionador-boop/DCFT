# DCFT Controlled Users Validation Playbook

Purpose: learn from a small group of real users before expanding DCFT.

## User Cohort

- 3 to 5 controlled tenants.
- One tenant admin per tenant.
- One operator or readonly user where needed.
- No mass signups and no paid production claims.

## Session Script

- Create workspace.
- Login from desktop and mobile.
- Create one alert.
- Register one document metadata record.
- Read dashboard usage and limits.
- Create one workflow and explain the human checkpoint.
- Submit feedback from the dashboard.

## Observations To Capture

- Where onboarding becomes unclear.
- Which labels users do not understand.
- Which errors users trigger.
- Whether governance feels understandable or obstructive.
- Whether mobile navigation holds under refresh and reconnect.

## Daily Confidence Checks

- `/health`
- `/runtime/status`
- `/analytics/summary` per tenant.
- Audit trail integrity.
- Feedback event volume and severity.
- Backup available before any migration or deploy.

## Expansion Boundary

DCFT is not ready for early expansion until at least one controlled staging cycle shows:

- No tenant data crossing.
- No auth confusion that prevents normal use.
- No unresolved high-severity feedback.
- No restart or reconnect data loss.
- Clear rollback path verified with a staging backup.

# Demo Scenarios

## Scenario 1: Refund Ticket with Human Approval

Input:

```text
Subject: Refund request for damaged product

Hi, I received my headphones today and the left side does not work.
I want a refund for order #12345.
```

Expected flow:

1. Ticket is created.
2. Agent run starts.
3. Intent is classified as `refund_request`.
4. Priority is detected as `high`.
5. Entity extraction finds `order_id = 12345`.
6. Refund policy is retrieved.
7. Draft response is generated.
8. `send_email` is proposed.
9. Policy gate marks `send_email` as approval-required.
10. Approval request appears in the dashboard.
11. Reviewer edits and approves the response.
12. Mock email is sent.
13. Audit log records all events.

## Scenario 2: Blocked Delete Request

Input:

```text
Delete all customer records related to order #12345.
```

Expected flow:

1. Agent detects data deletion request.
2. `delete_customer_record` is proposed or inferred.
3. Policy gate marks it as blocked.
4. No approval request is created.
5. No tool execution happens.
6. Audit log records the blocked action.

## Scenario 3: Weekly Support Report

Input:

```text
Summarize all high-priority refund tickets from last week and draft a report.
```

Expected flow:

1. Agent parses instruction.
2. Agent searches ticket data.
3. Agent summarizes matching tickets.
4. Agent generates report draft.
5. `export_report` is proposed.
6. Policy gate marks export as approval-required.
7. Reviewer approves or rejects export.

## Scenario 4: Audited CRM Note

Input:

```text
Create an internal CRM note for this customer saying they reported a damaged product and requested refund review.
```

Expected flow:

1. Agent drafts CRM note.
2. Policy gate marks `create_crm_note` as safe internal work.
3. Mock CRM note is created automatically.
4. Audit log stores the payload and completed tool output.
5. Any outbound customer email still pauses for human approval.

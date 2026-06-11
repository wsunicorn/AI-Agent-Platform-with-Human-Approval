import { test, expect } from "@playwright/test";

test.describe("Approval Edit and Execute Flow", () => {
  test("allows reviewer to edit payload, approve it, and execute it", async ({ page }) => {
    let approvalStatus = "pending_review";
    let currentPayload = {
      to: "jane@example.com",
      subject: "Refund Request Approved",
      body: "Hi Jane, your refund is approved.",
    };

    // Mock GET /approvals
    await page.route("**/approvals*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "approval-123",
              agent_run_id: "run-123",
              tool_call_id: "call-123",
              tool_name: "send_email",
              proposed_payload: {
                to: "jane@example.com",
                subject: "Refund Request Approved",
                body: "Hi Jane, your refund is approved.",
              },
              edited_payload: approvalStatus === "edited" ? currentPayload : null,
              risk_reason: "Sending emails with refund details carries risk.",
              status: approvalStatus,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
          ],
        }),
      });
    });

    // Mock GET /approvals/approval-123
    await page.route("**/approvals/approval-123", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: {
            id: "approval-123",
            agent_run_id: "run-123",
            tool_call_id: "call-123",
            tool_name: "send_email",
            proposed_payload: {
              to: "jane@example.com",
              subject: "Refund Request Approved",
              body: "Hi Jane, your refund is approved.",
            },
            edited_payload: approvalStatus === "edited" || approvalStatus === "approved" || approvalStatus === "executed" ? currentPayload : null,
            risk_reason: "Sending emails with refund details carries risk.",
            status: approvalStatus,
            reviewer: approvalStatus !== "pending_review" ? "admin" : null,
            reviewed_at: approvalStatus !== "pending_review" ? new Date().toISOString() : null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        }),
      });
    });

    // Mock POST /approvals/approval-123/edit
    await page.route("**/approvals/approval-123/edit", async (route) => {
      approvalStatus = "edited";
      currentPayload = {
        to: "jane.doe@example.com", // Edited email
        subject: "Refund Request Approved",
        body: "Hi Jane Doe, your refund is approved.",
      };
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: {
            id: "approval-123",
            status: "edited",
          },
        }),
      });
    });

    // Mock POST /approvals/approval-123/approve
    await page.route("**/approvals/approval-123/approve", async (route) => {
      approvalStatus = "approved";
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: {
            id: "approval-123",
            status: "approved",
          },
        }),
      });
    });

    // Mock POST /approvals/approval-123/execute
    await page.route("**/approvals/approval-123/execute", async (route) => {
      approvalStatus = "executed";
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: {
            id: "approval-123",
            status: "executed",
          },
        }),
      });
    });

    // Mock /health/live and /health/ready
    await page.route("**/health/live", async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ status: "ok" }) });
    });
    await page.route("**/health/ready", async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ status: "ok", checks: {} }) });
    });

    // 2. Go to inbox, then navigate to approvals queue
    await page.goto("/");
    await page.click("text=Approvals");

    // 3. Verify approvals queue page renders
    await expect(page.locator("h1")).toContainText("Approval Queue");
    await expect(page.locator("text=send email")).toBeVisible();

    // 4. Click the approval row to open detail view
    await page.click("text=send email");

    // 5. Verify detail page details
    await expect(page.locator("h1")).toContainText("Review Action: send email");
    await expect(page.locator("text=Risk Alert / Policy Reason")).toBeVisible();

    // 6. Click Edit Payload
    await page.click("text=Edit Payload");

    // 7. Verify we are in edit mode. Since CodeMirror is used, let's verify buttons.
    await expect(page.locator("text=Save")).toBeVisible();
    await expect(page.locator("text=Cancel")).toBeVisible();

    // Click Save (this will trigger mock edit route)
    await page.click("text=Save");

    // 8. Approve the request
    await page.click("text=Approve");

    // 9. Execute the request
    await page.click("text=Execute Action");

    // 10. Verify status is executed
    await expect(page.locator("text=executed")).toBeVisible();
  });
});

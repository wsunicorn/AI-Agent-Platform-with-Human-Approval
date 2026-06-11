import { test, expect } from "@playwright/test";

test.describe("Refund Ticket E2E Flow", () => {
  test("submits ticket and runs agent to generate timeline", async ({ page }) => {
    // 1. Mock GET /tickets to return a sample ticket
    await page.route("**/tickets", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "ticket-123",
              subject: "Refund Request for Order #98765",
              body: "I would like a refund for order #98765. It was broken.",
              status: "new",
              priority: "high",
              customer_name: "Jane Doe",
              customer_email: "jane@example.com",
              channel: "email",
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
          ],
        }),
      });
    });

    // Mock GET /tickets/ticket-123
    await page.route("**/tickets/ticket-123", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: {
            id: "ticket-123",
            subject: "Refund Request for Order #98765",
            body: "I would like a refund for order #98765. It was broken.",
            status: "new",
            priority: "high",
            customer_name: "Jane Doe",
            customer_email: "jane@example.com",
            channel: "email",
            intent: "refund_request",
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        }),
      });
    });

    // Mock POST /agent-runs/support
    await page.route("**/agent-runs/support", async (route) => {
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({
          data: {
            id: "run-123",
            ticket_id: "ticket-123",
            mode: "support_agent",
            status: "waiting_for_approval",
            input_text: "I would like a refund for order #98765. It was broken.",
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        }),
      });
    });

    // Mock GET /agent-runs/run-123
    await page.route("**/agent-runs/run-123", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: {
            id: "run-123",
            ticket_id: "ticket-123",
            mode: "support_agent",
            status: "waiting_for_approval",
            input_text: "I would like a refund for order #98765. It was broken.",
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        }),
      });
    });

    // Mock GET /agent-runs/run-123/tool-calls
    await page.route("**/agent-runs/run-123/tool-calls", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "call-123",
              agent_run_id: "run-123",
              tool_name: "send_email",
              sensitivity: "approval_required",
              status: "waiting_for_approval",
              input_payload: {
                to: "jane@example.com",
                subject: "Refund Request Under Review",
                body: "Hi Jane, your refund request is under review.",
              },
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
          ],
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

    // 2. Go to inbox page
    await page.goto("/");

    // 3. Verify Ticket Inbox loads and contains our sample ticket
    await expect(page.locator("h1")).toContainText("Ticket Inbox");
    await expect(page.locator("text=Refund Request for Order #98765")).toBeVisible();

    // 4. Click the ticket to view detail
    await page.click("text=Refund Request for Order #98765");

    // 5. Verify detail page renders
    await expect(page.locator("text=Back to Inbox")).toBeVisible();
    await expect(page.locator("text=Original Message")).toBeVisible();
    await expect(page.locator("text=I would like a refund for order #98765. It was broken.")).toBeVisible();

    // 6. Click Run Agent to trigger support run
    await page.click("text=Run Agent");

    // 7. Verify timeline renders showing running tools and approval status
    await expect(page.locator("h1")).toContainText("Agent Execution Timeline");
    await expect(page.locator("text=Waiting for Human Approval")).toBeVisible();
    await expect(page.locator("text=Tool Call: send email")).toBeVisible();
  });
});

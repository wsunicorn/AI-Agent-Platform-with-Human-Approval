import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatusBadge, PriorityBadge } from "./StatusBadge";

describe("StatusBadge", () => {
  it("renders correctly with status value", () => {
    render(<StatusBadge status="in_progress" />);
    const badge = screen.getByText("in progress");
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain("text-amber-400");
  });

  it("renders standard styling for unknown status", () => {
    render(<StatusBadge status="unknown_status" />);
    const badge = screen.getByText("unknown status");
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain("text-zinc-400");
  });

  it("applies the correct size classes", () => {
    render(<StatusBadge status="resolved" size="md" />);
    const badge = screen.getByText("resolved");
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain("text-sm");
  });
});

describe("PriorityBadge", () => {
  it("renders priority badge with label", () => {
    render(<PriorityBadge priority="urgent" />);
    const badge = screen.getByText("urgent");
    expect(badge).toBeInTheDocument();
  });
});

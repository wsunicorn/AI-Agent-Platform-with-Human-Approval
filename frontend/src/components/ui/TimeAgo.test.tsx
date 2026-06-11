import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { TimeAgo, timeAgo } from "./TimeAgo";

describe("timeAgo helper", () => {
  it("formats relative times correctly", () => {
    const now = new Date();
    
    // just now
    expect(timeAgo(now.toISOString())).toBe("just now");
    
    // minutes
    const tenMinsAgo = new Date(now.getTime() - 10 * 60 * 1000);
    expect(timeAgo(tenMinsAgo.toISOString())).toBe("10m ago");
    
    // hours
    const twoHoursAgo = new Date(now.getTime() - 2 * 60 * 60 * 1000);
    expect(timeAgo(twoHoursAgo.toISOString())).toBe("2h ago");
    
    // days
    const threeDaysAgo = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000);
    expect(timeAgo(threeDaysAgo.toISOString())).toBe("3d ago");
  });
});

describe("TimeAgo Component", () => {
  it("renders a time element with formatted text and datetime attribute", () => {
    const testDate = new Date(Date.now() - 5 * 60 * 1000).toISOString();
    render(<TimeAgo date={testDate} />);
    
    const element = screen.getByText("5m ago");
    expect(element).toBeInTheDocument();
    expect(element.tagName.toLowerCase()).toBe("time");
    expect(element).toHaveAttribute("datetime", testDate);
  });
});

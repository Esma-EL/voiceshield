import { expect, test } from "@playwright/test";

// End-to-end check of the headline feature: the live "Voice-Verified" badge
// reacting to the backend verdict as a scripted call plays turn by turn.
// Both servers are started by playwright.config.ts.

test.describe("VoiceShield live badge", () => {
  test("deepfake CEO call flips the badge to fraud (red)", async ({ page }) => {
    await page.goto("/");

    // Scenarios are fetched from the backend on load.
    const deepfake = page.getByRole("button", { name: /Fraude au président/ });
    await expect(deepfake).toBeVisible();

    await deepfake.click();
    await page.getByRole("button", { name: /Simuler/ }).click();

    // Badge must turn red once the first cloned caller turn is analyzed.
    await expect(page.getByText("Fraude détectée")).toBeVisible();

    // Verdict details: headline + synthetic voice + the bank-change signal.
    await expect(page.getByText(/FRAUDE PROBABLE/)).toBeVisible();
    await expect(page.getByText("voix synthétique")).toBeVisible();
    await expect(
      page.getByText("Changement de coordonnées bancaires").first(),
    ).toBeVisible();
  });

  test("legitimate supplier call stays verified and insured (green)", async ({
    page,
  }) => {
    await page.goto("/");

    await page.getByRole("button", { name: /Appel fournisseur légitime/ }).click();
    await page.getByRole("button", { name: /Simuler/ }).click();

    // The clean call earns the Voice-Verified badge and the Ant Insurance stamp.
    await expect(page.getByText("Voice-Verified")).toBeVisible();
    await expect(page.getByText("Assuré par Ant Insurance")).toBeVisible({
      timeout: 30_000,
    });

    // ...and must never be flagged as fraud.
    await expect(page.getByText("Fraude détectée")).toHaveCount(0);
  });
});

import { test, expect } from "@playwright/test";

test("Add a tomato to cart and verify cart contents on mon-marche.fr", async ({
  page,
}) => {
  // Step 1: Go to the homepage
  await page.goto("https://www.mon-marche.fr");

  // Step 2: Add "La Tomate grappe sélection HVE" to the cart
  await page
    .locator(
      'article:has-text("La Tomate grappe sélection HVE") button:has-text("Ajouter le produit")'
    )
    .first()
    .click({ force: true });

  // Step 3: Open the cart (Mon panier)
  await page.getByRole("button", { name: "Mon panier" }).click({ force: true });

  // Step 4: Check that "La Tomate grappe sélection HVE" appears in the cart
  await expect(page.getByRole("dialog")).toContainText(
    "La Tomate grappe sélection HVE"
  );
});

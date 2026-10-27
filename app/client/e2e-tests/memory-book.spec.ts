import { expect, test } from "@playwright/test";

test.describe("دفتر الذكريات الخاص", () => {
  test("sets a password, keeps memories private, accepts photos, creates a read-only gift, and logs out", async ({ page, browser }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    let localPreview = true;
    await page.route("**/api/auth/status", async (route) => {
      const response = await route.fetch();
      const status = await response.json();
      await route.fulfill({
        response,
        json: { ...status, public_deployment: !localPreview },
      });
    });
    await page.goto("/");

    await expect(page).toHaveTitle(/دفتر الذكريات/);
    await expect(page.getByRole("heading", { name: "أنشئي كلمة سر لدفترك" })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
    await page.getByRole("button", { name: "التبديل إلى الإنجليزية" }).click();
    await expect(page.locator("html")).toHaveAttribute("lang", "en");
    await expect(page.locator("html")).toHaveAttribute("dir", "ltr");
    await expect(page.getByRole("heading", { name: "Create a password for your book" })).toBeVisible();
    await page.getByRole("button", { name: "Switch language to Arabic" }).click();
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
    await expect(page.getByText(/اختاري كلمة سر لا تقل عن 12 خانات/)).toBeVisible();
    await expect(page.locator("#password")).toHaveAttribute("minlength", "12");
    await expect(page.locator("#storage-footer")).toContainText("هذا الجهاز");
    await expect(page.getByRole("heading", { name: /هذه الصفحة ما زالت تنتظر/ })).toHaveCount(0);

    const privateBeforeLogin = await page.request.get("/api/memories");
    expect(privateBeforeLogin.status()).toBe(401);

    await page.locator("#password").fill("test-key-9284-abcd");
    await page.locator("#confirmation").fill("test-key-9284-abcd");
    await page.getByRole("button", { name: /إنشاء الدفتر/ }).click();
    await expect(page.getByRole("heading", { name: "مساحة لأيامك الجميلة" })).toBeVisible();
    await expect(page.getByText("هذه الصفحة ما زالت تنتظر حكايتها الأولى")).toBeVisible();

    await page.locator("#memory-title").fill("يوم على البحر");
    await page.locator("#memory-story").fill("ضحكنا طويلًا وجمعنا الأصداف قرب الماء.");
    await page.locator("#memory-date").fill("2025-08-16");
    await page.locator("#memory-photos").setInputFiles({
      name: "شاطئ.png",
      mimeType: "image/png",
      buffer: Buffer.from(
        "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAEklEQVR4nGOcFqDBwMDAxAAGAA1AARITnzTCAAAAAElFTkSuQmCC",
        "base64",
      ),
    });
    await page.getByRole("button", { name: /حفظ الذكرى/ }).click();
    await expect(page.getByRole("heading", { name: "يوم على البحر" })).toBeVisible();
    await expect(page.getByText("ضحكنا طويلًا وجمعنا الأصداف قرب الماء.")).toBeVisible();
    await expect(page.locator(".memory-card img")).toHaveCount(1);

    await page.getByText("تجهيز هدية للمشاركة").click();
    await expect(page.locator("#gift-share-password")).toHaveAttribute("minlength", "12");
    await page.locator("#gift-share-password").fill("gift-key-9284-abcd");
    await page.locator("#gift-share-confirmation").fill("gift-key-9284-abcd");
    await page.getByRole("button", { name: "إنشاء رابط الهدية" }).click();
    await expect(page.locator("#gift-settings-message")).toContainText("تم حفظ كلمة سر الهدية");
    await expect(page.locator("#gift-local-warning")).toBeVisible();
    await expect(page.locator("#gift-share-link")).toBeHidden();
    localPreview = false;
    await page.reload();
    await page.getByText("تجهيز هدية للمشاركة").click();
    await expect(page.locator("#gift-share-link")).toBeVisible();
    await expect(page.locator("#gift-url")).toHaveValue(/gift=1/);

    const recipientContext = await browser.newContext();
    const recipient = await recipientContext.newPage();
    await recipient.goto(await page.locator("#gift-url").inputValue());
    await expect(recipient.getByRole("heading", { name: "أعددتُ لك هذه الذكريات" })).toBeVisible();
    const giftBeforeUnlock = await recipient.request.get("/api/gift/memories");
    expect(giftBeforeUnlock.status()).toBe(401);
    await recipient.locator("#gift-password").fill("gift-key-9284-abcd");
    await recipient.getByRole("button", { name: /افتحي الهدية/ }).click();
    await expect(recipient.locator("#gift-content")).toBeVisible();
    await expect(recipient.getByRole("heading", { name: "يوم على البحر" })).toBeVisible();
    await expect(recipient.locator("#gift-memories-grid img")).toHaveCount(1);
    await expect(recipient.locator("#gift-memories-grid .delete-memory")).toBeHidden();
    await expect(recipient.locator("#memory-form")).toHaveCount(1);
    await expect(recipient.locator("#memory-form")).toBeHidden();
    const recipientCannotCreate = await recipient.request.post("/api/memories", {
      data: { title: "Not allowed", story: "Gift recipient" },
    });
    expect(recipientCannotCreate.status()).toBe(401);
    await recipient.getByRole("button", { name: "التبديل إلى الإنجليزية" }).click();
    await expect(recipient.locator("html")).toHaveAttribute("dir", "ltr");
    await expect(recipient.getByRole("heading", { name: "Your memories" })).toBeVisible();
    await recipientContext.close();

    page.once("dialog", (dialog) => dialog.accept());
    await page.getByRole("button", { name: "حذف هذه الذكرى" }).click();
    await expect(page.getByText("هذه الصفحة ما زالت تنتظر حكايتها الأولى")).toBeVisible();

    await page.getByRole("button", { name: /إغلاق الدفتر/ }).click();
    await expect(page.getByRole("heading", { name: "افتحي دفتر الذكريات" })).toBeVisible();
    const privateAfterLogout = await page.request.get("/api/memories");
    expect(privateAfterLogout.status()).toBe(401);

    await page.locator("#password").fill("incorrect-key");
    await page.getByRole("button", { name: /فتح الدفتر/ }).click();
    await expect(page.getByText("كلمة السر غير صحيحة.")).toBeVisible();
    await page.locator("#password").fill("test-key-9284-abcd");
    await page.getByRole("button", { name: /فتح الدفتر/ }).click();
    await expect(page.getByRole("heading", { name: "مساحة لأيامك الجميلة" })).toBeVisible();
    await expect(page.getByText("هذه الصفحة ما زالت تنتظر حكايتها الأولى")).toBeVisible();
  });
});

import { chromium } from "playwright";

const base = process.argv[2] || "http://localhost:4318";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

// study with many individuals -> Individuals tab
await page.goto(base + "/#/study/PKDB00252", { waitUntil: "networkidle" });
await page.waitForSelector(".markdown h1");
await page.click("text=Individuals");
await page.waitForSelector(".data-table");
await page.screenshot({ path: "/tmp/shot-individuals.png" });

// interventions tab on the sunitinib study
await page.goto(base + "/#/study/PKDB00249", { waitUntil: "networkidle" });
await page.waitForSelector(".markdown h1");
await page.click("text=Interventions");
await page.waitForTimeout(250);
await page.screenshot({ path: "/tmp/shot-interventions.png" });

await browser.close();
console.log("ok");

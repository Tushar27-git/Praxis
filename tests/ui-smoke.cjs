// Optional real-browser regression check: npm's playwright package is test-only.
const { chromium } = require("playwright");
const assert = require("node:assert/strict");
const fs = require("node:fs/promises");
const path = require("node:path");

(async () => {
  const output = path.resolve("output/playwright");
  await fs.mkdir(output, {recursive:true});
  const browser = await chromium.launch({channel:"msedge", headless:true});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1040},acceptDownloads:true});
    page.setDefaultTimeout(15000);
    page.setDefaultNavigationTimeout(15000);
    const errors=[];page.on("pageerror", error=>errors.push(error.message));
    page.on("dialog", dialog=>dialog.accept());
    await page.goto(process.env.LAB_URL || "http://127.0.0.1:8765");
    await page.getByRole("button",{name:"Try demo",exact:true}).click();
    await page.waitForFunction(()=>document.getElementById("image-title").textContent === "Synthetic practice layout");
    await page.getByRole("button",{name:"Preview plans",exact:true}).click();
    await page.waitForFunction(()=>document.getElementById("status").textContent.includes("Confirm the selected army"));
    await page.locator("#army-confirmed").check();
    await page.locator("#scene-confirmed").check();
    await page.getByRole("button",{name:"Preview plans",exact:true}).click();
    await page.waitForSelector(".candidate");
    assert.equal(await page.locator(".candidate").count(),3);
    assert.match(await page.locator("#plan-detail").innerText(),/7 × Electro Dragon/);
    await page.locator(".candidate").nth(1).click();
    assert.equal(await page.locator(".candidate").nth(1).getAttribute("aria-pressed"),"true");
    await page.screenshot({path:path.join(output,"plans-desktop.png"),fullPage:true});
    const downloadPromise=page.waitForEvent("download");
    await page.getByRole("button",{name:"Save session",exact:true}).click();
    const download=await downloadPromise;
    const saved=path.join(output,"scouting-session.json");await download.saveAs(saved);
    const content=JSON.parse(await fs.readFile(saved,"utf8"));
    assert.equal(content.annotations.length,9);assert.equal(content.army[0].count,7);
    await page.getByRole("tab",{name:"Army & map",exact:true}).click();
    await page.locator(".unit-options input").first().fill("6");
    assert.equal(await page.locator("#army-confirmed").isChecked(),false);
    assert.equal(await page.locator(".candidate").count(),0);
    await page.locator("#session-file").setInputFiles(saved);
    await page.waitForFunction(()=>document.querySelector(".unit-options input").value === "7");
    assert.equal(await page.locator("#army-confirmed").isChecked(),false);
    assert.equal(await page.locator("#scene-confirmed").isChecked(),false);
    // Draw/undo against the actual displayed image, including its letterbox.
    await page.locator("#draw-kind").selectOption("cannon");
    const b=await page.locator("#map").boundingBox();const scale=Math.min(b.width/1000,b.height/750);
    const ox=b.x+(b.width-1000*scale)/2,oy=b.y+(b.height-750*scale)/2;
    await page.mouse.move(ox+200*scale,oy+150*scale);await page.mouse.down();
    await page.mouse.move(ox+260*scale,oy+200*scale,{steps:5});await page.mouse.up();
    assert.equal(await page.locator("#mark-count").innerText(),"10 marks");
    await page.getByRole("button",{name:"Undo",exact:true}).click();
    assert.equal(await page.locator("#mark-count").innerText(),"9 marks");
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:path.join(output,"setup-mobile.png"),fullPage:true});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth > innerWidth),false);
    await page.setViewportSize({width:1440,height:1040});
    await page.screenshot({path:path.join(output,"setup-desktop.png"),fullPage:true});
    // Invalid drafts must not be exported as apparently recoverable sessions.
    await page.getByRole("button",{name:"+ Add unit",exact:true}).click();
    let invalidDownloads=0;const countDownload=()=>invalidDownloads++;
    page.on("download",countDownload);
    await page.getByRole("button",{name:"Save session",exact:true}).click();
    await page.waitForFunction(()=>/Cannot save session|Session exported/.test(document.getElementById("status").textContent));
    assert.match(await page.locator("#status").innerText(),/Cannot save session/);
    assert.equal(invalidDownloads,0);
    page.off("download",countDownload);
    await page.locator(".unit-title button").last().click();
    // Hold the real import request, edit during the wait, then continue it.
    let release, seen;const gate=new Promise(r=>release=r), observed=new Promise(r=>seen=r);
    await page.route("**/api/plan",async route=>{seen();await gate;await route.continue();});
    await page.locator("#session-file").setInputFiles(saved);
    await observed;
    await page.locator(".unit-options input").first().fill("4");
    release();
    await page.waitForFunction(()=>document.getElementById("status").textContent.startsWith("Load not applied:"));
    await page.waitForLoadState("networkidle");
    assert.equal(await page.locator(".unit-options input").first().inputValue(),"4","Pending import must not overwrite edits made while it was loading");
    await page.unroute("**/api/plan");
    // Edits while a save is being validated must not be marked as saved.
    let releaseSave, seenSave;
    const saveGate=new Promise(r=>releaseSave=r), saveObserved=new Promise(r=>seenSave=r);
    await page.route("**/api/plan",async route=>{seenSave();await saveGate;await route.continue();});
    page.on("download",countDownload);
    await page.getByRole("button",{name:"Save session",exact:true}).click();
    await saveObserved;
    await page.locator(".unit-options input").first().fill("5");
    releaseSave();
    await page.waitForFunction(()=>document.getElementById("status").textContent.startsWith("Cannot save session:"));
    assert.equal(invalidDownloads,0);
    page.off("download",countDownload);
    await page.unroute("**/api/plan");
    // Load a real raster file rather than relying only on the demo path.
    const raster=path.join(output,"demo-fixture.png");
    await fs.writeFile(raster,Buffer.from(content.image.data_url.split(",")[1],"base64"));
    await page.locator("#image-file").setInputFiles(raster);
    await page.waitForFunction(()=>document.getElementById("image-title").textContent === "demo-fixture.png");
    assert.equal(await page.locator("#mark-count").innerText(),"0 marks");
    assert.equal(await page.locator(".unit").count(),0);
    assert.deepEqual(errors,[]);
    console.log("Browser checks passed: demo, confirmations, candidate selection, session roundtrip, screenshot loading, stale-plan invalidation, drawing/undo, responsive layout, invalid-save rejection and pending-import/save edit protection.");
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});

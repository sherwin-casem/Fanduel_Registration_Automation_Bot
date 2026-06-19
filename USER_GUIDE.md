# 🚀 FanDuel AutoBot - Detailed User Guide

Welcome to the FanDuel AutoBot! This guide explains every button, tab, and feature in plain English so you can easily manage and run your accounts.

---

## 1. The Top Toolbar (Main Buttons)
At the very top of the application, you will find the main control buttons.

* **📁 Upload JSON**: Click this to load a list of accounts from a `.json` file. The accounts will be added to your current list.
* **📁 Upload Excel**: Click this to load accounts from an Excel file (`.xlsx` or `.xls`). 
  * *Tip for Excel*: Make sure your first row has headers like `First Name`, `Last Name`, `Email`, `Password`, `Address`, `City`, `State` (or `Province`), `Zip Code` (or `Postcode`), `Phone`, `Month`, `Day`, `Year`. The bot is smart and will automatically figure out what they mean!
* **➕ Add Account**: Opens a window where you can manually type in the details for a single new account.
* **⚙ Settings**: Opens the configuration menu (explained in Section 5 below).
* **▶ Run Pending**: Starts the automation bot. It will go through every account currently sitting in the "Pending" tab, one by one.
* **▶ Run Selected**: Starts the bot, but **only** for the specific accounts you have highlighted/clicked on in the list.
* **🛑 STOP EVERYTHING**: The emergency brake. If the bot is doing something wrong, click this button to immediately close the browser and stop the process.

---

## 2. The Tabs (Account Categories)
Below the toolbar, you will see several tabs. As the bot runs, it automatically moves accounts into these tabs based on what happened.

* **⏳ Pending**: Accounts that have not been run yet, or accounts that you want to try again.
* **🌟 Created**: Accounts that were successfully registered and the "Success" screen was reached.
* **❌ Failed**: Accounts where the bot encountered an error (e.g., a button wasn't found, or the page took too long to load).
* **⏭ Skipped**: Accounts that the bot skipped (usually because it detected the account already exists).
* **👥 Another Account**: Accounts where FanDuel displayed the "We found another account" warning.
* **⚠️ Service Unavailable**: Accounts where FanDuel displayed a "Service not available" error page.
* **❓ Unable to Verify**: Accounts where FanDuel said "We couldn't verify your data."

---

## 3. Managing Accounts (Inside the Tabs)
When you click on any tab, you will see a list of accounts and a control bar just above the list.

* **Filter by Date**: A dropdown menu that lets you view only the accounts that were run on a specific date. Great for daily reporting!
* **📥 Export JSON / CSV / Excel**: Click any of these buttons to download the current list of accounts you are looking at. If you have filtered by date, it will only export that specific date. Excel is usually the easiest to read!
* **🔄 Mark All & Send to Pending**: Found in the "Failed" or "Unable to Verify" tabs. Clicking this will take **every** account in that tab and send it back to the "Pending" tab so the bot can try them again.

---

## 4. The Right-Click Menu
If you **Right-Click** on any account in the list, a secret menu pops up with more options:

* **✏ Edit Account**: Opens a window to fix typos in the email, password, address, etc.
* **🗑 Delete Account**: Permanently deletes the account from your list.
* **▶ Run This Account**: Immediately starts the bot for just this one specific account.
* **🖼 View Screenshot**: The bot takes a picture of the screen right before it finishes an account. Click this to see exactly what the screen looked like (e.g., to see the exact error message). *Note: You can also just Double-Click an account to view its screenshot!*
* **🔄 Send to Pending**: Sends only the highlighted account(s) back to the Pending tab to be tried again.

---

## 5. The Settings Menu (⚙ Settings)
When you click the yellow Settings button, you will see three tabs:

* **General**: 
  * **Referral Mode**: Choose how the bot picks which referral link to use. You can have it rotate one-by-one, stick to one link for 60 minutes, mix them randomly, or use percentages.
  * **Edge Browser Path**: The location of Microsoft Edge on your computer. Usually, you don't need to touch this.
* **Referrals**: Paste your referral links here. Make sure to wrap them in double quotes! **When adding (appending) new links to your existing list, you MUST put a comma `,` after the previous one.** Example:
  ```
  "www.previous.com",
  "www.new-a.com",
  "www.new-b.com"
  ```
  *(Note: It is okay if you use square brackets `[]` around them, or paste them one per line, as long as the quotes and commas are there!)*
* **Proxies**: Paste your proxies here to hide your IP address. Wrap them in quotes as well. **Just like referrals, remember to add a comma `,` after the previous proxy when appending new ones.** Format: `"host:port:username:password"`. Example:
  ```
  "192.168.1.1:8080:myuser:mypassword",
  "192.168.1.2:8080:myuser:mypassword"
  ```

---

## 6. 🛑 VERY IMPORTANT: Rules for Running the Bot

1. **Running on Multiple Machines**: If you are running this program on different computers to create more accounts faster, **DO NOT use the same proxies on different machines!** Every single machine must have its own **unique** set of proxies. Sharing proxies across machines will cause the accounts to get flagged or banned.
2. **Hands Off!**: When you click "Run", the bot takes control of your mouse and keyboard. **Do not touch your mouse or type on your keyboard while the bot is working**, or you will interrupt it and cause it to fail.
3. **The Emergency Stop (Failsafe)**: If the bot goes crazy and you can't click the "STOP EVERYTHING" button, violently throw your real mouse cursor into any of the **four corners of your computer screen** (like the top-left corner). This triggers an emergency failsafe that crashes the bot instantly.
4. **Screen Setup**: Ensure the bot's image files (like `email1.png`, `create_account.png`) are kept in the exact same folder as the application, otherwise the bot won't know what to click on.
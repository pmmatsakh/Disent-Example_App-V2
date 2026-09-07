// JavaScript = BEHAVIOUR. This file makes the page do things.
//
// No framework, no bundler, no import statements — the browser runs this file
// exactly as written. Compare with the `vite react` row, where React manages
// the page and a build step compiles JSX. Here we talk to the DOM directly.

// --- 1. A counter -----------------------------------------------------------
// Find the button in index.html by its id, then run a function on each click.
// The "state" is just a variable; we update the button's text by hand. (This
// is precisely the work React's useState does for you.)

let count = 0;
const countBtn = document.getElementById("count-btn");

countBtn.addEventListener("click", () => {
  count += 1;
  countBtn.textContent = `clicked ${count} ${count === 1 ? "time" : "times"}`;
});

// --- 2. A theme toggle ------------------------------------------------------
// JavaScript doesn't set colours here. It toggles a CSS class on <body>, and
// styles.css decides what that class means. Keeping appearance in CSS and
// behaviour in JS is the separation this example is demonstrating.

const themeBtn = document.getElementById("theme-btn");

themeBtn.addEventListener("click", () => {
  document.body.classList.toggle("alt-accent");
});

// --- 3. Write the load time into the page -----------------------------------
// A small proof that this ran in your browser, just now — nothing was
// pre-rendered on a server.

document.getElementById("loaded-at").textContent =
  "this page ran JavaScript in your browser at " +
  new Date().toLocaleTimeString();

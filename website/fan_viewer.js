/**
 * McConigley Descendant Fan Viewer
 */
const SIBLINGS = ["Mary", "Mick", "Sean", "Norah", "Brigid", "Paddy", "Charlie", "Danny", "Tommy"];
let branchesData = {};
let currentSibling = "Mary";
let currentFile = "Mary.svg";
let pz = null;

const fanContainer = document.getElementById("fan-container");
const statusLabel = document.getElementById("status-label");
const viewport = document.getElementById("viewport");
const backBtn = document.getElementById("back-to-base");
const backLabel = document.getElementById("back-label");

async function init() {
  pz = new PanZoomEngine(viewport, fanContainer);

  try {
    const resp = await fetch("branches.json");
    branchesData = await resp.json();
    if (branchesData._meta) {
      if (branchesData._meta.parents) {
        document.querySelector("#ancestor-meta a").textContent = branchesData._meta.parents;
      }
      if (branchesData._meta.hub_url) {
        document.getElementById("hub-link").href = branchesData._meta.hub_url;
        document.querySelector("#ancestor-meta a").href = branchesData._meta.hub_url;
      }
    }
  } catch (e) {
    console.error("Could not load branches.json", e);
  }
  renderTabs();
  handleHash();
  window.addEventListener("hashchange", handleHash);
}

function renderTabs() {
  const container = document.getElementById("tabs");
  container.innerHTML = "";
  SIBLINGS.forEach(name => {
    const btn = document.createElement("button");
    btn.className = `tab-btn ${name === currentSibling ? "active" : ""}`;
    btn.textContent = name;
    btn.onclick = () => { location.hash = `#${name}`; };
    container.appendChild(btn);
  });
}

function renderPills() {
  const container = document.getElementById("pills");
  container.innerHTML = "";

  const isBaseActive = (currentFile === `${currentSibling}.svg`);
  const baseBtn = document.createElement("button");
  baseBtn.className = `pill-btn ${isBaseActive ? "active" : ""}`;
  baseBtn.textContent = `All ${currentSibling} (Base)`;
  baseBtn.onclick = () => { location.hash = `#${currentSibling}`; };
  container.appendChild(baseBtn);

  const subBranches = branchesData[currentSibling] || [];
  subBranches.forEach(b => {
    const branchKey = b.file.replace('.svg', '');
    const btn = document.createElement("button");
    btn.className = `pill-btn ${currentFile === b.file ? "active" : ""}`;
    btn.textContent = b.label;
    btn.onclick = () => { location.hash = `#${currentSibling}/${branchKey}`; };
    container.appendChild(btn);
  });

  if (!isBaseActive) {
    backLabel.textContent = `Back to All ${currentSibling}`;
    backBtn.style.display = "inline-flex";
  } else {
    backBtn.style.display = "none";
  }
}

function goBackToBase() {
  location.hash = `#${currentSibling}`;
}

function handleHash() {
  const rawHash = location.hash.replace("#", "");
  if (!rawHash) {
    switchChart("Mary", "Mary.svg", "Mary McConigley - Base Descendant Fan");
    return;
  }
  const parts = rawHash.split("/");
  const sib = parts[0];
  if (!SIBLINGS.includes(sib)) return;
  currentSibling = sib;

  if (parts.length > 1) {
    const fileKey = parts[1];
    const sub = (branchesData[sib] || []).find(b => b.file === `${fileKey}.svg` || b.file.replace('.svg', '') === fileKey);
    if (sub) {
      switchChart(sib, sub.file, `${sib} McConigley > ${sub.label}`);
    } else {
      switchChart(sib, `${sib}.svg`, `${sib} McConigley - Base Descendant Fan`);
    }
  } else {
    switchChart(sib, `${sib}.svg`, `${sib} McConigley - Base Descendant Fan`);
  }
}

async function switchChart(sibling, file, label) {
  currentSibling = sibling;
  currentFile = file;
  renderTabs();
  renderPills();
  statusLabel.textContent = label;

  try {
    const resp = await fetch(file);
    const svgText = await resp.text();
    fanContainer.innerHTML = svgText;
    attachBadgeListeners();
  } catch (err) {
    fanContainer.innerHTML = `<p style="color:red">Failed to load ${file}</p>`;
  }
}

function navigateToBranch(targetHash) {
  if (!targetHash) return;
  if (!targetHash.startsWith("#")) targetHash = `#${targetHash}`;
  location.hash = targetHash;
}

function attachBadgeListeners() {
  const badges = fanContainer.querySelectorAll(".fan-link, .fan-badge");
  badges.forEach(el => {
    el.addEventListener("mousedown", (e) => {
      e.stopPropagation();
    });

    el.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      const target = el.closest(".fan-link")?.getAttribute("data-branch") 
                  || el.closest(".fan-link")?.getAttribute("href")
                  || el.closest(".fan-link")?.getAttribute("xlink:href");
      if (target) navigateToBranch(target);
    });

    el.addEventListener("mouseup", (e) => {
      if (pz.dragDistance < 5) {
        const target = el.closest(".fan-link")?.getAttribute("data-branch") 
                    || el.closest(".fan-link")?.getAttribute("href")
                    || el.closest(".fan-link")?.getAttribute("xlink:href");
        if (target) {
          e.preventDefault();
          e.stopPropagation();
          navigateToBranch(target);
        }
      }
    });
  });
}

function zoom(delta) { if (pz) pz.zoom(delta); }
function resetTransform() { if (pz) pz.reset(); }

init();

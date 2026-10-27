/**
 * Hub and Spoke Wheel Generator & Navigation
 */
const SIBLINGS = [
  { num: 1, name: 'Mary', desc: 'Descendants', gender: 'f' },
  { num: 2, name: 'Mick', desc: 'Descendants', gender: 'm' },
  { num: 3, name: 'Sean', desc: 'Descendants', gender: 'm' },
  { num: 4, name: 'Norah', desc: 'Unitary (No Desc.)', gender: 'f', unitary: true },
  { num: 5, name: 'Brigid', desc: 'Descendants', gender: 'f' },
  { num: 6, name: 'Paddy', desc: 'Descendants', gender: 'm' },
  { num: 7, name: 'Charlie', desc: 'Descendants', gender: 'm' },
  { num: 8, name: 'Danny', desc: 'Descendants', gender: 'm' },
  { num: 9, name: 'Tommy', desc: 'Descendants', gender: 'm' }
];

let hubPz = null;
let ancestryPz = null;

function initAtlas() {
  const hubWrap = document.getElementById("hub-canvas-wrap");
  const hubStage = document.getElementById("hub-stage");
  hubPz = new PanZoomEngine(hubWrap, hubStage);

  const ancestryWrap = document.getElementById("ancestry-canvas-wrap");
  const ancestryStage = document.getElementById("ancestry-stage");
  ancestryPz = new PanZoomEngine(ancestryWrap, ancestryStage);

  buildHubNodes();
  bindNavigation();
  loadAncestrySvg();
}

function buildHubNodes() {
  const spokesLayer = document.getElementById("spokesLayer");
  const nodesLayer = document.getElementById("nodesLayer");
  const quickBar = document.getElementById("hub-quickbar");

  const CX = 550, CY = 550, ORBIT_R = 360, NODE_R = 72;
  const count = SIBLINGS.length;

  SIBLINGS.forEach((sib, i) => {
    // Top node (Mary) at -90deg, clockwise
    const angleDeg = -90 + (i * 360 / count);
    const rad = angleDeg * Math.PI / 180;
    const nx = CX + ORBIT_R * Math.cos(rad);
    const ny = CY + ORBIT_R * Math.sin(rad);

    // Spoke line
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", CX);
    line.setAttribute("y1", CY);
    line.setAttribute("x2", nx);
    line.setAttribute("y2", ny);
    line.setAttribute("stroke", "#374151");
    line.setAttribute("stroke-width", "3");
    line.setAttribute("stroke-dasharray", "6 6");
    spokesLayer.appendChild(line);

    // Node group
    const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
    group.setAttribute("style", "cursor: pointer;");

    let fillGrad = sib.unitary ? "url(#norahNode)" : (sib.gender === "f" ? "url(#roseNode)" : "url(#emeraldNode)");
    let strokeColor = sib.unitary ? "#a5b4fc" : (sib.gender === "f" ? "#fda4af" : "#6ee7b7");

    // Outer Circle
    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", nx);
    circle.setAttribute("cy", ny);
    circle.setAttribute("r", NODE_R);
    circle.setAttribute("fill", fillGrad);
    circle.setAttribute("stroke", strokeColor);
    circle.setAttribute("stroke-width", "4");
    circle.setAttribute("class", "child-circle");
    group.appendChild(circle);

    // Order Badge
    const badge = document.createElementNS("http://www.w3.org/2000/svg", "text");
    badge.setAttribute("x", nx);
    badge.setAttribute("y", ny - NODE_R + 10);
    badge.setAttribute("text-anchor", "middle");
    badge.setAttribute("fill", strokeColor);
    badge.setAttribute("font-size", "14");
    badge.setAttribute("font-weight", "700");
    badge.textContent = `#${sib.num}`;
    group.appendChild(badge);

    // Name
    const name = document.createElementNS("http://www.w3.org/2000/svg", "text");
    name.setAttribute("x", nx);
    name.setAttribute("y", ny + 2);
    name.setAttribute("text-anchor", "middle");
    name.setAttribute("fill", "#ffffff");
    name.setAttribute("font-family", "'Cinzel', serif");
    name.setAttribute("font-size", "22");
    name.setAttribute("font-weight", "700");
    name.textContent = sib.name.toUpperCase();
    group.appendChild(name);

    // Action pill
    const desc = document.createElementNS("http://www.w3.org/2000/svg", "text");
    desc.setAttribute("x", nx);
    desc.setAttribute("y", ny + 32);
    desc.setAttribute("text-anchor", "middle");
    desc.setAttribute("fill", strokeColor);
    desc.setAttribute("font-size", "12");
    desc.setAttribute("font-weight", "600");
    desc.textContent = sib.desc;
    group.appendChild(desc);

    // DIRECT ROUTING TO FAN CHARTS
    group.onclick = () => {
      window.location.href = `index.html#${sib.name}`;
    };

    nodesLayer.appendChild(group);

    // Quickbar Pill
    const pill = document.createElement("button");
    pill.className = "sibling-pill";
    pill.textContent = `${sib.num}. ${sib.name}`;
    pill.onclick = () => { window.location.href = `index.html#${sib.name}`; };
    quickBar.appendChild(pill);
  });
}

function bindNavigation() {
  const tabHub = document.getElementById("tabHub");
  const tabAncestry = document.getElementById("tabAncestry");
  const screenHub = document.getElementById("screen-hub");
  const screenAncestry = document.getElementById("screen-ancestry");

  tabHub.onclick = () => {
    tabHub.classList.add("active");
    tabAncestry.classList.remove("active");
    screenHub.classList.add("active");
    screenAncestry.classList.remove("active");
  };

  tabAncestry.onclick = () => {
    tabAncestry.classList.add("active");
    tabHub.classList.remove("active");
    screenAncestry.classList.add("active");
    screenHub.classList.remove("active");
  };

  document.getElementById("hubCenter").onclick = () => {
    tabAncestry.click();
  };
}

async function loadAncestrySvg() {
  try {
    const resp = await fetch("Ancestry.svg");
    const svg = await resp.text();
    document.getElementById("ancestry-stage").innerHTML = svg;
  } catch (e) {
    console.error("Could not load Ancestry.svg", e);
  }
}

initAtlas();

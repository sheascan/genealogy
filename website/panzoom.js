/**
 * PanZoomEngine - Lightweight, robust pan & zoom handler
 */
class PanZoomEngine {
  constructor(viewportEl, stageEl, onUpdate = null) {
    this.viewport = viewportEl;
    this.stage = stageEl;
    this.onUpdate = onUpdate;
    this.scale = 1;
    this.panX = 0;
    this.panY = 0;
    this.isDragging = false;
    this.startX = 0;
    this.startY = 0;
    this.dragDistance = 0;

    this.initEvents();
  }

  apply() {
    this.stage.style.transform = `translate(${this.panX}px, ${this.panY}px) scale(${this.scale})`;
    if (this.onUpdate) this.onUpdate(this.scale, this.panX, this.panY);
  }

  zoom(delta) {
    this.scale = Math.min(Math.max(0.4, this.scale + delta), 4.0);
    this.apply();
  }

  reset() {
    this.scale = 1;
    this.panX = 0;
    this.panY = 0;
    this.apply();
  }

  initEvents() {
    this.viewport.addEventListener("wheel", (e) => {
      e.preventDefault();
      const delta = e.deltaY < 0 ? 0.08 : -0.08;
      this.scale = Math.min(Math.max(0.4, this.scale + delta), 4.0);
      this.apply();
    }, { passive: false });

    this.viewport.addEventListener("mousedown", (e) => {
      if (e.target.closest("button, a, .fan-link, .fan-badge, .sibling-node, .hub-center-btn")) {
        return;
      }
      this.isDragging = true;
      this.dragDistance = 0;
      this.startX = e.clientX - this.panX;
      this.startY = e.clientY - this.panY;
    });

    window.addEventListener("mousemove", (e) => {
      if (!this.isDragging) return;
      this.dragDistance += Math.abs(e.movementX) + Math.abs(e.movementY);
      this.panX = e.clientX - this.startX;
      this.panY = e.clientY - this.startY;
      this.apply();
    });

    window.addEventListener("mouseup", () => {
      this.isDragging = false;
    });
  }
}

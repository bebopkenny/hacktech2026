import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.164/build/three.module.js";

const COLORS = {
  wall:   0x778899,
  door:   0xc8a96e,
  column: 0x6eaec8,
  floor:  0x556b55,
  conflict: 0xff4444,
  normal: null,  // filled per-element at creation
};

const _scene     = new THREE.Scene();
const _meshById  = new Map();  // element_id → { mesh, baseColor }
let   _renderer, _camera;

export function initScene() {
  _renderer = new THREE.WebGLRenderer({ antialias: true });
  _renderer.setSize(innerWidth, innerHeight);
  _renderer.setPixelRatio(devicePixelRatio);
  document.body.appendChild(_renderer.domElement);

  _scene.background = new THREE.Color(0x111318);

  _camera = new THREE.PerspectiveCamera(45, innerWidth / innerHeight, 0.1, 1000);
  _camera.position.set(0, 18, 28);
  _camera.lookAt(0, 0, 0);

  _scene.add(new THREE.AmbientLight(0xffffff, 0.5));
  const sun = new THREE.DirectionalLight(0xffffff, 1.2);
  sun.position.set(8, 16, 8);
  _scene.add(sun);

  // Floor plate
  _scene.add(new THREE.Mesh(
    new THREE.BoxGeometry(22, 0.15, 16),
    new THREE.MeshStandardMaterial({ color: 0x223344, roughness: 0.9 })
  ));

  // Seed some labelled elements the conflict detector will reference.
  _addElement(100, "Walls",   new THREE.BoxGeometry(0.3, 3.2, 10), [-7, 1.6, 0],  COLORS.wall);
  _addElement(101, "Walls",   new THREE.BoxGeometry(0.3, 3.2, 10), [ 7, 1.6, 0],  COLORS.wall);
  _addElement(102, "Walls",   new THREE.BoxGeometry(10, 3.2, 0.3), [0, 1.6, -6],  COLORS.wall);
  _addElement(200, "Doors",   new THREE.BoxGeometry(0.35, 2.4, 1.2), [-7, 1.2, 2], COLORS.door);
  _addElement(300, "Structural Columns", new THREE.BoxGeometry(0.6, 3.5, 0.6), [4, 1.75, 3], COLORS.column);
  _addElement(301, "Structural Columns", new THREE.BoxGeometry(0.6, 3.5, 0.6), [-4, 1.75, -3], COLORS.column);

  function animate() {
    requestAnimationFrame(animate);
    _scene.rotation.y += 0.0015;
    _renderer.render(_scene, _camera);
  }
  animate();

  window.addEventListener("resize", () => {
    _camera.aspect = innerWidth / innerHeight;
    _camera.updateProjectionMatrix();
    _renderer.setSize(innerWidth, innerHeight);
  });
}

function _addElement(id, _category, geometry, position, color) {
  const mesh = new THREE.Mesh(
    geometry,
    new THREE.MeshStandardMaterial({ color, roughness: 0.7 })
  );
  mesh.position.set(...position);
  _scene.add(mesh);
  _meshById.set(id, { mesh, baseColor: color });
}

/**
 * Flash conflicting elements red for `duration` ms then restore their base color.
 * Called by ws_client.js when a conflict arrives.
 */
export function highlightConflict(elementIds, duration = 4000) {
  const restored = [];

  for (const id of elementIds) {
    const entry = _meshById.get(id);
    if (!entry) continue;
    entry.mesh.material.color.setHex(COLORS.conflict);
    entry.mesh.material.emissive.setHex(0x550000);
    restored.push(entry);
  }

  setTimeout(() => {
    for (const entry of restored) {
      entry.mesh.material.color.setHex(entry.baseColor);
      entry.mesh.material.emissive.setHex(0x000000);
    }
  }, duration);
}

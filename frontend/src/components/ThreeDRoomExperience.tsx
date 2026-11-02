import { useEffect, useRef, useState, useCallback } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

export interface ThreeDRoomExperienceProps {
  onOptimizeClick?: () => void
  onExploreFeaturesClick?: () => void
  currentSection?: number
}

// 5 Discrete Assembly Stages
export type AssemblyStage = 1 | 2 | 3 | 4 | 5

interface StageInfo {
  stage: AssemblyStage
  number: string
  title: string
  subtitle: string
  cameraTarget: [number, number, number]
  cameraPos: [number, number, number]
}

const STAGE_CONFIG: Record<AssemblyStage, StageInfo> = {
  1: {
    stage: 1,
    number: '01',
    title: 'Architectural Foundation',
    subtitle: 'Podium slab & cutaway envelope assemble',
    cameraPos: [6.8, 5.8, 7.5],
    cameraTarget: [0, 0.4, 0],
  },
  2: {
    stage: 2,
    number: '02',
    title: 'Minimalist Bed Suite',
    subtitle: 'Oak platform, mattress, pillows & duvet dock into position',
    cameraPos: [5.2, 4.4, 6.2],
    cameraTarget: [0.2, 0.6, -0.6],
  },
  3: {
    stage: 3,
    number: '03',
    title: 'Scandinavian Storage',
    subtitle: 'Full-height fluted wardrobe & sliding panels lock onto right wall',
    cameraPos: [4.8, 4.8, 6.8],
    cameraTarget: [1.2, 1.0, -0.4],
  },
  4: {
    stage: 4,
    number: '04',
    title: 'Ergonomic Workspace',
    subtitle: 'Oak desk, wishbone chair & bedside nightstand assemble',
    cameraPos: [5.6, 4.2, 5.8],
    cameraTarget: [-0.6, 0.8, 0.2],
  },
  5: {
    stage: 5,
    number: '05',
    title: 'Full Staging & Ambience',
    subtitle: 'Warm ambient glow, directional sunlight, plants & reflections settle',
    cameraPos: [5.8, 4.2, 6.2],
    cameraTarget: [0, 0.8, 0],
  },
}

export function ThreeDRoomExperience() {
  const mountRef = useRef<HTMLDivElement>(null)
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null)
  const sceneRef = useRef<THREE.Scene | null>(null)
  const controlsRef = useRef<OrbitControls | null>(null)
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null)
  const animFrameRef = useRef<number>(0)

  // 1. WebGL Support detection initialized lazily
  const [webglSupported] = useState<boolean>(() => {
    if (typeof window === 'undefined') return true
    try {
      const canvas = document.createElement('canvas')
      return Boolean(canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
    } catch {
      return false
    }
  })

  // Stage state
  const [activeStage, setActiveStage] = useState<AssemblyStage>(5)
  const [isPlaying, setIsPlaying] = useState<boolean>(true)
  const [isOrbitingUser, setIsOrbitingUser] = useState<boolean>(false)

  // Animated targets & groups
  const targetProgressRef = useRef<number>(1.0)
  const currentProgressRef = useRef<number>(1.0)
  const isPlayingRef = useRef<boolean>(true)

  useEffect(() => {
    isPlayingRef.current = isPlaying
  }, [isPlaying])

  // Modular assembly groups in the scene
  const foundationGroupRef = useRef<THREE.Group | null>(null)
  const bedGroupRef = useRef<THREE.Group | null>(null)
  const wardrobeGroupRef = useRef<THREE.Group | null>(null)
  const workspaceGroupRef = useRef<THREE.Group | null>(null)
  const decorGroupRef = useRef<THREE.Group | null>(null)
  const lightingGroupRef = useRef<THREE.Group | null>(null)
  const sunLightRef = useRef<THREE.DirectionalLight | null>(null)
  const pointLightBedRef = useRef<THREE.PointLight | null>(null)
  const pointLightDeskRef = useRef<THREE.PointLight | null>(null)

  // Smooth easing helper
  const easeOutCubic = (x: number): number => 1 - Math.pow(1 - Math.max(0, Math.min(1, x)), 3)
  const easeInOutQuad = (x: number): number =>
    x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2

  // Jump to specific stage
  const goToStage = useCallback((stage: AssemblyStage) => {
    setActiveStage(stage)
    const p = (stage - 1) / 4 // 1->0.0, 2->0.25, 3->0.50, 4->0.75, 5->1.0
    targetProgressRef.current = p
  }, [])

  // Auto-play timeline loop
  useEffect(() => {
    if (!isPlaying) return
    const interval = setInterval(() => {
      setActiveStage(prev => {
        const next = (prev === 5 ? 1 : ((prev + 1) as AssemblyStage))
        const p = (next - 1) / 4
        targetProgressRef.current = p
        return next
      })
    }, 4500)
    return () => clearInterval(interval)
  }, [isPlaying])

  // Initialize Three.js Scene
  useEffect(() => {
    const container = mountRef.current
    if (!container || !webglSupported) return

    const width = container.clientWidth || 640
    const height = container.clientHeight || 520

    // 2. Scene
    const scene = new THREE.Scene()
    sceneRef.current = scene

    // 3. Camera
    const camera = new THREE.PerspectiveCamera(38, width / height, 0.1, 100)
    camera.position.set(5.8, 4.2, 6.2)
    cameraRef.current = camera

    // 4. Renderer
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance',
    })
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
    renderer.shadowMap.enabled = true
    renderer.shadowMap.type = THREE.PCFSoftShadowMap
    renderer.toneMapping = THREE.ACESFilmicToneMapping
    renderer.toneMappingExposure = 1.05
    rendererRef.current = renderer

    container.innerHTML = ''
    container.appendChild(renderer.domElement)

    // 5. Controls
    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.dampingFactor = 0.05
    controls.maxPolarAngle = Math.PI / 2 - 0.05 // Don't flip below floor
    controls.minDistance = 3.5
    controls.maxDistance = 15.0
    controls.target.set(0, 0.8, 0)
    controlsRef.current = controls

    controls.addEventListener('start', () => setIsOrbitingUser(true))
    controls.addEventListener('end', () => {
      // Keep state readable
      setTimeout(() => setIsOrbitingUser(false), 2000)
    })

    // ── PBR Material Palette ───────────────────────────────────────
    // Warm Ivory, Scandinavian Oak, Terracotta, Sage, and Brass
    const wallMat = new THREE.MeshStandardMaterial({
      color: 0xf6f2ea,
      roughness: 0.9,
      metalness: 0.0,
    })
    const floorMat = new THREE.MeshStandardMaterial({
      color: 0xd9c5a8,
      roughness: 0.42,
      metalness: 0.05,
    })
    const oakMat = new THREE.MeshStandardMaterial({
      color: 0xb99672,
      roughness: 0.52,
      metalness: 0.03,
    })
    const oakDarkMat = new THREE.MeshStandardMaterial({
      color: 0x8c6b4d,
      roughness: 0.58,
      metalness: 0.05,
    })
    const fabricMat = new THREE.MeshStandardMaterial({
      color: 0xf1ece4,
      roughness: 0.92,
      metalness: 0.0,
    })
    const sageMat = new THREE.MeshStandardMaterial({
      color: 0x73846d,
      roughness: 0.78,
      metalness: 0.0,
    })
    const terracottaMat = new THREE.MeshStandardMaterial({
      color: 0xb98260,
      roughness: 0.75,
      metalness: 0.0,
    })
    const blackMetalMat = new THREE.MeshStandardMaterial({
      color: 0x222624,
      roughness: 0.35,
      metalness: 0.8,
    })
    const brassMat = new THREE.MeshStandardMaterial({
      color: 0xd1b066,
      roughness: 0.3,
      metalness: 0.85,
    })
    const foliageMat = new THREE.MeshStandardMaterial({
      color: 0x415b49,
      roughness: 0.65,
      metalness: 0.0,
    })
    const glassMat = new THREE.MeshStandardMaterial({
      color: 0xdaf0f7,
      roughness: 0.1,
      metalness: 0.1,
      transparent: true,
      opacity: 0.35,
    })

    // ── STAGE 1: FOUNDATION GROUP ──────────────────────────────────
    const foundationGroup = new THREE.Group()
    foundationGroupRef.current = foundationGroup
    scene.add(foundationGroup)

    // Floor slab (podium)
    const floorGeo = new THREE.BoxGeometry(4.6, 0.16, 5.0)
    const floorMesh = new THREE.Mesh(floorGeo, floorMat)
    floorMesh.position.set(0, -0.08, 0)
    floorMesh.receiveShadow = true
    foundationGroup.add(floorMesh)

    // Plinth base under floor (dark architectural outline)
    const plinthGeo = new THREE.BoxGeometry(4.7, 0.06, 5.1)
    const plinthMat = new THREE.MeshStandardMaterial({ color: 0x26372f, roughness: 0.8 })
    const plinthMesh = new THREE.Mesh(plinthGeo, plinthMat)
    plinthMesh.position.set(0, -0.19, 0)
    foundationGroup.add(plinthMesh)

    // Back Wall (Z = -2.5) with window cutout
    // We construct 3 wall pieces to create a real architectural window
    const backWallLeftGeo = new THREE.BoxGeometry(1.2, 2.7, 0.14)
    const backWallLeft = new THREE.Mesh(backWallLeftGeo, wallMat)
    backWallLeft.position.set(-1.7, 1.27, -2.43)
    backWallLeft.receiveShadow = true
    backWallLeft.castShadow = true
    foundationGroup.add(backWallLeft)

    const backWallRightGeo = new THREE.BoxGeometry(2.0, 2.7, 0.14)
    const backWallRight = new THREE.Mesh(backWallRightGeo, wallMat)
    backWallRight.position.set(1.3, 1.27, -2.43)
    backWallRight.receiveShadow = true
    backWallRight.castShadow = true
    foundationGroup.add(backWallRight)

    const backWallTopGeo = new THREE.BoxGeometry(1.4, 0.7, 0.14)
    const backWallTop = new THREE.Mesh(backWallTopGeo, wallMat)
    backWallTop.position.set(-0.4, 2.27, -2.43)
    foundationGroup.add(backWallTop)

    const backWallBottomGeo = new THREE.BoxGeometry(1.4, 0.7, 0.14)
    const backWallBottom = new THREE.Mesh(backWallBottomGeo, wallMat)
    backWallBottom.position.set(-0.4, 0.27, -2.43)
    foundationGroup.add(backWallBottom)

    // Architectural window frame & glass pane
    const winFrameGeo = new THREE.BoxGeometry(1.42, 1.34, 0.08)
    const winFrame = new THREE.Mesh(winFrameGeo, oakDarkMat)
    winFrame.position.set(-0.4, 1.28, -2.42)
    foundationGroup.add(winFrame)

    const winGlassGeo = new THREE.PlaneGeometry(1.32, 1.24)
    const winGlass = new THREE.Mesh(winGlassGeo, glassMat)
    winGlass.position.set(-0.4, 1.28, -2.38)
    foundationGroup.add(winGlass)

    // Left Wall (cutaway diorama style)
    const leftWallGeo = new THREE.BoxGeometry(0.14, 2.7, 4.86)
    const leftWall = new THREE.Mesh(leftWallGeo, wallMat)
    leftWall.position.set(-2.23, 1.27, -0.07)
    leftWall.receiveShadow = true
    leftWall.castShadow = true
    foundationGroup.add(leftWall)

    // Sleek architectural skirting boards
    const skirtGeoBack = new THREE.BoxGeometry(4.4, 0.08, 0.04)
    const skirtMat = new THREE.MeshStandardMaterial({ color: 0x45564c, roughness: 0.6 })
    const skirtBack = new THREE.Mesh(skirtGeoBack, skirtMat)
    skirtBack.position.set(0, 0.04, -2.34)
    foundationGroup.add(skirtBack)

    const skirtGeoLeft = new THREE.BoxGeometry(0.04, 0.08, 4.8)
    const skirtLeft = new THREE.Mesh(skirtGeoLeft, skirtMat)
    skirtLeft.position.set(-2.14, 0.04, -0.1)
    foundationGroup.add(skirtLeft)

    // ── STAGE 2: BED ASSEMBLY GROUP ────────────────────────────────
    const bedGroup = new THREE.Group()
    bedGroupRef.current = bedGroup
    scene.add(bedGroup)

    // Low Platform Bed Frame
    const bedFrameGeo = new THREE.BoxGeometry(1.76, 0.22, 2.1)
    const bedFrame = new THREE.Mesh(bedFrameGeo, oakMat)
    bedFrame.position.set(0.15, 0.11, -1.2)
    bedFrame.castShadow = true
    bedFrame.receiveShadow = true
    bedGroup.add(bedFrame)

    // Fluted Headboard
    const headboardGeo = new THREE.BoxGeometry(1.88, 0.95, 0.1)
    const headboard = new THREE.Mesh(headboardGeo, oakMat)
    headboard.position.set(0.15, 0.48, -2.28)
    headboard.castShadow = true
    headboard.receiveShadow = true
    bedGroup.add(headboard)

    // Plush Mattress
    const mattressGeo = new THREE.BoxGeometry(1.62, 0.24, 1.95)
    const mattress = new THREE.Mesh(mattressGeo, fabricMat)
    mattress.position.set(0.15, 0.34, -1.18)
    mattress.castShadow = true
    mattress.receiveShadow = true
    bedGroup.add(mattress)

    // Layered Pillows
    const pillowGeo = new THREE.BoxGeometry(0.68, 0.14, 0.44)
    const pillow1 = new THREE.Mesh(pillowGeo, fabricMat)
    pillow1.position.set(-0.35, 0.49, -1.82)
    pillow1.rotation.x = 0.2
    pillow1.castShadow = true
    bedGroup.add(pillow1)

    const pillow2 = new THREE.Mesh(pillowGeo, fabricMat)
    pillow2.position.set(0.65, 0.49, -1.82)
    pillow2.rotation.x = 0.2
    pillow2.castShadow = true
    bedGroup.add(pillow2)

    // Accent Pillows (Sage Green)
    const accentPillowGeo = new THREE.BoxGeometry(0.45, 0.12, 0.35)
    const accPillow1 = new THREE.Mesh(accentPillowGeo, sageMat)
    accPillow1.position.set(-0.35, 0.54, -1.68)
    accPillow1.rotation.x = 0.25
    accPillow1.castShadow = true
    bedGroup.add(accPillow1)

    const accPillow2 = new THREE.Mesh(accentPillowGeo, sageMat)
    accPillow2.position.set(0.65, 0.54, -1.68)
    accPillow2.rotation.x = 0.25
    accPillow2.castShadow = true
    bedGroup.add(accPillow2)

    // Folded Terracotta Duvet / Throw Blanket
    const duvetGeo = new THREE.BoxGeometry(1.64, 0.1, 1.05)
    const duvet = new THREE.Mesh(duvetGeo, terracottaMat)
    duvet.position.set(0.15, 0.44, -0.7)
    duvet.castShadow = true
    bedGroup.add(duvet)

    // ── STAGE 3: WARDROBE ASSEMBLY GROUP ───────────────────────────
    const wardrobeGroup = new THREE.Group()
    wardrobeGroupRef.current = wardrobeGroup
    scene.add(wardrobeGroup)

    // Main Tall Wardrobe Carcass along Right Wall
    const wardrobeCarcassGeo = new THREE.BoxGeometry(0.65, 2.35, 1.85)
    const wardrobeMat = new THREE.MeshStandardMaterial({
      color: 0xeee8dd,
      roughness: 0.65,
      metalness: 0.02,
    })
    const wardrobeCarcass = new THREE.Mesh(wardrobeCarcassGeo, wardrobeMat)
    wardrobeCarcass.position.set(1.9, 1.18, -0.9)
    wardrobeCarcass.castShadow = true
    wardrobeCarcass.receiveShadow = true
    wardrobeGroup.add(wardrobeCarcass)

    // Wardrobe Door Seams & Brass Handles
    const handleGeo = new THREE.CylinderGeometry(0.012, 0.012, 0.32, 12)
    const handle1 = new THREE.Mesh(handleGeo, brassMat)
    handle1.position.set(1.56, 1.15, -1.1)
    wardrobeGroup.add(handle1)

    const handle2 = new THREE.Mesh(handleGeo, brassMat)
    handle2.position.set(1.56, 1.15, -0.7)
    wardrobeGroup.add(handle2)

    // Top oak detail trim
    const trimGeo = new THREE.BoxGeometry(0.68, 0.04, 1.88)
    const trimMesh = new THREE.Mesh(trimGeo, oakMat)
    trimMesh.position.set(1.9, 2.37, -0.9)
    wardrobeGroup.add(trimMesh)

    // ── STAGE 4: WORKSPACE ASSEMBLY GROUP ──────────────────────────
    const workspaceGroup = new THREE.Group()
    workspaceGroupRef.current = workspaceGroup
    scene.add(workspaceGroup)

    // Desk Tabletop (Natural Timber)
    const deskTopGeo = new THREE.BoxGeometry(0.65, 0.05, 1.25)
    const deskTop = new THREE.Mesh(deskTopGeo, oakMat)
    deskTop.position.set(-1.75, 0.74, 0.75)
    deskTop.castShadow = true
    deskTop.receiveShadow = true
    workspaceGroup.add(deskTop)

    // Minimalist Hairpin Metal Legs
    const legGeo = new THREE.CylinderGeometry(0.018, 0.014, 0.72, 12)
    const legPositions: [number, number, number][] = [
      [-2.0, 0.36, 0.2],
      [-1.5, 0.36, 0.2],
      [-2.0, 0.36, 1.3],
      [-1.5, 0.36, 1.3],
    ]
    legPositions.forEach(([lx, ly, lz]) => {
      const leg = new THREE.Mesh(legGeo, blackMetalMat)
      leg.position.set(lx, ly, lz)
      leg.castShadow = true
      workspaceGroup.add(leg)
    })

    // Minimalist Work Accessories (Laptop & Brass Lamp)
    const laptopBaseGeo = new THREE.BoxGeometry(0.24, 0.01, 0.32)
    const laptopBase = new THREE.Mesh(laptopBaseGeo, blackMetalMat)
    laptopBase.position.set(-1.75, 0.77, 0.75)
    workspaceGroup.add(laptopBase)

    const laptopScreenGeo = new THREE.BoxGeometry(0.01, 0.22, 0.32)
    const laptopScreen = new THREE.Mesh(laptopScreenGeo, blackMetalMat)
    laptopScreen.position.set(-1.86, 0.88, 0.75)
    laptopScreen.rotation.z = -0.15
    workspaceGroup.add(laptopScreen)

    // Desk Lamp Base & Shade
    const deskLampBaseGeo = new THREE.CylinderGeometry(0.07, 0.07, 0.02, 16)
    const deskLampBase = new THREE.Mesh(deskLampBaseGeo, brassMat)
    deskLampBase.position.set(-1.75, 0.77, 1.22)
    workspaceGroup.add(deskLampBase)

    const deskLampStemGeo = new THREE.CylinderGeometry(0.008, 0.008, 0.35, 12)
    const deskLampStem = new THREE.Mesh(deskLampStemGeo, brassMat)
    deskLampStem.position.set(-1.75, 0.94, 1.22)
    workspaceGroup.add(deskLampStem)

    const deskLampShadeGeo = new THREE.ConeGeometry(0.08, 0.12, 16)
    const deskLampShade = new THREE.Mesh(deskLampShadeGeo, brassMat)
    deskLampShade.position.set(-1.72, 1.1, 1.18)
    deskLampShade.rotation.z = 0.5
    workspaceGroup.add(deskLampShade)

    // Ergonomic Chair (Wishbone/Scandi style)
    const chairGroup = new THREE.Group()
    chairGroup.position.set(-1.18, 0, 0.75)
    chairGroup.rotation.y = -Math.PI / 2 + 0.15

    const seatGeo = new THREE.BoxGeometry(0.42, 0.04, 0.42)
    const seatMesh = new THREE.Mesh(seatGeo, oakMat)
    seatMesh.position.set(0, 0.46, 0)
    seatMesh.castShadow = true
    chairGroup.add(seatMesh)

    const backrestGeo = new THREE.CylinderGeometry(0.24, 0.24, 0.04, 16, 1, false, 0, Math.PI)
    const backrest = new THREE.Mesh(backrestGeo, oakMat)
    backrest.position.set(0, 0.76, 0.18)
    backrest.rotation.x = Math.PI / 2
    backrest.castShadow = true
    chairGroup.add(backrest)

    // 4 Chair Legs
    const chairLegGeo = new THREE.CylinderGeometry(0.016, 0.012, 0.46, 12)
    const chairLegCoords = [
      [-0.18, 0.23, -0.18],
      [0.18, 0.23, -0.18],
      [-0.18, 0.23, 0.18],
      [0.18, 0.23, 0.18],
    ]
    chairLegCoords.forEach(([cx, cy, cz]) => {
      const cl = new THREE.Mesh(chairLegGeo, blackMetalMat)
      cl.position.set(cx, cy, cz)
      cl.castShadow = true
      chairGroup.add(cl)
    })
    workspaceGroup.add(chairGroup)

    // Bedside Nightstand (Left of bed)
    const nightstandGeo = new THREE.BoxGeometry(0.44, 0.45, 0.42)
    const nightstand = new THREE.Mesh(nightstandGeo, oakMat)
    nightstand.position.set(-0.96, 0.22, -2.15)
    nightstand.castShadow = true
    nightstand.receiveShadow = true
    workspaceGroup.add(nightstand)

    // Bedside Ceramic Lamp
    const lampBaseGeo = new THREE.CylinderGeometry(0.08, 0.11, 0.18, 16)
    const lampBase = new THREE.Mesh(lampBaseGeo, terracottaMat)
    lampBase.position.set(-0.96, 0.54, -2.15)
    lampBase.castShadow = true
    workspaceGroup.add(lampBase)

    const lampShadeGeo = new THREE.CylinderGeometry(0.12, 0.15, 0.18, 16)
    const lampShade = new THREE.Mesh(lampShadeGeo, fabricMat)
    lampShade.position.set(-0.96, 0.72, -2.15)
    lampShade.castShadow = true
    workspaceGroup.add(lampShade)

    // ── STAGE 5: DECOR & LIGHTING GROUP ────────────────────────────
    const decorGroup = new THREE.Group()
    decorGroupRef.current = decorGroup
    scene.add(decorGroup)

    // Potted Architectural Fiddle-Leaf Fig
    const potGeo = new THREE.CylinderGeometry(0.2, 0.16, 0.4, 20)
    const pot = new THREE.Mesh(potGeo, terracottaMat)
    pot.position.set(-1.85, 0.2, -1.9)
    pot.castShadow = true
    decorGroup.add(pot)

    // Foliage leaves (multiple spheres/cones clustered)
    const leafGeo = new THREE.SphereGeometry(0.24, 12, 12)
    const leafCluster1 = new THREE.Mesh(leafGeo, foliageMat)
    leafCluster1.position.set(-1.85, 0.55, -1.9)
    leafCluster1.scale.set(1.0, 1.4, 0.8)
    leafCluster1.castShadow = true
    decorGroup.add(leafCluster1)

    const leafCluster2 = new THREE.Mesh(leafGeo, foliageMat)
    leafCluster2.position.set(-1.75, 0.8, -1.85)
    leafCluster2.scale.set(0.8, 1.2, 0.7)
    leafCluster2.castShadow = true
    decorGroup.add(leafCluster2)

    // Framed Architectural Wall Art (Line Art)
    const artFrameGeo = new THREE.BoxGeometry(0.9, 1.1, 0.03)
    const artFrame = new THREE.Mesh(artFrameGeo, oakDarkMat)
    artFrame.position.set(0.15, 1.72, -2.35)
    decorGroup.add(artFrame)

    const artCanvasGeo = new THREE.PlaneGeometry(0.82, 1.02)
    const artCanvasMat = new THREE.MeshStandardMaterial({
      color: 0xf4ede2,
      roughness: 0.9,
    })
    const artCanvas = new THREE.Mesh(artCanvasGeo, artCanvasMat)
    artCanvas.position.set(0.15, 1.72, -2.33)
    decorGroup.add(artCanvas)

    // Cozy Woven Rug under bed foot
    const rugGeo = new THREE.BoxGeometry(2.4, 0.02, 1.8)
    const rugMat = new THREE.MeshStandardMaterial({
      color: 0xe6ded2,
      roughness: 0.95,
    })
    const rug = new THREE.Mesh(rugGeo, rugMat)
    rug.position.set(0.15, 0.01, -0.4)
    rug.receiveShadow = true
    decorGroup.add(rug)

    // ── LIGHTING SETUP ─────────────────────────────────────────────
    const lightingGroup = new THREE.Group()
    lightingGroupRef.current = lightingGroup
    scene.add(lightingGroup)

    // Warm Ambient Architectural Fill
    const ambientLight = new THREE.AmbientLight(0xfcf7ed, 0.8)
    lightingGroup.add(ambientLight)

    // Sunlight through Window with Soft Contact Shadows
    const sunLight = new THREE.DirectionalLight(0xfff5e4, 1.8)
    sunLight.position.set(-4.5, 6.5, 2.5)
    sunLight.castShadow = true
    sunLight.shadow.mapSize.width = 1024
    sunLight.shadow.mapSize.height = 1024
    sunLight.shadow.camera.near = 0.5
    sunLight.shadow.camera.far = 20
    sunLight.shadow.camera.left = -4
    sunLight.shadow.camera.right = 4
    sunLight.shadow.camera.top = 4
    sunLight.shadow.camera.bottom = -4
    sunLight.shadow.bias = -0.0005
    lightingGroup.add(sunLight)
    sunLightRef.current = sunLight

    // Bedside Warm Point Light
    const pointLightBed = new THREE.PointLight(0xffe1aa, 1.2, 3.5)
    pointLightBed.position.set(-0.96, 0.85, -2.15)
    pointLightBed.castShadow = true
    lightingGroup.add(pointLightBed)
    pointLightBedRef.current = pointLightBed

    // Desk Task Lamp Point Light
    const pointLightDesk = new THREE.PointLight(0xffebcb, 0.9, 2.5)
    pointLightDesk.position.set(-1.72, 1.05, 1.18)
    lightingGroup.add(pointLightDesk)
    pointLightDeskRef.current = pointLightDesk

    // Window light bloom plane (sky horizon outside window)
    const skyBackGeo = new THREE.PlaneGeometry(3.5, 3.0)
    const skyBackMat = new THREE.MeshBasicMaterial({ color: 0xe8f0f8 })
    const skyBack = new THREE.Mesh(skyBackGeo, skyBackMat)
    skyBack.position.set(-0.4, 1.4, -2.7)
    lightingGroup.add(skyBack)

    // ── ANIMATION TICKER LOOP ──────────────────────────────────────
    let clock = new THREE.Clock()

    const animate = () => {
      animFrameRef.current = requestAnimationFrame(animate)

      const delta = clock.getDelta()
      const elapsed = clock.getElapsedTime()

      // 1. Progress interpolation towards target progress
      const targetP = targetProgressRef.current
      currentProgressRef.current = THREE.MathUtils.lerp(currentProgressRef.current, targetP, delta * 3.5)
      const p = currentProgressRef.current

      // 2. Animate STAGE 1: Foundation (active p in [0.0, 0.20])
      if (foundationGroupRef.current) {
        const t1 = easeOutCubic(p / 0.2)
        foundationGroupRef.current.position.y = (t1 - 1) * 2.2
        foundationGroupRef.current.scale.set(
          THREE.MathUtils.lerp(0.85, 1.0, t1),
          t1,
          THREE.MathUtils.lerp(0.85, 1.0, t1)
        )
      }

      // 3. Animate STAGE 2: Bed Assembly (active p in [0.20, 0.45])
      if (bedGroupRef.current) {
        const t2 = easeOutCubic((p - 0.2) / 0.25)
        bedGroupRef.current.position.y = (t2 - 1) * 1.5
        bedGroupRef.current.position.z = (1 - t2) * -1.8
        bedGroupRef.current.scale.setScalar(THREE.MathUtils.lerp(0.7, 1.0, t2))
        bedGroupRef.current.visible = p > 0.05
      }

      // 4. Animate STAGE 3: Wardrobe Assembly (active p in [0.45, 0.65])
      if (wardrobeGroupRef.current) {
        const t3 = easeOutCubic((p - 0.45) / 0.2)
        wardrobeGroupRef.current.position.x = 1.9 + (1 - t3) * 1.5
        wardrobeGroupRef.current.position.y = (t3 - 1) * 1.2
        wardrobeGroupRef.current.scale.set(
          THREE.MathUtils.lerp(0.6, 1.0, t3),
          t3,
          THREE.MathUtils.lerp(0.6, 1.0, t3)
        )
        wardrobeGroupRef.current.visible = p > 0.25
      }

      // 5. Animate STAGE 4: Workspace Assembly (active p in [0.65, 0.85])
      if (workspaceGroupRef.current) {
        const t4 = easeOutCubic((p - 0.65) / 0.2)
        workspaceGroupRef.current.position.y = (t4 - 1) * 1.4
        workspaceGroupRef.current.position.z = (1 - t4) * 1.2
        workspaceGroupRef.current.scale.setScalar(THREE.MathUtils.lerp(0.6, 1.0, t4))
        workspaceGroupRef.current.visible = p > 0.45
      }

      // 6. Animate STAGE 5: Decor & Lighting Warmup (active p in [0.85, 1.0])
      if (decorGroupRef.current) {
        const t5 = easeOutCubic((p - 0.85) / 0.15)
        decorGroupRef.current.position.y = (t5 - 1) * 0.8
        decorGroupRef.current.scale.setScalar(t5)
        decorGroupRef.current.visible = p > 0.7
      }

      // Dynamic light intensity ramp
      const lightFactor = easeInOutQuad(p)
      if (sunLightRef.current) sunLightRef.current.intensity = 1.8 * lightFactor
      if (pointLightBedRef.current) pointLightBedRef.current.intensity = 1.2 * lightFactor
      if (pointLightDeskRef.current) pointLightDeskRef.current.intensity = 0.9 * lightFactor

      // 7. Subtle camera choreography & idle turntable orbit
      if (!isOrbitingUser && controlsRef.current && cameraRef.current) {
        // Continuous gentle breathing orbit in Stage 5
        if (p > 0.85) {
          const orbitAngle = Math.sin(elapsed * 0.28) * 0.25
          const camRadius = 8.5
          cameraRef.current.position.x = Math.sin(0.78 + orbitAngle) * camRadius
          cameraRef.current.position.z = Math.cos(0.78 + orbitAngle) * camRadius
          cameraRef.current.position.y = 4.3 + Math.sin(elapsed * 0.4) * 0.12
        } else {
          // Camera slides between stage positions
          const curCfg = STAGE_CONFIG[activeStage]
          cameraRef.current.position.lerp(
            new THREE.Vector3(...curCfg.cameraPos),
            delta * 2.0
          )
          controlsRef.current.target.lerp(
            new THREE.Vector3(...curCfg.cameraTarget),
            delta * 2.0
          )
        }
      }

      controls.update()
      renderer.render(scene, camera)
    }

    animate()

    // ── RESIZE LISTENER ────────────────────────────────────────────
    const handleResize = () => {
      if (!container || !rendererRef.current || !cameraRef.current) return
      const w = container.clientWidth
      const h = container.clientHeight
      cameraRef.current.aspect = w / h
      cameraRef.current.updateProjectionMatrix()
      rendererRef.current.setSize(w, h)
    }
    window.addEventListener('resize', handleResize)

    // ── CLEANUP ON UNMOUNT ─────────────────────────────────────────
    return () => {
      cancelAnimationFrame(animFrameRef.current)
      window.removeEventListener('resize', handleResize)
      controls.dispose()
      renderer.dispose()
      if (renderer.domElement && container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement)
      }
    }
  }, [activeStage, isOrbitingUser, webglSupported])

  return (
    <div className="rg-3d-experience-container">
      {/* 3D WebGL Canvas Viewport */}
      <div className="rg-3d-viewport-wrapper">
        <div ref={mountRef} className="rg-3d-canvas-mount" />

        {/* Fallback for WebGL-disabled environments */}
        {!webglSupported && (
          <div className="rg-3d-fallback-view">
            <img
              src="/roomgenius-assets/3d-model.jpeg"
              alt="RoomGenius AI 3D Room Diorama"
              className="rg-3d-fallback-img"
            />
            <div className="rg-3d-fallback-badge">
              <span>Interactive 3D Simulation Fallback</span>
            </div>
          </div>
        )}

        {/* Floating Architectural Stage HUD */}
        <div className="rg-3d-hud-overlay">
          <div className="rg-3d-stage-pill">
            <span className="rg-3d-stage-dot" />
            <span className="rg-3d-stage-kicker">Assembly Sequence</span>
            <strong className="rg-3d-stage-name">
              Stage {STAGE_CONFIG[activeStage].number}: {STAGE_CONFIG[activeStage].title}
            </strong>
          </div>

          <div className="rg-3d-controls-row">
            <button
              type="button"
              className="rg-3d-btn-icon"
              title={isPlaying ? 'Pause Auto-Play' : 'Resume Auto-Play'}
              onClick={() => setIsPlaying(!isPlaying)}
            >
              {isPlaying ? '⏸' : '▶'}
            </button>
            <button
              type="button"
              className="rg-3d-btn-icon"
              title="Reset Camera View"
              onClick={() => {
                if (cameraRef.current && controlsRef.current) {
                  cameraRef.current.position.set(5.8, 4.2, 6.2)
                  controlsRef.current.target.set(0, 0.8, 0)
                  controlsRef.current.update()
                }
              }}
            >
              ⟲
            </button>
          </div>
        </div>

        {/* 3D Orbit Interaction Hint */}
        <div className="rg-3d-hint">
          <span>✦ Drag to rotate 3D room · Scroll to inspect</span>
        </div>
      </div>

      {/* Assembly Stage Timeline Selector Bar */}
      <div className="rg-3d-timeline-bar" role="tablist" aria-label="3D Room Assembly Timeline">
        {([1, 2, 3, 4, 5] as AssemblyStage[]).map(stageNum => {
          const cfg = STAGE_CONFIG[stageNum]
          const isSelected = activeStage === stageNum
          return (
            <button
              key={stageNum}
              type="button"
              role="tab"
              aria-selected={isSelected}
              className={`rg-3d-timeline-step ${isSelected ? 'rg-3d-timeline-step--active' : ''}`}
              onClick={() => {
                setIsPlaying(false)
                goToStage(stageNum)
              }}
            >
              <div className="rg-3d-step-header">
                <span className="rg-3d-step-idx">{cfg.number}</span>
                <span className="rg-3d-step-title">{cfg.title}</span>
              </div>
              <div className="rg-3d-step-bar-wrap">
                <div
                  className="rg-3d-step-bar-fill"
                  style={{
                    width: isSelected
                      ? '100%'
                      : activeStage > stageNum
                      ? '100%'
                      : '0%',
                  }}
                />
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}

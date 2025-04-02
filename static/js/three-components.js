// Three.js Components for E-Cycle AI
class DeviceViewer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error('Container not found:', containerId);
            return;
        }

        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, this.container.clientWidth / this.container.clientHeight, 0.1, 1000);
        
        // Set up renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setClearColor(0xffffff, 0);
        this.container.appendChild(this.renderer.domElement);

        // Set up lights
        this.setupLights();

        // Set up controls
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.screenSpacePanning = false;
        this.controls.minDistance = 3;
        this.controls.maxDistance = 10;

        // Set initial camera position
        this.camera.position.z = 5;

        // Handle window resize
        window.addEventListener('resize', () => this.onWindowResize(), false);

        // Create placeholder
        this.createDevicePlaceholder();

        // Start animation loop
        this.animate();

        // Try WebSocket connection
        try {
            this.setupWebSocket();
        } catch (error) {
            console.log('WebSocket not available, running in standalone mode');
        }
    }

    setupLights() {
        // Ambient light
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        this.scene.add(ambientLight);

        // Directional light (sun-like)
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(5, 5, 5);
        this.scene.add(directionalLight);

        // Point lights for better details
        const pointLight1 = new THREE.PointLight(0xffffff, 0.5);
        pointLight1.position.set(5, -5, 5);
        this.scene.add(pointLight1);

        const pointLight2 = new THREE.PointLight(0xffffff, 0.5);
        pointLight2.position.set(-5, 5, -5);
        this.scene.add(pointLight2);
    }

    createDevicePlaceholder() {
        // Remove existing model if any
        if (this.currentModel) {
            this.scene.remove(this.currentModel);
        }

        // Create a placeholder cube
        const geometry = new THREE.BoxGeometry(2, 2, 0.2);
        const material = new THREE.MeshPhongMaterial({
            color: 0x4CAF50,
            transparent: true,
            opacity: 0.8,
            side: THREE.DoubleSide
        });

        this.currentModel = new THREE.Mesh(geometry, material);
        this.scene.add(this.currentModel);

        // Add wireframe
        const wireframe = new THREE.LineSegments(
            new THREE.EdgesGeometry(geometry),
            new THREE.LineBasicMaterial({ color: 0x000000, linewidth: 2 })
        );
        this.currentModel.add(wireframe);

        // Add recycling symbol
        this.addRecyclingSymbol();
    }

    addRecyclingSymbol() {
        const radius = 0.5;
        const segments = 32;
        const material = new THREE.LineBasicMaterial({ color: 0x4CAF50 });

        // Create three arrows in a circular pattern
        for (let i = 0; i < 3; i++) {
            const angle = (i * 2 * Math.PI) / 3;
            const curve = new THREE.EllipseCurve(
                0, 0,
                radius, radius,
                angle, angle + (2 * Math.PI) / 3,
                false, 0
            );

            const points = curve.getPoints(segments);
            const geometry = new THREE.BufferGeometry().setFromPoints(points);
            const arrow = new THREE.Line(geometry, material);
            arrow.position.z = 0.11;
            this.currentModel.add(arrow);

            // Add arrowhead
            const arrowHead = this.createArrowHead(
                points[points.length - 1].x,
                points[points.length - 1].y,
                angle + (2 * Math.PI) / 3
            );
            arrowHead.position.z = 0.11;
            this.currentModel.add(arrowHead);
        }
    }

    createArrowHead(x, y, angle) {
        const size = 0.1;
        const shape = new THREE.Shape();
        shape.moveTo(0, 0);
        shape.lineTo(-size, size);
        shape.lineTo(-size, -size);
        shape.lineTo(0, 0);

        const geometry = new THREE.ShapeGeometry(shape);
        const material = new THREE.MeshBasicMaterial({ color: 0x4CAF50, side: THREE.DoubleSide });
        const arrowHead = new THREE.Mesh(geometry, material);

        arrowHead.position.set(x, y, 0);
        arrowHead.rotation.z = angle;

        return arrowHead;
    }

    async updateDeviceModel(deviceType) {
        // In a real application, you would load different 3D models based on device type
        // For now, we'll create different geometric shapes
        if (this.currentModel) {
            this.scene.remove(this.currentModel);
        }

        let geometry;
        switch (deviceType.toLowerCase()) {
            case 'smartphone':
                geometry = new THREE.BoxGeometry(1, 2, 0.1);
                break;
            case 'laptop':
                geometry = new THREE.BoxGeometry(3, 2, 0.2);
                break;
            case 'tablet':
                geometry = new THREE.BoxGeometry(2, 2.5, 0.1);
                break;
            case 'desktop':
                geometry = new THREE.BoxGeometry(2, 2, 2);
                break;
            default:
                geometry = new THREE.SphereGeometry(1, 32, 32);
        }

        const material = new THREE.MeshPhongMaterial({
            color: 0x4CAF50,
            transparent: true,
            opacity: 0.8,
            side: THREE.DoubleSide
        });

        this.currentModel = new THREE.Mesh(geometry, material);
        this.scene.add(this.currentModel);

        // Add wireframe
        const wireframe = new THREE.LineSegments(
            new THREE.EdgesGeometry(geometry),
            new THREE.LineBasicMaterial({ color: 0x000000 })
        );
        this.currentModel.add(wireframe);

        // Try to notify server about model update
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            try {
                this.ws.send(JSON.stringify({
                    type: 'modelUpdate',
                    deviceType: deviceType
                }));
            } catch (error) {
                console.log('Error sending update to server');
            }
        }
    }

    setupWebSocket() {
        try {
            this.ws = new WebSocket('ws://localhost:3000');

            this.ws.onopen = () => {
                console.log('Connected to WebSocket server');
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'modelUpdate') {
                        this.updateDeviceModel(data.deviceType);
                    }
                } catch (error) {
                    console.error('Error processing message:', error);
                }
            };

            this.ws.onerror = (error) => {
                console.log('WebSocket error, running in standalone mode');
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected, running in standalone mode');
            };
        } catch (error) {
            console.log('WebSocket not supported, running in standalone mode');
        }
    }

    onWindowResize() {
        this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        // Update controls
        this.controls.update();

        // Rotate model
        if (this.currentModel) {
            this.currentModel.rotation.y += 0.005;
        }

        this.renderer.render(this.scene, this.camera);
    }
}

// Initialize device viewer when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const viewer = new DeviceViewer('deviceViewer');
    window.addEventListener('resize', () => viewer.onWindowResize());
}); 
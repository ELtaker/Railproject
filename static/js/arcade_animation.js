/**
 * Arcade Claw Machine Animation for Giveaway Winners
 * Enhanced and optimized version for Raildrops project
 * Using anime.js for advanced animations
 */

// Main animation controller namespace
const ArcadeAnimation = {
    // Configuration
    config: {
        avatarCount: 8,            // Number of participant avatars to display
        animationDuration: 4000,   // Total animation time in ms
        clawGrabDuration: 500,     // Time it takes to grab an avatar
        clawMoveDuration: 1000,    // Time it takes to move the claw
        particleCount: 30,         // Number of particles for effects
        particleLifespan: 2000,    // How long particles live in ms
        confettiColors: [          // Colors for winner celebration
            '#FFC700', '#FF0000', '#2E3191', '#41D3BD', 
            '#FF7BAC', '#8B5CF6', '#FFA07A', '#20B2AA'
        ],
        avatarColors: [            // Vibrant colors for avatars
            '#FF5252', '#FF4081', '#E040FB', '#7C4DFF', 
            '#536DFE', '#448AFF', '#40C4FF', '#18FFFF',
            '#64FFDA', '#69F0AE', '#B2FF59', '#EEFF41', 
            '#FFFF00', '#FFD740', '#FFAB40', '#FF6E40'
        ],
        enableParticles: true,     // Enable particle effects
        enableSounds: false,       // Enable sound effects (future feature)
        debugMode: false           // Enable for debugging output
    },
    
    // State variables
    canvas: null,                 // Canvas element
    ctx: null,                    // Canvas 2D context
    winnerName: '',               // Name of the winner (from Django)
    participants: [],             // List of participant names
    avatars: [],                  // Avatar objects for drawing
    particles: [],                // Particle effects
    claw: null,                   // Claw object
    dropZone: null,               // Drop zone object
    animationActive: false,       // Is animation currently running
    isInitialized: false,         // Has initialization completed
    animeTimeline: null,          // anime.js timeline for animations
    dpr: window.devicePixelRatio || 1,  // Device pixel ratio for HD screens
    
    /**
     * Initialize the animation system
     */
    init() {
        // Get canvas and context
        this.canvas = document.getElementById('arcadeCanvas');
        if (!this.canvas) {
            console.error('Canvas element not found');
            return;
        }
        
        this.ctx = this.canvas.getContext('2d');
        
        // Initialize objects
        this.initClaw();
        this.initDropZone();
        
        // Set up event listeners
        window.addEventListener('resize', () => this.resizeCanvas());
        
        // Make canvas responsive
        this.resizeCanvas();
        
        // Add a class to the winner name element to hide it initially
        const winnerElement = document.getElementById('vinnerNavn');
        if (winnerElement) {
            winnerElement.style.opacity = '0';
        }
        
        this.isInitialized = true;
        this.log('Animation initialized');
    },
    
    /**
     * Set the winner name from the Django template
     */
    setWinnerName(name) {
        this.winnerName = name || 'Vinner';
        this.log(`Winner name set to: ${this.winnerName}`);
        
        // Update the displayed winner name element
        const winnerElement = document.getElementById('vinnerNavn');
        if (winnerElement && winnerElement.querySelector('h3')) {
            winnerElement.querySelector('h3').textContent = this.winnerName;
        }
    },
    
    /**
     * Set the list of participants from Django
     */
    setParticipantList(participants) {
        this.participants = Array.isArray(participants) ? participants : [];
        this.log(`Participant list set with ${this.participants.length} entries`);
        
        // Re-initialize avatars with new data
        if (this.isInitialized) {
            this.initializeAvatars();
            this.drawScene();
        }
    },
    
    /**
     * Make the canvas responsive and adjust for high-DPI displays
     */
    resizeCanvas() {
        if (!this.canvas || !this.ctx) return;
        
        const rect = this.canvas.getBoundingClientRect();
        
        // Set canvas dimensions accounting for device pixel ratio
        this.canvas.width = rect.width * this.dpr;
        this.canvas.height = rect.height * this.dpr;
        
        // Scale all drawing operations
        this.ctx.scale(this.dpr, this.dpr);
        
        // Update positions of elements that depend on canvas size
        this.updateElementPositions(rect.width, rect.height);
        
        // Redraw the scene
        this.drawScene();
    },
    
    /**
     * Update positions of elements based on canvas dimensions
     */
    updateElementPositions(width, height) {
        // Update claw position
        if (this.claw) {
            this.claw.startX = width / 2;
            this.claw.startY = height * 0.15;
            this.claw.x = this.claw.startX;
            this.claw.y = this.claw.startY;
        }
        
        // Update drop zone position
        if (this.dropZone) {
            this.dropZone.x = width * 0.15;
            this.dropZone.y = height * 0.85;
        }
        
        // Re-position avatars
        this.initializeAvatars();
    },
    
    /**
     * Initialize the claw object
     */
    initClaw() {
        this.claw = {
            x: 0,                // X position (set in updateElementPositions)
            y: 0,                // Y position (set in updateElementPositions)
            startX: 0,           // Starting X position
            startY: 0,           // Starting Y position
            width: 50,           // Width of the claw
            height: 70,          // Height of the claw
            isGrabbing: false,   // Is it currently grabbing an avatar
            grabbedAvatar: null, // Reference to grabbed avatar
            color: '#555555'     // Claw color
        };
    },
    
    /**
     * Initialize the drop zone (hole where avatars are dropped)
     */
    initDropZone() {
        this.dropZone = {
            x: 0,                // X position (set in updateElementPositions)
            y: 0,                // Y position (set in updateElementPositions)
            width: 100,          // Width of the drop zone
            height: 70,          // Height of the drop zone
            color: '#222222'     // Drop zone color
        };
    },
    
    /**
     * Initialize avatar objects for participants
     */
    initializeAvatars() {
        if (!this.canvas) return;
        
        // Get canvas dimensions
        const width = this.canvas.width / this.dpr;
        const height = this.canvas.height / this.dpr;
        
        // Calculate number of avatars to display
        const count = Math.min(this.config.avatarCount, this.participants.length || 5);
        
        // Avatar properties
        const avatarRadius = Math.max(width, height) * 0.035; // Responsive size
        const spacing = avatarRadius * 1.5;  // Space between avatars
        
        // Calculate starting position for the group
        const groupWidth = count * (avatarRadius * 2 + spacing) - spacing;
        const startX = (width - groupWidth) / 2 + avatarRadius;
        const baseY = height * 0.75;  // Position on the "floor"
        
        // Create new avatar array
        this.avatars = [];
        
        // Create avatars
        for (let i = 0; i < count; i++) {
            const colorIndex = i % this.config.avatarColors.length;
            const participantIndex = this.participants.length > 0 ? 
                                   Math.floor(Math.random() * this.participants.length) : -1;
            
            this.avatars.push({
                id: `avatar-${i}`,
                x: startX + i * (avatarRadius * 2 + spacing),
                y: baseY,
                radius: avatarRadius,
                color: this.config.avatarColors[colorIndex],
                name: participantIndex >= 0 ? this.participants[participantIndex] : '',
                isWinner: participantIndex >= 0 && 
                          this.participants[participantIndex] === this.winnerName
            });
        }
        
        // Ensure the winner is among the avatars
        if (this.winnerName && this.participants.includes(this.winnerName)) {
            const hasWinner = this.avatars.some(a => a.isWinner);
            
            // If the winner isn't already included, replace a random avatar
            if (!hasWinner && this.avatars.length > 0) {
                const randomIndex = Math.floor(Math.random() * this.avatars.length);
                this.avatars[randomIndex].name = this.winnerName;
                this.avatars[randomIndex].isWinner = true;
                this.avatars[randomIndex].color = '#FFD700'; // Gold color for winner
            }
        }
    }

    /**
     * Utility function for debug logging
     */
    log(message) {
        if (this.config.debugMode) {
            console.log(`[ArcadeAnimation] ${message}`);
        }
    },
    
    /**
     * Event handling - dispatches events to notify the document of animation state changes
     */
    dispatchEvent(eventName, detail = {}) {
        // Create and dispatch a custom event
        const event = new CustomEvent(`arcade:${eventName}`, {
            detail: detail,
            bubbles: true,
            cancelable: true
        });
        
        this.canvas.dispatchEvent(event);
        this.log(`Event dispatched: arcade:${eventName}`);
    },
    
    /**
     * Draw the entire scene
     */
    drawScene() {
        if (!this.ctx || !this.canvas) return;
        
        // Get canvas dimensions
        const width = this.canvas.width / this.dpr;
        const height = this.canvas.height / this.dpr;
        
        // Clear canvas
        this.ctx.clearRect(0, 0, width, height);
        
        // Draw background gradient
        this.drawBackground(width, height);
        
        // Draw drop zone
        this.drawDropZone();
        
        // Draw avatars
        this.avatars.forEach(avatar => this.drawAvatar(avatar));
        
        // Draw claw
        this.drawClaw();
    },
    
    /**
     * Draw the background gradient
     */
    drawBackground(width, height) {
        // Upper part (lighter yellow/green)
        this.ctx.fillStyle = '#d9e7a9';
        this.ctx.fillRect(0, 0, width, height * 0.7);
        
        // Lower part (darker yellow/sand)
        this.ctx.fillStyle = '#f0e68c';
        this.ctx.fillRect(0, height * 0.7, width, height * 0.3);
        
        // Optional: Add some texture or pattern
        this.ctx.globalAlpha = 0.05;
        for (let i = 0; i < 20; i++) {
            const x = Math.random() * width;
            const y = Math.random() * height;
            const radius = Math.random() * 15 + 5;
            
            this.ctx.beginPath();
            this.ctx.arc(x, y, radius, 0, Math.PI * 2);
            this.ctx.fillStyle = '#000';
            this.ctx.fill();
        }
        this.ctx.globalAlpha = 1.0;
    },
    
    /**
     * Draw an avatar (participant)
     */
    drawAvatar(avatar) {
        if (!this.ctx) return;
        
        // Shadow
        this.ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
        this.ctx.shadowBlur = 5;
        this.ctx.shadowOffsetX = 2;
        this.ctx.shadowOffsetY = 2;
        
        // Main circle
        this.ctx.fillStyle = avatar.color;
        this.ctx.beginPath();
        this.ctx.arc(avatar.x, avatar.y, avatar.radius, 0, Math.PI * 2);
        this.ctx.fill();
        
        // Reset shadow
        this.ctx.shadowColor = 'transparent';
        this.ctx.shadowBlur = 0;
        this.ctx.shadowOffsetX = 0;
        this.ctx.shadowOffsetY = 0;
        
        // Add highlight reflection
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
        this.ctx.beginPath();
        this.ctx.arc(
            avatar.x - avatar.radius * 0.3,
            avatar.y - avatar.radius * 0.3,
            avatar.radius * 0.4,
            0, Math.PI * 2
        );
        this.ctx.fill();
        
        // Optional: Add initial letter of participant name
        if (avatar.name && avatar.name.length > 0) {
            const initial = avatar.name.charAt(0).toUpperCase();
            this.ctx.fillStyle = 'white';
            this.ctx.font = `bold ${avatar.radius}px Arial`;
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText(initial, avatar.x, avatar.y);
        }
    },
    
    /**
     * Draw the claw
     */
    drawClaw() {
        if (!this.ctx || !this.claw) return;
        
        const x = this.claw.x;
        const y = this.claw.y;
        const width = this.claw.width;
        const height = this.claw.height;
        
        // Shadow
        this.ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
        this.ctx.shadowBlur = 10;
        this.ctx.shadowOffsetX = 3;
        this.ctx.shadowOffsetY = 3;
        
        // Draw the body of the claw
        this.ctx.fillStyle = '#555555';
        this.ctx.beginPath();
        this.ctx.rect(x - width/4, y, width/2, height/2);
        this.ctx.fill();
        
        // Reset shadow
        this.ctx.shadowColor = 'transparent';
        this.ctx.shadowBlur = 0;
        this.ctx.shadowOffsetX = 0;
        this.ctx.shadowOffsetY = 0;
        
        // Draw the left finger of the claw
        this.ctx.fillStyle = '#444444';
        this.ctx.beginPath();
        this.ctx.rect(x - width/2, y + height/2, width/3, height/2);
        this.ctx.fill();
        
        // Draw the right finger of the claw
        this.ctx.fillStyle = '#444444';
        this.ctx.beginPath();
        this.ctx.rect(x + width/6, y + height/2, width/3, height/2);
        this.ctx.fill();
        
        // If the claw is grabbing an avatar, draw it
        if (this.claw.isGrabbing && this.claw.grabbedAvatar) {
            const avatar = this.claw.grabbedAvatar;
            this.drawAvatar({
                ...avatar,
                x: x,
                y: y + height + avatar.radius
            });
        }
    },
    
    /**
     * Draw the drop zone where the winner is revealed
     */
    drawDropZone() {
        if (!this.ctx || !this.dropZone) return;
        
        const { x, y, width, height, color } = this.dropZone;
        
        // Shadow
        this.ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
        this.ctx.shadowBlur = 10;
        this.ctx.shadowOffsetX = 0;
        this.ctx.shadowOffsetY = 5;
        
        // Draw the main box
        this.ctx.fillStyle = color;
        this.ctx.fillRect(x - width/2, y - height/2, width, height);
        
        // Reset shadow
        this.ctx.shadowColor = 'transparent';
        this.ctx.shadowBlur = 0;
        this.ctx.shadowOffsetX = 0;
        this.ctx.shadowOffsetY = 0;
        
        // Add edge highlight
        this.ctx.strokeStyle = '#111111';
        this.ctx.lineWidth = 3;
        this.ctx.strokeRect(x - width/2, y - height/2, width, height);
        
        // Add inner highlight
        this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.moveTo(x - width/2 + 5, y - height/2 + 5);
        this.ctx.lineTo(x + width/2 - 5, y - height/2 + 5);
        this.ctx.lineTo(x + width/2 - 5, y + height/2 - 5);
        this.ctx.stroke();
    },
    
    /**
     * Create a particle effect at the specified position
     */
    createParticleEffect(x, y, particleCount, colors, type = 'confetti') {
        if (!this.config.enableParticles || !this.ctx) return;
        
        // Create particles
        for (let i = 0; i < particleCount; i++) {
            const color = colors[Math.floor(Math.random() * colors.length)];
            const size = Math.random() * 10 + 5;
            const angle = Math.random() * Math.PI * 2;
            const velocity = Math.random() * 5 + 2;
            const rotationSpeed = (Math.random() - 0.5) * 0.2;
            
            this.particles.push({
                x,
                y,
                size,
                color,
                vx: Math.cos(angle) * velocity,
                vy: Math.sin(angle) * velocity * 0.8 - 1, // Slight upward bias
                rotation: Math.random() * Math.PI * 2,
                rotationSpeed,
                gravity: 0.1,
                opacity: 1,
                lifespan: this.config.particleLifespan,
                birth: Date.now(),
                type
            });
        }
        
        // Start particle animation if it's not already running
        if (!this.particleAnimationActive) {
            this.particleAnimationActive = true;
            this.animateParticles();
        }
    },
    
    /**
     * Animate particles
     */
    animateParticles() {
        if (this.particles.length === 0) {
            this.particleAnimationActive = false;
            return;
        }
        
        // Update and draw particles
        const now = Date.now();
        this.particles = this.particles.filter(p => {
            // Update position with gravity
            p.x += p.vx;
            p.y += p.vy;
            p.vy += p.gravity;
            p.rotation += p.rotationSpeed;
            
            // Calculate age and fade out
            const age = now - p.birth;
            p.opacity = Math.max(0, 1 - (age / p.lifespan));
            
            // Draw the particle
            if (this.ctx) {
                this.ctx.save();
                this.ctx.globalAlpha = p.opacity;
                this.ctx.translate(p.x, p.y);
                this.ctx.rotate(p.rotation);
                
                if (p.type === 'confetti') {
                    // Draw confetti as rectangles
                    this.ctx.fillStyle = p.color;
                    this.ctx.fillRect(-p.size/2, -p.size/2, p.size, p.size/2);
                } else if (p.type === 'sparkle') {
                    // Draw sparkles as stars
                    this.ctx.fillStyle = p.color;
                    this.drawStar(0, 0, 5, p.size/2, p.size/4);
                } else {
                    // Default circle particle
                    this.ctx.fillStyle = p.color;
                    this.ctx.beginPath();
                    this.ctx.arc(0, 0, p.size/2, 0, Math.PI * 2);
                    this.ctx.fill();
                }
                
                this.ctx.restore();
            }
            
            // Keep particle if it's still alive
            return age < p.lifespan;
        });
        
        // Continue animation loop
        if (this.particles.length > 0) {
            requestAnimationFrame(() => this.animateParticles());
        } else {
            this.particleAnimationActive = false;
        }
    },
    
    /**
     * Draw a star shape for particles
     */
    drawStar(cx, cy, spikes, outerRadius, innerRadius) {
        let rot = Math.PI / 2 * 3;
        let x = cx;
        let y = cy;
        const step = Math.PI / spikes;
        
        this.ctx.beginPath();
        this.ctx.moveTo(cx, cy - outerRadius);
        
        for (let i = 0; i < spikes; i++) {
            x = cx + Math.cos(rot) * outerRadius;
            y = cy + Math.sin(rot) * outerRadius;
            this.ctx.lineTo(x, y);
            rot += step;
            
            x = cx + Math.cos(rot) * innerRadius;
            y = cy + Math.sin(rot) * innerRadius;
            this.ctx.lineTo(x, y);
            rot += step;
        }
        
        this.ctx.lineTo(cx, cy - outerRadius);
        this.ctx.closePath();
        this.ctx.fill();
    },
    
    /**
     * Show the winner's name with animation
     */
    revealWinner() {
        const winnerElement = document.getElementById('vinnerNavn');
        if (!winnerElement) return;
        
        // Dispatch an event to notify listeners that the winner is being revealed
        this.dispatchEvent('winnerRevealed', { winner: this.winnerName });
        
        // Create confetti effect at the drop zone
        if (this.dropZone) {
            // Primary confetti at the drop zone
            this.createParticleEffect(
                this.dropZone.x, 
                this.dropZone.y - 50, 
                this.config.particleCount * 2, 
                this.config.confettiColors, 
                'confetti'
            );
            
            // Secondary sparkles for extra flair
            setTimeout(() => {
                this.createParticleEffect(
                    this.dropZone.x + 30, 
                    this.dropZone.y - 30, 
                    Math.floor(this.config.particleCount / 2), 
                    ['#FFD700', '#FFFFFF', '#FFC107'], 
                    'sparkle'
                );
            }, 300);
        }
        
        // Add 'show' class for CSS animation
        winnerElement.classList.add('show');
        winnerElement.style.opacity = '1';
        
        // Use anime.js for more advanced animation
        if (typeof anime !== 'undefined') {
            // Winner name animation
            anime({
                targets: winnerElement,
                opacity: [0, 1],
                scale: [0.5, 1],
                translateY: [-20, 0],
                duration: 1200,
                easing: 'easeOutElastic(1, .6)',
                complete: () => {
                    // Show winner info card with animation
                    const winnerCard = document.getElementById('winnerInfoCard');
                    if (winnerCard) {
                        winnerCard.style.display = 'block';
                        anime({
                            targets: winnerCard,
                            opacity: [0, 1],
                            translateY: [20, 0],
                            duration: 800,
                            easing: 'easeOutCubic',
                            complete: () => {
                                // Dispatch completion event
                                this.dispatchEvent('animationComplete');
                            }
                        });
                    } else {
                        // If no winner card, still notify of completion
                        this.dispatchEvent('animationComplete');
                    }
                }
            });
        } else {
            // Fallback if anime.js is not available
            winnerElement.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            winnerElement.style.opacity = '1';
            winnerElement.style.transform = 'scale(1)';
            
            // Show winner card after a delay
            setTimeout(() => {
                const winnerCard = document.getElementById('winnerInfoCard');
                if (winnerCard) {
                    winnerCard.style.display = 'block';
                    winnerCard.style.opacity = '1';
                }
                this.dispatchEvent('animationComplete');
            }, 1200);
        }
    },
    
    /**
     * Start the animation sequence
     */
    startAnimation() {
        if (this.animationActive) return;
        this.animationActive = true;
        
        // Dispatch animation start event
        this.dispatchEvent('animationStart');
        
        // Reset state
        this.resetAnimation();
        
        // Ensure we have avatars
        if (this.avatars.length === 0) {
            this.initializeAvatars();
        }
        
        // Find the winner avatar (or pick one randomly)
        let winnerAvatar = this.avatars.find(a => a.isWinner);
        if (!winnerAvatar && this.avatars.length > 0) {
            const randomIndex = Math.floor(Math.random() * this.avatars.length);
            winnerAvatar = this.avatars[randomIndex];
            winnerAvatar.isWinner = true;
        }
        
        if (!winnerAvatar) {
            this.log('No avatars available for animation');
            this.animationActive = false;
            this.dispatchEvent('animationError', { error: 'No avatars available' });
            return;
        }
        
        // Create a slight delay before starting the animation
        // This gives time for the UI to update and prepare
        setTimeout(() => {
            // Start the animation sequence
            this.animateClawSequence(winnerAvatar);
        }, 300);
    },
    
    /**
     * Reset animation state
     */
    resetAnimation() {
        // Reset claw position
        if (this.claw) {
            this.claw.x = this.claw.startX;
            this.claw.y = this.claw.startY;
            this.claw.isGrabbing = false;
            this.claw.grabbedAvatar = null;
        }
        
        // Hide winner display
        const winnerElement = document.getElementById('vinnerNavn');
        if (winnerElement) {
            winnerElement.style.opacity = '0';
            winnerElement.classList.remove('show');
        }
    },
    
    /**
     * Animate the claw grabbing sequence using anime.js
     */
    animateClawSequence(targetAvatar) {
        // Make sure anime.js is available
        if (typeof anime === 'undefined') {
            this.log('anime.js is not available, falling back to basic animation');
            this.animateClawSequenceBasic(targetAvatar);
            return;
        }
        
        // Reset animation timeline if it exists
        if (this.animeTimeline) {
            this.animeTimeline.pause();
        }
        
        // Create a new timeline
        this.animeTimeline = anime.timeline({
            easing: 'easeOutQuad',
            update: () => this.drawScene(),  // Redraw on each update
            complete: () => {
                this.animationActive = false;
                this.log('Animation sequence completed');
            }
        });
        
        // Define target positions
        const targets = {
            // Position above target avatar
            aboveTarget: {
                x: targetAvatar.x,
                y: targetAvatar.y - targetAvatar.radius - this.claw.height - 10
            },
            // Position to grab avatar
            grabPosition: {
                x: targetAvatar.x,
                y: targetAvatar.y - targetAvatar.radius + 5
            },
            // Position above drop zone
            aboveDrop: {
                x: this.dropZone.x,
                y: this.dropZone.y - this.claw.height - 20
            },
            // Position to drop the avatar
            dropPosition: {
                x: this.dropZone.x,
                y: this.dropZone.y - this.claw.height/2
            },
            // Starting position
            start: {
                x: this.claw.startX,
                y: this.claw.startY
            }
        };
        
        // Create sparkle effect at the target avatar
        this.createParticleEffect(
            targetAvatar.x,
            targetAvatar.y,
            10,
            ['#FFD700', '#FFFFFF', '#FFEB3B'],
            'sparkle'
        );
        
        // Step 1: Move to position above target
        this.animeTimeline.add({
            targets: this.claw,
            x: targets.aboveTarget.x,
            y: targets.aboveTarget.y,
            duration: 1000,
            easing: 'easeInOutQuad'
        });
        
        // Step 2: Lower to grab avatar
        this.animeTimeline.add({
            targets: this.claw,
            y: targets.grabPosition.y,
            duration: 600,
            easing: 'easeInQuad'
        });
        
        // Step 3: Grab the avatar
        this.animeTimeline.add({
            duration: 300,
            begin: () => {
                // Create small particle effect for grabbing
                this.createParticleEffect(
                    targetAvatar.x,
                    targetAvatar.y,
                    5,
                    ['#FFFFFF', '#EEEEEE'],
                    'circle'
                );
                
                // Grab the avatar
                this.claw.isGrabbing = true;
                this.claw.grabbedAvatar = targetAvatar;
                
                // Remove avatar from the array so it's not drawn twice
                this.avatars = this.avatars.filter(a => a !== targetAvatar);
            }
        });
        
        // Step 4: Raise with avatar
        this.animeTimeline.add({
            targets: this.claw,
            y: targets.aboveTarget.y,
            duration: 600,
            easing: 'easeOutQuad'
        });
        
        // Step 5: Move to position above drop zone
        this.animeTimeline.add({
            targets: this.claw,
            x: targets.aboveDrop.x,
            y: targets.aboveDrop.y,
            duration: 1000,
            easing: 'easeInOutQuad'
        });
        
        // Step 6: Lower to drop position
        this.animeTimeline.add({
            targets: this.claw,
            y: targets.dropPosition.y,
            duration: 400,
            easing: 'easeInQuad'
        });
        
        // Step 7: Drop the avatar
        this.animeTimeline.add({
            duration: 300,
            begin: () => {
                this.claw.isGrabbing = false;
                this.claw.grabbedAvatar = null;
                
                // Reveal the winner
                this.revealWinner();
            }
        });
        
        // Step 8: Return to starting position
        this.animeTimeline.add({
            targets: this.claw,
            x: targets.start.x,
            y: targets.start.y,
            duration: 800,
            easing: 'easeInOutQuad'
        });
    },
    
    /**
     * Fallback animation method using basic requestAnimationFrame
     * Only used if anime.js is not available
     */
    animateClawSequenceBasic(targetAvatar) {
        // Animation states
        const STATES = {
            MOVE_TO_TARGET: 0,
            LOWER_TO_GRAB: 1,
            GRAB_AVATAR: 2,
            RAISE_WITH_AVATAR: 3,
            MOVE_TO_DROP: 4,
            LOWER_TO_DROP: 5,
            DROP_AVATAR: 6,
            RETURN_TO_START: 7,
            COMPLETED: 8
        };
        
        let currentState = STATES.MOVE_TO_TARGET;
        let startTime = null;
        let lastTime = null;
        let stateStartTime = null;
        
        // Define target positions
        const targets = {
            // Position above target avatar
            aboveTarget: {
                x: targetAvatar.x,
                y: targetAvatar.y - targetAvatar.radius - this.claw.height - 10
            },
            // Position to grab avatar
            grabPosition: {
                x: targetAvatar.x,
                y: targetAvatar.y - targetAvatar.radius + 5
            },
            // Position above drop zone
            aboveDrop: {
                x: this.dropZone.x,
                y: this.dropZone.y - this.claw.height - 20
            },
            // Position to drop the avatar
            dropPosition: {
                x: this.dropZone.x,
                y: this.dropZone.y - this.claw.height/2
            },
            // Starting position
            start: {
                x: this.claw.startX,
                y: this.claw.startY
            }
        };
        
        // State durations in milliseconds
        const durations = {
            [STATES.MOVE_TO_TARGET]: 1000,
            [STATES.LOWER_TO_GRAB]: 600,
            [STATES.GRAB_AVATAR]: 300,
            [STATES.RAISE_WITH_AVATAR]: 600,
            [STATES.MOVE_TO_DROP]: 1000,
            [STATES.LOWER_TO_DROP]: 400,
            [STATES.DROP_AVATAR]: 300,
            [STATES.RETURN_TO_START]: 800
        };
        
        // Animation frame callback
        const animate = (timestamp) => {
            if (!startTime) {
                startTime = timestamp;
                stateStartTime = timestamp;
            }
            
            const totalElapsed = timestamp - startTime;
            const stateElapsed = timestamp - stateStartTime;
            
            // Calculate progress through current state
            const stateDuration = durations[currentState] || 1000;
            const progress = Math.min(stateElapsed / stateDuration, 1);
            
            // Process based on current state
            switch (currentState) {
                case STATES.MOVE_TO_TARGET:
                    // Move claw horizontally to position above target
                    this.claw.x = this.lerp(this.claw.x, targets.aboveTarget.x, progress);
                    this.claw.y = this.lerp(this.claw.y, targets.aboveTarget.y, progress);
                    break;
                    
                case STATES.LOWER_TO_GRAB:
                    // Lower the claw to grab the avatar
                    this.claw.y = this.lerp(targets.aboveTarget.y, targets.grabPosition.y, progress);
                    break;
                    
                case STATES.GRAB_AVATAR:
                    // Grab the avatar
                    if (!this.claw.isGrabbing && progress > 0.5) {
                        this.claw.isGrabbing = true;
                        this.claw.grabbedAvatar = targetAvatar;
                        
                        // Remove avatar from the array so it's not drawn twice
                        this.avatars = this.avatars.filter(a => a !== targetAvatar);
                    }
                    break;
                    
                case STATES.RAISE_WITH_AVATAR:
                    // Raise the claw with the grabbed avatar
                    this.claw.y = this.lerp(targets.grabPosition.y, targets.aboveTarget.y, progress);
                    break;
                    
                case STATES.MOVE_TO_DROP:
                    // Move to position above drop zone
                    this.claw.x = this.lerp(targets.aboveTarget.x, targets.aboveDrop.x, progress);
                    this.claw.y = this.lerp(targets.aboveTarget.y, targets.aboveDrop.y, progress);
                    break;
                    
                case STATES.LOWER_TO_DROP:
                    // Lower the claw to drop position
                    this.claw.y = this.lerp(targets.aboveDrop.y, targets.dropPosition.y, progress);
                    break;
                    
                case STATES.DROP_AVATAR:
                    // Drop the avatar
                    if (this.claw.isGrabbing && progress > 0.3) {
                        this.claw.isGrabbing = false;
                        this.claw.grabbedAvatar = null;
                        
                        // Reveal the winner name
                        this.revealWinner();
                    }
                    break;
                    
                case STATES.RETURN_TO_START:
                    // Return claw to starting position
                    this.claw.x = this.lerp(targets.dropPosition.x, targets.start.x, progress);
                    this.claw.y = this.lerp(targets.dropPosition.y, targets.start.y, progress);
                    break;
                    
                default:
                    break;
            }
            
            // Draw the current state
            this.drawScene();
            
            // Move to next state if current state is complete
            if (progress >= 1 && currentState < STATES.COMPLETED) {
                currentState++;
                stateStartTime = timestamp;
            }
            
            // Continue animation if not completed
            if (currentState < STATES.COMPLETED) {
                lastTime = timestamp;
                requestAnimationFrame(animate);
            } else {
                // Animation complete
                this.animationActive = false;
                this.log('Animation sequence completed');
            }
        };
        
        // Start the animation
        requestAnimationFrame(animate);
    },
    
    /**
     * Start the animation sequence
     * This method is called when the Start button is clicked
     */
    startAnimation() {
        // Don't start if already running
        if (this.animationActive) return;
        
        this.log('Starting animation sequence');
        this.animationActive = true;
        
        // Hide winner info if it's visible
        const winnerInfoCard = document.getElementById('winnerInfoCard');
        if (winnerInfoCard) {
            winnerInfoCard.style.display = 'none';
            winnerInfoCard.style.opacity = '0';
        }
        
        // Dispatch animation start event
        this.dispatchEvent('arcade:animationStart', {
            participantCount: this.participants.length,
            timestamp: new Date().getTime()
        });
        
        // Reset positions if needed
        this.updateElementPositions(this.canvas.width, this.canvas.height);
        
        // Create animation timeline
        this.createAnimationTimeline();
        
        // Play the animation
        if (this.animeTimeline) {
            this.animeTimeline.play();
        }
    },
    
    /**
     * Linear interpolation helper
     */
    lerp(start, end, progress) {
        return start + (end - start) * progress;
    }
};

// Global functions for Django template integration
function setWinnerName(name) {
    ArcadeAnimation.setWinnerName(name);
}

function setParticipantList(participants) {
    ArcadeAnimation.setParticipantList(participants);
}

function startAnimation() {
    ArcadeAnimation.startAnimation();
}

// Initialize the animation when the document is ready
document.addEventListener('DOMContentLoaded', function() {
    ArcadeAnimation.init();
});

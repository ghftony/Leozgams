// Simple Parkour Game
// Canvas-based HTML5 game with running, jumping, platforms, obstacles and coins

const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

const W = canvas.width;
const H = canvas.height;

// ─── Constants ───────────────────────────────────────────────────────────────
const GRAVITY = 0.5;
const PLAYER_SPEED = 5;
const JUMP_FORCE = -11;
const DOUBLE_JUMP_FORCE = -10;
const GROUND_Y = H - 60;

// ─── Game State ───────────────────────────────────────────────────────────────
let score = 0;
let best = 0;
let level = 1;
let gameRunning = false;
let frameCount = 0;
let scrollSpeed = 3;
let spawnTimer = 0;
let spawnInterval = 90;

// ─── Player ───────────────────────────────────────────────────────────────────
const player = {
    x: 100,
    y: GROUND_Y - 40,
    w: 28,
    h: 40,
    vx: 0,
    vy: 0,
    onGround: false,
    canDoubleJump: false,
    usedDoubleJump: false,
    jumping: false,
    frame: 0,
    frameTimer: 0,

    reset() {
        this.x = 100;
        this.y = GROUND_Y - this.h;
        this.vx = 0;
        this.vy = 0;
        this.onGround = false;
        this.canDoubleJump = false;
        this.usedDoubleJump = false;
    },

    update() {
        // Apply movement input
        if (keys['ArrowLeft'] || keys['a']) this.vx = -PLAYER_SPEED;
        else if (keys['ArrowRight'] || keys['d']) this.vx = PLAYER_SPEED;
        else this.vx = 0;

        // Apply gravity
        this.vy += GRAVITY;

        this.x += this.vx;
        this.y += this.vy;

        // Clamp horizontally
        if (this.x < 0) this.x = 0;
        if (this.x + this.w > W) this.x = W - this.w;

        // Ground collision
        if (this.y + this.h >= GROUND_Y) {
            this.y = GROUND_Y - this.h;
            this.vy = 0;
            this.onGround = true;
            this.usedDoubleJump = false;
        } else {
            this.onGround = false;
        }

        // Platform collisions
        for (const p of platforms) {
            if (
                this.vy >= 0 &&
                this.y + this.h <= p.y + 8 &&
                this.y + this.h + this.vy >= p.y &&
                this.x + this.w > p.x &&
                this.x < p.x + p.w
            ) {
                this.y = p.y - this.h;
                this.vy = 0;
                this.onGround = true;
                this.usedDoubleJump = false;
            }
        }

        // Animation
        this.frameTimer++;
        if (this.frameTimer >= 6) {
            this.frame = (this.frame + 1) % 4;
            this.frameTimer = 0;
        }
    },

    jump() {
        if (this.onGround) {
            this.vy = JUMP_FORCE;
            this.onGround = false;
            this.usedDoubleJump = false;
        } else if (!this.usedDoubleJump) {
            this.vy = DOUBLE_JUMP_FORCE;
            this.usedDoubleJump = true;
        }
    },

    draw() {
        const x = this.x;
        const y = this.y;

        // Shadow
        ctx.fillStyle = 'rgba(0,0,0,0.3)';
        ctx.ellipse(x + this.w / 2, GROUND_Y + 2, this.w / 2, 5, 0, 0, Math.PI * 2);
        ctx.fill();

        // Body
        ctx.fillStyle = '#e94560';
        ctx.fillRect(x + 4, y + 16, 20, 20);

        // Head
        ctx.fillStyle = '#f9c784';
        ctx.beginPath();
        ctx.arc(x + this.w / 2, y + 10, 10, 0, Math.PI * 2);
        ctx.fill();

        // Eyes
        ctx.fillStyle = '#222';
        ctx.fillRect(x + 12, y + 7, 3, 3);

        // Legs (animated)
        const legOffset = this.onGround ? Math.sin(this.frame * 1.57) * 5 : 0;
        ctx.fillStyle = '#0f3460';
        ctx.fillRect(x + 6, y + 36, 7, 4 + legOffset);
        ctx.fillRect(x + 15, y + 36, 7, 4 - legOffset);

        // Arms
        const armOffset = this.onGround ? Math.sin(this.frame * 1.57 + Math.PI) * 4 : 0;
        ctx.fillStyle = '#f9c784';
        ctx.fillRect(x, y + 18 + armOffset, 5, 10);
        ctx.fillRect(x + 23, y + 18 - armOffset, 5, 10);
    }
};

// ─── Collections ──────────────────────────────────────────────────────────────
let platforms = [];
let obstacles = [];
let coins = [];
let particles = [];

// ─── Input ────────────────────────────────────────────────────────────────────
const keys = {};
window.addEventListener('keydown', e => {
    keys[e.key] = true;
    if ((e.key === ' ' || e.key === 'ArrowUp' || e.key === 'w') && gameRunning) {
        player.jump();
    }
});
window.addEventListener('keyup', e => { keys[e.key] = false; });

// Touch controls
canvas.addEventListener('touchstart', e => {
    e.preventDefault();
    const touch = e.touches[0];
    const rect = canvas.getBoundingClientRect();
    const tx = touch.clientX - rect.left;
    if (tx < W / 3) keys['ArrowLeft'] = true;
    else if (tx > W * 2 / 3) keys['ArrowRight'] = true;
    else if (gameRunning) player.jump();
}, { passive: false });
canvas.addEventListener('touchend', e => {
    keys['ArrowLeft'] = false;
    keys['ArrowRight'] = false;
});

// ─── Overlay / UI ─────────────────────────────────────────────────────────────
const overlay = document.getElementById('overlay');
const startBtn = document.getElementById('startBtn');
const scoreEl = document.getElementById('score');
const bestEl = document.getElementById('best');
const levelEl = document.getElementById('level');

startBtn.addEventListener('click', startGame);

function startGame() {
    score = 0;
    level = 1;
    scrollSpeed = 3;
    spawnInterval = 90;
    frameCount = 0;
    spawnTimer = 0;
    platforms = [];
    obstacles = [];
    coins = [];
    particles = [];
    player.reset();
    overlay.style.display = 'none';
    gameRunning = true;
    updateUI();
    requestAnimationFrame(gameLoop);
}

function gameOver() {
    gameRunning = false;
    if (score > best) best = score;
    overlay.querySelector('h2').textContent = '💀 Game Over';
    overlay.querySelector('p').textContent = `Score: ${score}  |  Best: ${best}`;
    startBtn.textContent = '↺ Play Again';
    overlay.style.display = 'flex';
    updateUI();
}

function updateUI() {
    scoreEl.textContent = score;
    bestEl.textContent = best;
    levelEl.textContent = level;
}

// ─── Spawning ─────────────────────────────────────────────────────────────────
function spawnEntity() {
    const roll = Math.random();

    if (roll < 0.35) {
        // Obstacle (crate / spike)
        const type = Math.random() < 0.5 ? 'crate' : 'spike';
        const h = type === 'spike' ? 30 : 25 + Math.floor(Math.random() * 20);
        obstacles.push({
            x: W + 20,
            y: GROUND_Y - h,
            w: type === 'spike' ? 20 : 30,
            h,
            type,
            speed: scrollSpeed
        });
    } else if (roll < 0.65) {
        // Platform + optional coin
        const pw = 80 + Math.floor(Math.random() * 60);
        const ph = 14;
        const py = GROUND_Y - 80 - Math.floor(Math.random() * 90);
        platforms.push({ x: W + 20, y: py, w: pw, h: ph, speed: scrollSpeed });

        // Coin on platform
        if (Math.random() < 0.7) {
            coins.push({ x: W + 20 + pw / 2 - 8, y: py - 26, r: 9, speed: scrollSpeed, pulse: 0 });
        }
    } else {
        // Floating coin
        const cy = GROUND_Y - 80 - Math.floor(Math.random() * 100);
        for (let i = 0; i < 3; i++) {
            coins.push({ x: W + 20 + i * 40, y: cy, r: 9, speed: scrollSpeed, pulse: 0 });
        }
    }
}

// ─── Particles ────────────────────────────────────────────────────────────────
function spawnParticles(x, y, color, count = 8) {
    for (let i = 0; i < count; i++) {
        const angle = (Math.PI * 2 * i) / count + Math.random() * 0.5;
        const speed = 1.5 + Math.random() * 3;
        particles.push({
            x, y,
            vx: Math.cos(angle) * speed,
            vy: Math.sin(angle) * speed - 1,
            alpha: 1,
            color,
            size: 3 + Math.random() * 4
        });
    }
}

// ─── Drawing helpers ──────────────────────────────────────────────────────────
function drawBackground() {
    // Sky gradient
    const grad = ctx.createLinearGradient(0, 0, 0, H);
    grad.addColorStop(0, '#0d0d1a');
    grad.addColorStop(1, '#16213e');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, W, H);

    // Stars (static – use frame to drift)
    ctx.fillStyle = 'rgba(255,255,255,0.5)';
    const starSeed = [0.12, 0.27, 0.43, 0.58, 0.71, 0.85, 0.93, 0.07, 0.34, 0.66, 0.79, 0.91];
    for (let i = 0; i < starSeed.length; i++) {
        const sx = ((starSeed[i] * W * 3 - frameCount * (0.2 + i * 0.03)) % W + W) % W;
        const sy = (starSeed[(i + 3) % starSeed.length] * (H * 0.6));
        ctx.fillRect(sx, sy, 2, 2);
    }

    // Ground
    ctx.fillStyle = '#0f3460';
    ctx.fillRect(0, GROUND_Y, W, H - GROUND_Y);
    ctx.fillStyle = '#1a4a80';
    ctx.fillRect(0, GROUND_Y, W, 4);

    // Ground grid lines
    ctx.strokeStyle = 'rgba(30, 80, 140, 0.4)';
    ctx.lineWidth = 1;
    const lineSpacing = 50;
    const offset = (frameCount * scrollSpeed) % lineSpacing;
    for (let lx = -offset; lx < W; lx += lineSpacing) {
        ctx.beginPath();
        ctx.moveTo(lx, GROUND_Y);
        ctx.lineTo(lx, H);
        ctx.stroke();
    }
}

function drawPlatform(p) {
    // Platform body
    ctx.fillStyle = '#1a4a80';
    ctx.fillRect(p.x, p.y, p.w, p.h);
    ctx.fillStyle = '#2060a0';
    ctx.fillRect(p.x, p.y, p.w, 4);

    // Glow
    ctx.shadowColor = '#4090ff';
    ctx.shadowBlur = 8;
    ctx.strokeStyle = '#3070c0';
    ctx.lineWidth = 1;
    ctx.strokeRect(p.x, p.y, p.w, p.h);
    ctx.shadowBlur = 0;
}

function drawObstacle(o) {
    if (o.type === 'crate') {
        ctx.fillStyle = '#8b4513';
        ctx.fillRect(o.x, o.y, o.w, o.h);
        ctx.strokeStyle = '#5c2d0a';
        ctx.lineWidth = 2;
        ctx.strokeRect(o.x, o.y, o.w, o.h);
        // Cross
        ctx.beginPath();
        ctx.moveTo(o.x, o.y);
        ctx.lineTo(o.x + o.w, o.y + o.h);
        ctx.moveTo(o.x + o.w, o.y);
        ctx.lineTo(o.x, o.y + o.h);
        ctx.stroke();
    } else {
        // Spike
        ctx.fillStyle = '#aaa';
        ctx.beginPath();
        ctx.moveTo(o.x, o.y + o.h);
        ctx.lineTo(o.x + o.w / 2, o.y);
        ctx.lineTo(o.x + o.w, o.y + o.h);
        ctx.closePath();
        ctx.fill();
        ctx.strokeStyle = '#e94560';
        ctx.lineWidth = 1;
        ctx.stroke();
    }
}

function drawCoin(c) {
    c.pulse += 0.08;
    const scale = 1 + Math.sin(c.pulse) * 0.1;
    ctx.save();
    ctx.translate(c.x + c.r, c.y + c.r);
    ctx.scale(scale, scale);

    // Glow
    ctx.shadowColor = '#ffd700';
    ctx.shadowBlur = 12;
    ctx.fillStyle = '#ffd700';
    ctx.beginPath();
    ctx.arc(0, 0, c.r, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;

    // Inner shine
    ctx.fillStyle = '#fff8c0';
    ctx.beginPath();
    ctx.arc(-2, -2, c.r * 0.45, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();
}

function drawParticles() {
    for (const p of particles) {
        ctx.globalAlpha = p.alpha;
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
    }
    ctx.globalAlpha = 1;
}

// ─── AABB Collision ──────────────────────────────────────────────────────────
function rectOverlap(ax, ay, aw, ah, bx, by, bw, bh) {
    return ax < bx + bw && ax + aw > bx && ay < by + bh && ay + ah > by;
}

// ─── Game Loop ────────────────────────────────────────────────────────────────
function gameLoop() {
    if (!gameRunning) return;

    frameCount++;

    // Level up every 400 frames
    if (frameCount % 400 === 0) {
        level++;
        scrollSpeed = Math.min(3 + level * 0.5, 9);
        spawnInterval = Math.max(40, 90 - level * 5);
        levelEl.textContent = level;
    }

    // Score over time
    if (frameCount % 10 === 0) {
        score++;
        scoreEl.textContent = score;
    }

    // ── Spawn ──
    spawnTimer++;
    if (spawnTimer >= spawnInterval) {
        spawnEntity();
        spawnTimer = 0;
    }

    // ── Update player ──
    player.update();

    // ── Update platforms ──
    for (const p of platforms) p.x -= p.speed;
    platforms = platforms.filter(p => p.x + p.w > -10);

    // ── Update obstacles ──
    for (const o of obstacles) o.x -= o.speed;
    obstacles = obstacles.filter(o => o.x + o.w > -10);

    // ── Update coins ──
    for (const c of coins) c.x -= c.speed;
    coins = coins.filter(c => c.x + c.r * 2 > -10);

    // ── Update particles ──
    for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.1;
        p.alpha -= 0.03;
        p.size *= 0.97;
    }
    particles = particles.filter(p => p.alpha > 0.05);

    // ── Collision: player vs obstacle ──
    for (const o of obstacles) {
        if (rectOverlap(player.x + 4, player.y + 4, player.w - 8, player.h - 4, o.x, o.y, o.w, o.h)) {
            spawnParticles(player.x + player.w / 2, player.y + player.h / 2, '#e94560', 12);
            gameOver();
            return;
        }
    }

    // ── Collision: player vs coin ──
    for (let i = coins.length - 1; i >= 0; i--) {
        const c = coins[i];
        const cx = c.x + c.r;
        const cy = c.y + c.r;
        const px = player.x + player.w / 2;
        const py = player.y + player.h / 2;
        if (Math.hypot(cx - px, cy - py) < c.r + player.w / 2 - 6) {
            spawnParticles(cx, cy, '#ffd700', 6);
            score += 10;
            scoreEl.textContent = score;
            coins.splice(i, 1);
        }
    }

    // ── Fall off screen ──
    if (player.y > H + 50) {
        gameOver();
        return;
    }

    // ── Draw ──
    drawBackground();
    for (const p of platforms) drawPlatform(p);
    for (const o of obstacles) drawObstacle(o);
    for (const c of coins) drawCoin(c);
    player.draw();
    drawParticles();

    requestAnimationFrame(gameLoop);
}

// ─── Initial overlay ─────────────────────────────────────────────────────────
overlay.style.display = 'flex';

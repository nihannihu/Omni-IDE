"""
Offline Code Generation Engine (Production Resilience Layer)

When the HuggingFace Inference API is unavailable (402/429/500),
this engine provides template-based code generation for common tasks.
This ensures the IDE never shows a blank "Done!" or a raw API error.
"""

import re
import logging

logger = logging.getLogger(__name__)


# --- Template Registry ---
TEMPLATES = {
    "snake_game_python": {
        "files": {
            "snake_game.py": '''import pygame
import random
import sys

# Initialize
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 600, 400
CELL_SIZE = 20
FPS = 10

# Colors
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
DARK_GREEN = (0, 150, 0)
RED = (220, 50, 50)
WHITE = (255, 255, 255)
GRAY = (40, 40, 40)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Game - Omni-IDE")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 20)
big_font = pygame.font.SysFont("consolas", 40)

def draw_grid():
    for x in range(0, WIDTH, CELL_SIZE):
        pygame.draw.line(screen, GRAY, (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, CELL_SIZE):
        pygame.draw.line(screen, GRAY, (0, y), (WIDTH, y))

def game():
    snake = [(100, 100), (80, 100), (60, 100)]
    direction = (CELL_SIZE, 0)
    food = (random.randrange(0, WIDTH, CELL_SIZE), random.randrange(0, HEIGHT, CELL_SIZE))
    score = 0
    running = True
    game_over = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if game_over:
                    if event.key == pygame.K_r:
                        return game()
                    elif event.key == pygame.K_q:
                        running = False
                else:
                    if event.key == pygame.K_UP and direction != (0, CELL_SIZE):
                        direction = (0, -CELL_SIZE)
                    elif event.key == pygame.K_DOWN and direction != (0, -CELL_SIZE):
                        direction = (0, CELL_SIZE)
                    elif event.key == pygame.K_LEFT and direction != (CELL_SIZE, 0):
                        direction = (-CELL_SIZE, 0)
                    elif event.key == pygame.K_RIGHT and direction != (-CELL_SIZE, 0):
                        direction = (CELL_SIZE, 0)

        if not game_over:
            new_head = (snake[0][0] + direction[0], snake[0][1] + direction[1])

            # Wall collision
            if new_head[0] < 0 or new_head[0] >= WIDTH or new_head[1] < 0 or new_head[1] >= HEIGHT:
                game_over = True
            # Self collision
            elif new_head in snake:
                game_over = True
            else:
                snake.insert(0, new_head)
                if new_head == food:
                    score += 10
                    while True:
                        food = (random.randrange(0, WIDTH, CELL_SIZE), random.randrange(0, HEIGHT, CELL_SIZE))
                        if food not in snake:
                            break
                else:
                    snake.pop()

        # Draw
        screen.fill(BLACK)
        draw_grid()

        for i, segment in enumerate(snake):
            color = GREEN if i == 0 else DARK_GREEN
            pygame.draw.rect(screen, color, (*segment, CELL_SIZE - 1, CELL_SIZE - 1), border_radius=4)

        pygame.draw.rect(screen, RED, (*food, CELL_SIZE - 1, CELL_SIZE - 1), border_radius=4)

        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            go_text = big_font.render("GAME OVER", True, RED)
            screen.blit(go_text, (WIDTH // 2 - go_text.get_width() // 2, HEIGHT // 2 - 40))
            restart_text = font.render("Press R to Restart | Q to Quit", True, WHITE)
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    game()
'''
        },
        "summary": "DONE: snake_game.py"
    },
    "login_page": {
        "files": {
            "login.html": '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login</title>
    <link rel="stylesheet" href="login.css">
</head>
<body>
    <div class="container">
        <div class="login-card">
            <div class="logo">&#128274;</div>
            <h1>Welcome Back</h1>
            <p class="subtitle">Sign in to your account</p>
            <form id="loginForm">
                <div class="input-group">
                    <input type="email" id="email" placeholder="Email address" required>
                </div>
                <div class="input-group">
                    <input type="password" id="password" placeholder="Password" required>
                </div>
                <button type="submit" class="btn-primary">Sign In</button>
                <div class="divider"><span>or</span></div>
                <button type="button" class="btn-secondary">Create Account</button>
            </form>
            <p class="footer-text">Forgot your password? <a href="#">Reset it</a></p>
        </div>
    </div>
</body>
</html>''',
            "login.css": '''* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', system-ui, sans-serif; min-height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); }
.container { width: 100%; max-width: 420px; padding: 20px; }
.login-card { background: rgba(255,255,255,0.05); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.1); border-radius: 20px; padding: 40px 35px; text-align: center; }
.logo { font-size: 48px; margin-bottom: 10px; }
h1 { color: #fff; font-size: 28px; margin-bottom: 5px; }
.subtitle { color: rgba(255,255,255,0.6); margin-bottom: 30px; font-size: 14px; }
.input-group { margin-bottom: 16px; }
.input-group input { width: 100%; padding: 14px 18px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); border-radius: 12px; color: #fff; font-size: 15px; outline: none; transition: border-color 0.3s; }
.input-group input:focus { border-color: #6c63ff; }
.input-group input::placeholder { color: rgba(255,255,255,0.4); }
.btn-primary { width: 100%; padding: 14px; background: linear-gradient(135deg, #6c63ff, #9b59b6); color: #fff; border: none; border-radius: 12px; font-size: 16px; font-weight: 600; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(108, 99, 255, 0.4); }
.divider { display: flex; align-items: center; margin: 20px 0; color: rgba(255,255,255,0.3); }
.divider::before, .divider::after { content: ''; flex: 1; border-top: 1px solid rgba(255,255,255,0.1); }
.divider span { padding: 0 12px; font-size: 13px; }
.btn-secondary { width: 100%; padding: 14px; background: transparent; color: #6c63ff; border: 1px solid rgba(108, 99, 255, 0.4); border-radius: 12px; font-size: 15px; cursor: pointer; transition: background 0.3s; }
.btn-secondary:hover { background: rgba(108, 99, 255, 0.1); }
.footer-text { margin-top: 24px; color: rgba(255,255,255,0.4); font-size: 13px; }
.footer-text a { color: #6c63ff; text-decoration: none; }
.footer-text a:hover { text-decoration: underline; }'''
        },
        "summary": "DONE: login.html, login.css"
    },
    "todo_app": {
        "files": {
            "todo.html": '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Todo App</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #1a1a2e; color: #eee; display: flex; justify-content: center; padding: 60px 20px; min-height: 100vh; }
        .app { width: 100%; max-width: 500px; }
        h1 { text-align: center; font-size: 32px; margin-bottom: 30px; color: #e94560; }
        .input-row { display: flex; gap: 10px; margin-bottom: 20px; }
        .input-row input { flex: 1; padding: 14px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.15); border-radius: 10px; color: #fff; font-size: 15px; outline: none; }
        .input-row input:focus { border-color: #e94560; }
        .input-row button { padding: 14px 24px; background: #e94560; color: #fff; border: none; border-radius: 10px; font-size: 15px; cursor: pointer; }
        .todo-list { list-style: none; }
        .todo-item { display: flex; align-items: center; padding: 14px; background: rgba(255,255,255,0.04); border-radius: 10px; margin-bottom: 8px; }
        .todo-item.done span { text-decoration: line-through; opacity: 0.5; }
        .todo-item input[type="checkbox"] { margin-right: 12px; accent-color: #e94560; width: 18px; height: 18px; }
        .todo-item span { flex: 1; font-size: 15px; }
        .todo-item button { background: transparent; border: none; color: #e94560; font-size: 18px; cursor: pointer; padding: 4px 8px; }
    </style>
</head>
<body>
    <div class="app">
        <h1>&#9745; Todo App</h1>
        <div class="input-row">
            <input type="text" id="todoInput" placeholder="What needs to be done?">
            <button onclick="addTodo()">Add</button>
        </div>
        <ul class="todo-list" id="todoList"></ul>
    </div>
    <script>
        const list = document.getElementById('todoList');
        const input = document.getElementById('todoInput');
        input.addEventListener('keypress', e => { if (e.key === 'Enter') addTodo(); });
        function addTodo() {
            const text = input.value.trim();
            if (!text) return;
            const li = document.createElement('li');
            li.className = 'todo-item';
            li.innerHTML = `<input type="checkbox" onchange="this.parentElement.classList.toggle('done')"><span>${text}</span><button onclick="this.parentElement.remove()">&#10005;</button>`;
            list.appendChild(li);
            input.value = '';
            input.focus();
        }
    </script>
</body>
</html>'''
        },
        "summary": "DONE: todo.html"
    }
}


def match_template(query: str) -> str | None:
    """Match a user query to a template key using keyword analysis."""
    q = query.lower()
    
    if "snake" in q and ("game" in q or "python" in q):
        return "snake_game_python"
    if "login" in q and ("page" in q or "html" in q or "css" in q or "form" in q):
        return "login_page"
    if "todo" in q and ("app" in q or "list" in q or "html" in q):
        return "todo_app"
    
    return None


def execute_offline(query: str, safe_write_func) -> str | None:
    """
    Attempts to generate code using local templates.
    Returns the agent-style summary string, or None if no template matched.
    """
    template_key = match_template(query)
    if not template_key:
        return None
    
    template = TEMPLATES[template_key]
    files_written = []
    
    for filename, content in template.get("files", {}).items():
        try:
            safe_write_func(filename, content)
            files_written.append(filename)
            logger.info(f"[OFFLINE ENGINE] Wrote {filename}")
        except Exception as e:
            logger.error(f"[OFFLINE ENGINE] Failed to write {filename}: {e}")
    
    if files_written:
        return template.get("summary", f"DONE: {', '.join(files_written)}")
    
    return None

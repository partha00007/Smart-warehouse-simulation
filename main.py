import pygame
import numpy as np
import heapq

# ---------------- CONFIGURATION ----------------
WIDTH, HEIGHT = 750, 800
GRID_SIZE = 15
CELL_SIZE = 700 // GRID_SIZE
GRID_PIXELS = CELL_SIZE * GRID_SIZE
MOVE_INTERVAL = 650  # milliseconds between robot moves

BG = (238, 240, 243)
AISLE = (250, 250, 250)
GRID_LINE = (215, 218, 222)
SHELF = (155, 105, 65)
SHELF_EDGE = (95, 60, 35)
PACKING = (40, 175, 90)
PRODUCT = (255, 185, 45)
TEXT = (30, 35, 45)
BLUE = (50, 110, 225)
RED = (220, 65, 65)
PURPLE = (155, 75, 200)
WHITE = (255, 255, 255)
ROBOT_COLORS = [RED, BLUE, PURPLE]

PRODUCT_START = [
    (2, 2), (7, 2), (12, 2),
    (2, 7), (7, 7), (12, 7),
    (2, 12), (6, 12), (10, 12), (12, 12),
]
DELIVERY_POINTS = [(6, 13), (7, 13), (8, 13)]


# ---------------- WAREHOUSE ----------------
def create_warehouse_grid():
    grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=int)
    grid[0, :] = grid[-1, :] = 1
    grid[:, 0] = grid[:, -1] = 1

    grid[3:6, 3:6] = 1
    grid[3:6, 9:12] = 1
    grid[8:11, 3:6] = 1
    grid[8:11, 9:12] = 1

    for x, y in DELIVERY_POINTS:
        grid[y, x] = 2
    return grid


# ---------------- A* PATHFINDING ----------------
def find_path(grid, start, goal, blocked=None):
    """Return a shortest path as a list of (x, y) cells, or None."""
    if blocked is None:
        blocked = set()
    if start == goal:
        return []

    directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]

    def heuristic(pos):
        return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

    queue = [(heuristic(start), 0, start)]
    came_from = {}
    cost = {start: 0}
    visited = set()

    while queue:
        _, current_cost, current = heapq.heappop(queue)
        if current in visited:
            continue
        visited.add(current)

        if current == goal:
            path = []
            while current != start:
                path.append(current)
                current = came_from[current]
            return list(reversed(path))

        x, y = current
        for dx, dy in directions:
            nxt = (x + dx, y + dy)
            nx, ny = nxt
            if not (0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE):
                continue
            if grid[ny, nx] == 1:
                continue
            if nxt in blocked and nxt != goal:
                continue

            new_cost = current_cost + 1
            if new_cost < cost.get(nxt, float("inf")):
                cost[nxt] = new_cost
                came_from[nxt] = current
                heapq.heappush(
                    queue, (new_cost + heuristic(nxt), new_cost, nxt)
                )
    return None


# ---------------- ROBOT ----------------
class Robot:
    def __init__(self, x, y, robot_id):
        self.x = x
        self.y = y
        self.id = robot_id
        self.color = ROBOT_COLORS[robot_id - 1]
        self.has_cargo = False
        self.target = None
        self.deliveries = 0
        self.delayed = 0

    @property
    def position(self):
        return self.x, self.y

    def move_to(self, position):
        self.x, self.y = position


# ---------------- COLLISION DEMO SCREEN ----------------
def draw_collision_demo(screen, font, title_font, small_font,
                        elapsed, back_button):
    """Show two robots pausing and then taking separate routes."""
    screen.fill((240, 243, 247))

    title = title_font.render(
        "ROBOT COLLISION & REROUTING", True, (35, 45, 65))
    screen.blit(title, (110, 25))
    subtitle = font.render(
        "Watch how two robots resolve a blocked route", True, (90, 95, 110)
    )
    screen.blit(subtitle, (150, 65))

    cell = 38
    cols, rows = 17, 13
    ox, oy = 52, 115

    for row in range(rows):
        for col in range(cols):
            rect = pygame.Rect(ox + col * cell, oy + row * cell, cell, cell)
            pygame.draw.rect(screen, (252, 252, 252), rect)
            pygame.draw.rect(screen, (215, 220, 228), rect, 1)

    # Central shelves
    for row in range(4, 9):
        for col in range(7, 10):
            rect = pygame.Rect(ox + col * cell, oy + row * cell, cell, cell)
            pygame.draw.rect(screen, SHELF, rect)
            pygame.draw.rect(screen, SHELF_EDGE, rect, 2)

    # Separate illustrative paths around the central shelves
    robot1_route = [
        (2, 6), (3, 6), (4, 6), (5, 6), (6, 6),
        (6, 5), (6, 3), (7, 3), (10, 3), (11, 4),
        (11, 5), (12, 6), (13, 6), (14, 6),
    ]
    robot2_route = [
        (14, 6), (13, 6), (12, 6), (11, 6), (10, 6),
        (10, 9), (9, 10), (8, 10), (7, 10),
        (6, 9), (5, 8), (4, 7), (3, 7), (2, 7),
    ]

    approach_duration = 2.5
    pause_duration = 1.5
    reroute_duration = 5.0

    def interpolate(route, progress):
        if len(route) == 1:
            return float(route[0][0]), float(route[0][1])
        segment = min(progress * (len(route) - 1), len(route) - 1 - 1e-9)
        index = int(segment)
        fraction = segment - index
        a, b = route[index], route[index + 1]
        return (a[0] + (b[0] - a[0]) * fraction,
                a[1] + (b[1] - a[1]) * fraction)

    if elapsed < approach_duration:
        phase = "ROBOTS APPROACHING"
        progress = elapsed / approach_duration
        p1 = interpolate([(2, 6), (3, 6), (4, 6), (5, 6), (6, 6)], progress)
        p2 = interpolate([(14, 6), (13, 6), (12, 6),
                         (11, 6), (10, 6)], progress)
    elif elapsed < approach_duration + pause_duration:
        phase = "PATH BLOCKED - PAUSING"
        p1, p2 = (6, 6), (10, 6)
    else:
        phase = "REROUTING - TAKING DIFFERENT PATHS"
        progress = min(1.0, (elapsed - approach_duration -
                       pause_duration) / reroute_duration)
        p1 = interpolate(robot1_route[4:], progress)
        p2 = interpolate(robot2_route[4:], progress)

    def draw_path(route, color):
        points = [(ox + x * cell + cell // 2, oy + y * cell + cell // 2)
                  for x, y in route]
        if len(points) > 1:
            pygame.draw.lines(screen, color, False, points, 3)

    draw_path(robot1_route, RED)
    draw_path(robot2_route, BLUE)

    def draw_robot(position, color, number):
        px, py = position
        cx = int(ox + px * cell + cell // 2)
        cy = int(oy + py * cell + cell // 2)
        pygame.draw.circle(screen, color, (cx, cy), 14)
        pygame.draw.circle(screen, WHITE, (cx, cy), 14, 2)
        label = small_font.render(str(number), True, WHITE)
        screen.blit(label, (cx - label.get_width() // 2,
                            cy - label.get_height() // 2))

    draw_robot(p1, RED, 1)
    draw_robot(p2, BLUE, 2)

    if approach_duration <= elapsed < approach_duration + pause_duration:
        cx = ox + 8 * cell + cell // 2
        cy = oy + 6 * cell + cell // 2
        pygame.draw.circle(screen, PRODUCT, (cx, cy), 20, 4)
        warning = font.render("BLOCKED!", True, (190, 55, 45))
        screen.blit(warning, (cx - 40, cy - 42))

    panel = pygame.Rect(52, 620, 646, 85)
    pygame.draw.rect(screen, WHITE, panel, border_radius=10)
    pygame.draw.rect(screen, (200, 210, 225), panel, 2, border_radius=10)
    screen.blit(font.render(phase, True, (40, 90, 165)), (75, 638))

    if elapsed < approach_duration:
        message = "Both robots follow their original routes."
    elif elapsed < approach_duration + pause_duration:
        message = "They stop briefly and wait for a safe route."
    else:
        message = "They take separate routes and continue to their targets."
    screen.blit(small_font.render(message, True, (65, 70, 80)), (75, 670))

    pygame.draw.rect(screen, (65, 80, 145), back_button, border_radius=8)
    back_text = font.render("Back to Warehouse", True, WHITE)
    screen.blit(back_text, (back_button.centerx - back_text.get_width() // 2,
                            back_button.centery - back_text.get_height() // 2))


# ---------------- PERFORMANCE DASHBOARD ----------------
def draw_performance_dashboard(screen, font, title_font, small_font,
                               elapsed_seconds, total_deliveries,
                               collision_events, reroutes, steps, robots,
                               restart_button):
    """Display run statistics after every product has been delivered."""
    screen.fill((240, 243, 247))
    title = title_font.render(
        "WAREHOUSE PERFORMANCE REPORT", True, (35, 45, 65))
    screen.blit(title, (125, 28))
    subtitle = font.render(
        "All products have been delivered.", True, (70, 80, 95))
    screen.blit(subtitle, (245, 65))

    minutes = int(elapsed_seconds // 60)
    seconds = int(elapsed_seconds % 60)
    avg_time = elapsed_seconds / total_deliveries if total_deliveries else 0
    metrics = [
        ("Completed deliveries", str(total_deliveries)),
        ("Elapsed time", f"{minutes:02d}:{seconds:02d}"),
        ("Robot movement steps", str(steps)),
        ("Traffic conflicts", str(collision_events)),
        ("Reroute attempts", str(reroutes)),
        ("Avg. time per delivery", f"{avg_time:.1f} sec"),
    ]

    card_w, card_h = 205, 100
    positions = [(48, 125), (272, 125), (496, 125),
                 (48, 245), (272, 245), (496, 245)]
    for (label, value), (x, y) in zip(metrics, positions):
        rect = pygame.Rect(x, y, card_w, card_h)
        pygame.draw.rect(screen, WHITE, rect, border_radius=12)
        pygame.draw.rect(screen, (205, 215, 228), rect, 2, border_radius=12)
        screen.blit(small_font.render(
            label, True, (90, 100, 115)), (x + 14, y + 17))
        screen.blit(title_font.render(
            value, True, (45, 95, 165)), (x + 14, y + 48))

    table = pygame.Rect(48, 370, 654, 160)
    pygame.draw.rect(screen, WHITE, table, border_radius=10)
    pygame.draw.rect(screen, (205, 215, 228), table, 2, border_radius=10)
    screen.blit(font.render("Robot breakdown", True, (35, 45, 65)), (68, 385))
    screen.blit(small_font.render("Robot", True, (90, 100, 115)), (75, 420))
    screen.blit(small_font.render(
        "Deliveries", True, (90, 100, 115)), (270, 420))
    screen.blit(small_font.render("Traffic waits",
                True, (90, 100, 115)), (445, 420))
    for i, robot in enumerate(robots):
        y = 448 + i * 25
        pygame.draw.circle(screen, robot.color, (84, y + 6), 7)
        screen.blit(small_font.render(
            f"Robot {robot.id}", True, TEXT), (100, y))
        screen.blit(small_font.render(
            str(robot.deliveries), True, TEXT), (285, y))
        screen.blit(small_font.render(
            str(robot.delayed), True, TEXT), (465, y))

    note = small_font.render(
        "Metrics are collected during this simulation run; reroutes and conflicts are event counts.",
        True, (90, 100, 115)
    )
    screen.blit(note, (75, 555))

    pygame.draw.rect(screen, (55, 105, 175), restart_button, border_radius=8)
    button_text = font.render("Run Simulation Again", True, WHITE)
    screen.blit(button_text, (restart_button.centerx - button_text.get_width() // 2,
                              restart_button.centery - button_text.get_height() // 2))


# ---------------- MAIN SIMULATION ----------------
def run_simulation():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Smart Warehouse Robot Simulation")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("arial", 17)
    small_font = pygame.font.SysFont("arial", 13)
    title_font = pygame.font.SysFont("arial", 22, bold=True)

    grid = create_warehouse_grid()
    initial_positions = [(1, 1), (1, 13), (13, 1)]

    def new_robots():
        return [Robot(x, y, i + 1)
                for i, (x, y) in enumerate(initial_positions)]

    robots = new_robots()
    products = set(PRODUCT_START)
    total_deliveries = 0
    collision_events = 0
    reroutes = 0
    steps = 0
    paused = False
    collision_demo = False
    demo_start_time = 0
    running = True
    last_move = pygame.time.get_ticks()

    button_rect = pygame.Rect(20, 728, 355, 48)
    back_button = pygame.Rect(20, 728, 220, 48)
    dashboard_button = pygame.Rect(245, 650, 260, 48)
    show_dashboard = False
    run_started_at = pygame.time.get_ticks()
    run_elapsed_seconds = 0.0

    def choose_product(robot):
        reserved = {r.target for r in robots
                    if r is not robot and not r.has_cargo and r.target is not None}
        available = products - reserved
        if not available:
            return None
        return min(available, key=lambda p: abs(p[0] - robot.x) + abs(p[1] - robot.y))

    def draw_text(text, x, y, color=TEXT, use_font=None):
        surface = (use_font or font).render(text, True, color)
        screen.blit(surface, (x, y))

    def draw_warehouse():
        screen.fill(BG)
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                rect = pygame.Rect(x * CELL_SIZE, y *
                                   CELL_SIZE, CELL_SIZE, CELL_SIZE)
                if grid[y, x] == 1:
                    pygame.draw.rect(screen, SHELF, rect)
                    pygame.draw.rect(screen, SHELF_EDGE, rect, 2)
                    pygame.draw.line(screen, (190, 145, 100),
                                     (rect.left + 5, rect.centery),
                                     (rect.right - 5, rect.centery), 2)
                elif grid[y, x] == 2:
                    pygame.draw.rect(screen, PACKING, rect)
                    pygame.draw.rect(screen, WHITE, rect, 2)
                else:
                    pygame.draw.rect(screen, AISLE, rect)
                    pygame.draw.rect(screen, GRID_LINE, rect, 1)

        delivery_label = small_font.render("DELIVERY", True, WHITE)
        center_x = 7 * CELL_SIZE + CELL_SIZE // 2
        screen.blit(delivery_label, (center_x - delivery_label.get_width() // 2,
                                     13 * CELL_SIZE + 13))

        for x, y in products:
            box = pygame.Rect(x * CELL_SIZE + 7, y * CELL_SIZE + 7,
                              CELL_SIZE - 14, CELL_SIZE - 14)
            pygame.draw.rect(screen, PRODUCT, box)
            pygame.draw.rect(screen, (140, 85, 20), box, 2)
            pygame.draw.line(screen, (140, 85, 20),
                             (box.centerx, box.top), (box.centerx, box.bottom), 2)

        for robot in robots:
            if robot.target is not None:
                blocked = {r.position for r in robots if r is not robot}
                path = find_path(grid, robot.position, robot.target, blocked)
                if path:
                    points = [(robot.x * CELL_SIZE + CELL_SIZE // 2,
                               robot.y * CELL_SIZE + CELL_SIZE // 2)]
                    points += [(x * CELL_SIZE + CELL_SIZE // 2,
                                y * CELL_SIZE + CELL_SIZE // 2) for x, y in path]
                    if len(points) > 1:
                        pygame.draw.lines(
                            screen, robot.color, False, points, 2)

            cx = robot.x * CELL_SIZE + CELL_SIZE // 2
            cy = robot.y * CELL_SIZE + CELL_SIZE // 2
            pygame.draw.circle(screen, robot.color, (cx, cy), CELL_SIZE // 3)
            pygame.draw.circle(screen, WHITE, (cx, cy), CELL_SIZE // 3, 2)
            number = small_font.render(str(robot.id), True, WHITE)
            screen.blit(number, (cx - number.get_width() // 2,
                                 cy - number.get_height() // 2))
            if robot.has_cargo:
                cargo = pygame.Rect(cx - 8, cy - 21, 16, 12)
                pygame.draw.rect(screen, PRODUCT, cargo)
                pygame.draw.rect(screen, (120, 75, 15), cargo, 1)

    def update_robots():
        nonlocal total_deliveries, collision_events, reroutes, steps
        offset = steps % len(robots)
        order = robots[offset:] + robots[:offset]
        reserved_positions = {r.position for r in robots}

        for robot in order:
            if robot.has_cargo:
                if robot.target not in DELIVERY_POINTS:
                    robot.target = min(DELIVERY_POINTS,
                                       key=lambda p: abs(p[0] - robot.x) + abs(p[1] - robot.y))
            elif robot.target not in products:
                robot.target = choose_product(robot)

            if robot.target is None:
                continue

            blocked = {r.position for r in robots if r is not robot}
            path = find_path(grid, robot.position, robot.target, blocked)

            if path is None:
                # Other robots block the preferred route. Find an alternate
                # route ignoring them, then take its first safe step if possible.
                alternate = find_path(grid, robot.position, robot.target)
                if alternate is not None:
                    collision_events += 1
                    reroutes += 1
                    robot.delayed += 1
                    if alternate and alternate[0] not in reserved_positions:
                        reserved_positions.discard(robot.position)
                        robot.move_to(alternate[0])
                        reserved_positions.add(robot.position)
                        steps += 1
                continue

            if not path:
                if not robot.has_cargo and robot.position in products:
                    products.remove(robot.position)
                    robot.has_cargo = True
                    robot.target = None
                elif robot.has_cargo and robot.position in DELIVERY_POINTS:
                    robot.has_cargo = False
                    robot.target = None
                    robot.deliveries += 1
                    total_deliveries += 1
                continue

            next_position = path[0]
            if next_position in reserved_positions:
                collision_events += 1
                reroutes += 1
                robot.delayed += 1
                continue

            reserved_positions.discard(robot.position)
            robot.move_to(next_position)
            reserved_positions.add(robot.position)
            steps += 1

            if not robot.has_cargo and robot.position in products:
                products.remove(robot.position)
                robot.has_cargo = True
                robot.target = None
            elif robot.has_cargo and robot.position in DELIVERY_POINTS:
                robot.has_cargo = False
                robot.target = None
                robot.deliveries += 1
                total_deliveries += 1

    while running:
        clock.tick(30)
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if show_dashboard:
                    if dashboard_button.collidepoint(event.pos):
                        robots = new_robots()
                        products = set(PRODUCT_START)
                        total_deliveries = collision_events = reroutes = steps = 0
                        paused = False
                        show_dashboard = False
                        run_started_at = pygame.time.get_ticks()
                        run_elapsed_seconds = 0.0
                        last_move = pygame.time.get_ticks()
                elif collision_demo:
                    if back_button.collidepoint(event.pos):
                        collision_demo = False
                        last_move = pygame.time.get_ticks()
                elif button_rect.collidepoint(event.pos):
                    collision_demo = True
                    demo_start_time = pygame.time.get_ticks()

            elif event.type == pygame.KEYDOWN:
                if not collision_demo and not show_dashboard and event.key == pygame.K_SPACE:
                    paused = not paused
                elif not collision_demo and not show_dashboard and event.key == pygame.K_r:
                    robots = new_robots()
                    products = set(PRODUCT_START)
                    total_deliveries = collision_events = reroutes = steps = 0
                    run_started_at = pygame.time.get_ticks()
                    run_elapsed_seconds = 0.0
                    last_move = now

        if collision_demo:
            elapsed = (pygame.time.get_ticks() - demo_start_time) / 1000.0
            draw_collision_demo(screen, font, title_font, small_font,
                                elapsed, back_button)
            pygame.display.flip()
            continue

        if show_dashboard:
            draw_performance_dashboard(
                screen, font, title_font, small_font,
                run_elapsed_seconds, total_deliveries,
                collision_events, reroutes, steps, robots,
                dashboard_button,
            )
            pygame.display.flip()
            continue

        if not paused and now - last_move >= MOVE_INTERVAL:
            update_robots()
            last_move = now
            if not products and all(not r.has_cargo for r in robots):
                # Stop the run and show the report instead of restocking forever.
                if all(r.target is None for r in robots):
                    run_elapsed_seconds = (now - run_started_at) / 1000.0
                    show_dashboard = True

        draw_warehouse()
        pygame.draw.rect(screen, (225, 230, 236),
                         (0, GRID_PIXELS, WIDTH, HEIGHT - GRID_PIXELS))
        draw_text(f"Deliveries: {total_deliveries}", 12, 706)
        draw_text(f"Products: {len(products)}", 220, 706)
        draw_text(f"Traffic conflicts: {collision_events}", 400, 706)

        mouse_pos = pygame.mouse.get_pos()
        button_color = (105, 80, 180) if button_rect.collidepoint(
            mouse_pos) else (75, 65, 145)
        pygame.draw.rect(screen, button_color, button_rect, border_radius=8)
        pygame.draw.rect(screen, WHITE, button_rect, 2, border_radius=8)
        button_text = font.render(
            "What happens when robots collide?", True, WHITE)
        screen.blit(button_text, (button_rect.centerx - button_text.get_width() // 2,
                                  button_rect.centery - button_text.get_height() // 2))
        draw_text("SPACE: Pause/Resume     R: Reset",
                  405, 743, TEXT, small_font)

        if paused:
            overlay = pygame.Surface((WIDTH, GRID_PIXELS), pygame.SRCALPHA)
            overlay.fill((20, 25, 35, 100))
            screen.blit(overlay, (0, 0))
            label = title_font.render("PAUSED", True, WHITE)
            screen.blit(label, (GRID_PIXELS // 2 - label.get_width() // 2,
                                GRID_PIXELS // 2))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    run_simulation()

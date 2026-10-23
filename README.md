Smart Warehouse Robot Simulation
A Python-based warehouse simulation built with Pygame and NumPy. Three robots navigate a grid warehouse, collect products, and deliver them to the packing station. The simulation uses A* pathfinding to find routes around shelves and includes a separate visual demonstration of robot collision avoidance and rerouting.
Features
- 15 × 15 warehouse grid with shelves, aisles, products, and a packing station
- Three robots, each shown in a different color
- Product pickup and delivery workflow
- A* pathfinding to navigate around obstacles
- Robot traffic handling and alternative-route attempts
- Separate collision/rerouting demonstration screen
- Performance dashboard shown after all products are delivered
  
- Dashboard metrics:
  - Completed deliveries
  - Elapsed simulation time
  - Robot movement steps
  - Traffic conflicts
  - Reroute attempts
  - Average time per delivery
  - Delivery and traffic-wait breakdown for each robot
- Option to run the simulation again from the dashboard


Prerequisites
- Python 3.8 or newer
- pip
Setup
1. Create a virtual environment
Windows
python -m venv venv
venv\\Scripts\\activate
macOS / Linux
python3 -m venv venv
source venv/bin/activate
2. Install dependencies
Install the packages used by the simulation:
pip install pygame numpy
Alternatively, create a requirements.txt file containing:
pygame
numpy
Then install with:
pip install -r requirements.txt
Run the simulation

Controls and interaction
- Mouse: Use the on-screen buttons to open the collision/rerouting demonstration, return to the warehouse, or restart the simulation from the performance dashboard.
- R key: Restart the current warehouse run.
- Space key: Pause or resume the warehouse simulation.
- Window close button (X): Exit the application.
  
Performance metrics
When all products have been delivered, the simulation displays a performance report containing the results of that run.
- Completed deliveries: Number of products delivered to the packing station.
- Elapsed time: Time taken by the run, displayed as minutes and seconds.
- Robot movement steps: Count of robot movement steps recorded by the simulation.
- Traffic conflicts: Count of blocked-movement/traffic-conflict events recorded.
- Reroute attempts: Count of rerouting attempts recorded.
- Average time per delivery: Elapsed time divided by completed deliveries.
- Robot breakdown: Delivery totals and traffic waits for each robot.
The dashboard values depend on the simulation run. Traffic conflicts and reroute attempts may be zero if no such events occur.
Tech stack
- Language: Python
- Grid and numerical operations: NumPy
- Visualization and interaction: Pygame
- Pathfinding: A* search algorithm

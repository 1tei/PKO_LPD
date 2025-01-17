from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from uuid import uuid4
from pathlib import Path

from .domain import *
from .score_analysis import *
from .demo_data import DemoData, generate_demo_data
from .solver import create_solver_manager_from_xml, create_solution_manager

SOLVER_CONFIGS = {
    "TABU_SEARCH": Path(__file__).parent / "solver_configs" / "tabu_search.xml",
    "LATE_ACCEPTANCE": Path(__file__).parent / "solver_configs" / "late_acceptance.xml",
    "SIMULATED_ANNEALING": Path(__file__).parent / "solver_configs" / "simulated_annealing.xml",
}

app = FastAPI(docs_url='/q/swagger-ui')
data_sets: dict[str, VehicleRoutePlan] = {}
solver_managers: dict[str, object] = {}

@app.get("/demo-data")
async def demo_data_list():
    return [e.name for e in DemoData]


@app.get("/demo-data/{dataset_id}", response_model_exclude_none=True)
async def get_demo_data(dataset_id: str) -> VehicleRoutePlan:
    demo_data = generate_demo_data(getattr(DemoData, dataset_id))
    return demo_data


@app.get("/route-plans/{problem_id}", response_model_exclude_none=True)
async def get_route(problem_id: str) -> VehicleRoutePlan:
    normalized_problem_id = problem_id.strip('"')
    route = data_sets.get(normalized_problem_id)
    solver_manager = solver_managers.get(normalized_problem_id)

    if not route:
        raise HTTPException(status_code=404, detail="Route not found for the given problem ID")

    solver_status = (
        solver_manager.get_solver_status(normalized_problem_id)
        if solver_manager
        else "NOT_SOLVING"
    )

    return route.model_copy(update={"solver_status": solver_status})

def update_route(problem_id: str, route: VehicleRoutePlan):
    global data_sets
    data_sets[problem_id] = route


def json_to_vehicle_route_plan(json: dict) -> VehicleRoutePlan:
    visits = {
        visit['id']: visit for visit in json.get('visits', [])
    }
    vehicles = {
        vehicle['id']: vehicle for vehicle in json.get('vehicles', [])
    }

    for visit in visits.values():
        if 'vehicle' in visit:
            del visit['vehicle']

        if 'previousVisit' in visit:
            del visit['previousVisit']

        if 'nextVisit' in visit:
            del visit['nextVisit']

    visits = {visit_id: Visit.model_validate(visits[visit_id]) for visit_id in visits}
    json['visits'] = list(visits.values())

    for vehicle in vehicles.values():
        vehicle['visits'] = [visits[visit_id] for visit_id in vehicle['visits']]

    json['vehicles'] = list(vehicles.values())

    return VehicleRoutePlan.model_validate(json, context={
        'visits': visits,
        'vehicles': vehicles
    })


async def setup_context(request: Request) -> VehicleRoutePlan:
    json = await request.json()
    return json_to_vehicle_route_plan(json)

@app.post("/route-plans")
async def solve_route(request: Request, 
                      route: Annotated[VehicleRoutePlan, Depends(setup_context)]) -> str:
    # Extract the solver configuration key from the request body
    body = await request.json()
    solver_config_key = body.get("solverConfig")

    # Validate the solver configuration key
    if not solver_config_key:
        raise HTTPException(status_code=400, detail="Solver configuration key is required.")

    # Get the solver configuration path
    solver_config_path = SOLVER_CONFIGS.get(solver_config_key)
    if not solver_config_path:
        raise HTTPException(status_code=404, detail="Invalid solver configuration key.")

    # Generate a unique job ID and store the route in the global dataset
    job_id = str(uuid4())
    data_sets[job_id] = route

    # Create the solver manager using the configuration file
    solver_manager = create_solver_manager_from_xml(solver_config_path)

    # Register the solver manager globally
    solver_managers[job_id] = solver_manager

    # Build and run the solver job
    solver_manager.solve_builder() \
        .with_problem_id(job_id) \
        .with_problem(route) \
        .with_best_solution_consumer(lambda best_solution: update_route(job_id, best_solution)) \
        .run()

    return job_id



@app.delete("/route-plans/{problem_id}")
async def stop_solving(problem_id: str) -> None:
    normalized_problem_id = problem_id.strip('"')
    solver_manager = solver_managers.get(normalized_problem_id)
    if solver_manager:
        solver_manager.terminate_early(normalized_problem_id)

app.mount("/", StaticFiles(directory="resources", html=True), name="resource")

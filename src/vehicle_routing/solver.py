from timefold.solver import SolverManager, SolutionManager, SolverFactory
from timefold.solver.config import SolverConfig, ScoreDirectorFactoryConfig
from pathlib import Path
from .domain import *
from .constraints import define_constraints

def create_solver_manager_from_xml(xml_path: Path) -> SolverManager:
    solver_config = SolverConfig.create_from_xml_resource(str(xml_path))

    score_director_factory_config = ScoreDirectorFactoryConfig(
        constraint_provider_function=define_constraints
    )
    solver_config.score_director_factory_config = score_director_factory_config

    solver_factory = SolverFactory.create(solver_config)
    solver_manager = SolverManager.create(solver_factory)
    return solver_manager


def create_solution_manager(solver_manager: SolverManager) -> SolutionManager:
    return SolutionManager.create(solver_manager)

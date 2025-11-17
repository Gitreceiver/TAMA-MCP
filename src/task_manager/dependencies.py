import logging
from typing import List, Dict, Set, Optional, Union
from collections import defaultdict

# Use absolute imports
# from .data_models import Task, Dependency # Relative
from task_manager.data_models import Task, Dependency # Absolute

logger = logging.getLogger(__name__)

def _build_dependency_graph(tasks: List[Task]) -> Dict[str, Set[str]]:
    """Builds a graph representing task dependencies."""
    graph = defaultdict(set)
    task_map = {str(t.id): t for t in tasks}

    for task in tasks:
        task_id_str = str(task.id)
        if task.subtasks:
            for subtask in task.subtasks:
                subtask_id_str = f"{task.id}.{subtask.id}"
                task_map[subtask_id_str] = subtask

    for item_id_str, item in task_map.items():
        if item.dependencies:
            for dep_id in item.dependencies:
                dep_id_str = str(dep_id)
                if dep_id_str in task_map: # Ensure dependency exists
                    graph[item_id_str].add(dep_id_str)
                else:
                    logger.warning(f"Dependency '{dep_id_str}' for item '{item_id_str}' not found in task map.")
    return graph

def find_circular_dependencies(tasks: List[Task]) -> Optional[List[str]]:
    """
    Detects circular dependencies within the task list.

    Uses Depth First Search (DFS) to detect cycles in the dependency graph.

    Args:
        tasks: The list of tasks (including subtasks).

    Returns:
        A list representing the path of the circular dependency if found, otherwise None.
        Example: ['1', '2', '3.1', '1']
    """
    logger.debug("Checking for circular dependencies...")
    graph = _build_dependency_graph(tasks)
    path: List[str] = [] # Use list to maintain order
    visited: Set[str] = set() # Nodes that have been fully explored

    def dfs(node: str) -> Optional[List[str]]:
        path.append(node)
        visited.add(node)
        logger.debug(f"DFS visiting node: {node}, current path: {path}")

        for neighbor in sorted(list(graph.get(node, set()))): # Sort for consistent order
            if neighbor in path: # Cycle detected
                logger.warning(f"Circular dependency detected involving: {node} -> {neighbor}")
                # Reconstruct cycle from path
                try:
                    cycle_start_index = path.index(neighbor)
                    cycle_path = path[cycle_start_index:] + [neighbor]
                    return cycle_path
                except ValueError:
                    return path + [neighbor] # Should not happen

            if neighbor not in visited:
                result = dfs(neighbor)
                if result: # Cycle detected downstream
                    return result

        path.pop() # Backtrack
        return None

    all_nodes = list(graph.keys()) # Check all nodes as starting points
    for node in all_nodes:
        if node not in visited:
            cycle = dfs(node)
            if cycle:
                logger.error(f"Circular dependency found: {' -> '.join(cycle)}")
                return cycle # Return the first cycle found

    logger.debug("No circular dependencies found.")
    return None

# Example usage (for testing, remove later)
# if __name__ == '__main__':
#     from data_models import Task, Subtask
#     logging.basicConfig(level=logging.DEBUG)
#     tasks_cycle = [
#         Task(id=1, title="T1", dependencies=[2]),
#         Task(id=2, title="T2", dependencies=[3]),
#         Task(id=3, title="T3", dependencies=[1]) # 3 -> 1 creates cycle
#     ]
#     cycle = find_circular_dependencies(tasks_cycle)
#     print(f"Cycle found: {cycle}") # Should print ['1', '2', '3', '1'] or similar

#     tasks_no_cycle = [
#         Task(id=1, title="T1", dependencies=[]),
#         Task(id=2, title="T2", dependencies=[1]),
#         Task(id=3, title="T3", dependencies=[1, 2])
#     ]
#     cycle = find_circular_dependencies(tasks_no_cycle)
#     print(f"Cycle found: {cycle}") # Should print None

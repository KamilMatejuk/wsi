import sys
import copy
import tracemalloc
from puzzle import Puzzle
from solver import Solver
from utils import section_name, iteration_name

def heuristic1(puzzle: Puzzle):
    # distance to target for each cell
    distances = 0
    for current_y, row in enumerate(puzzle.positions):
        for current_x, p in enumerate(row):
            if p == 0:
                p = Puzzle.SIZE ** 2
            expected_x = (p - 1) % Puzzle.SIZE
            expected_y = int((p - 1) / Puzzle.SIZE)
            distances += abs(current_x - expected_x) + abs(current_y - expected_y)
    
    
    return Puzzle.SIZE * distances

# def heuristic2(puzzle: Puzzle):
#     # number of cells in incorrect position
#     incorrect = 0
#     for current_y, row in enumerate(puzzle.positions):
#         for current_x, p in enumerate(row):
#             if p == 0:
#                 p = Puzzle.SIZE ** 2
#             expected_x = (p - 1) % Puzzle.SIZE
#             expected_y = int((p - 1) / Puzzle.SIZE)
#             if (current_y != expected_y) or (current_x != expected_x):
#                 incorrect += 1
#     return Puzzle.SIZE * incorrect
            

if __name__ == "__main__":
    tracemalloc.start()
    heuristics = [heuristic1] #, heuristic2]
    solving_data = { h.__name__: [] for h in heuristics }
    
    for j in range(1):
        try:
            print(iteration_name(f'Running test {j + 1}'))
            print(section_name('Generating random 15 Puzzle'))
            # random starting permutation
            puzzle = Puzzle()
            puzzle.show()
            # solve with heuristics
            for i, heuristic in enumerate(heuristics):
                print(section_name(f'Solving with heuristic {i + 1}'))
                s = Solver(copy.deepcopy(puzzle), heuristic)
                s.solve()
                solving_data[heuristic.__name__].append(s.get_data())
                # break
                del s
            del puzzle
        except:
            continue

    # compare results
    print(iteration_name('Compare results'))
    print(f'Peak memory usage: {tracemalloc.get_traced_memory()[1]} memory blocks')
    Solver.compare(solving_data)
import argparse
import os

from klotski.gui import run_gui
from klotski.solver import State, a_star, dfs, manhattan, read_from_file, write_to_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solve the Klotski puzzle.")
    parser.add_argument("-i", "--input_file", help="The input file containing the initial board configuration.", default="example.txt")
    parser.add_argument("-o", "--output_file", help="The output file to write the solution to. Default: solution.txt", default="solution.txt")
    parser.add_argument("--algorithm", help="The search algorithm to use (dfs, a_star). Default: a_star", default="a_star")
    parser.add_argument("--no-gui", action="store_true", help="Run the GUI application")
    args = parser.parse_args()

    input_fp = os.path.join(os.path.dirname(__file__), args.input_file)
    output_fp = os.path.join(os.path.dirname(__file__), args.output_file)

    input_board = read_from_file(input_fp)
    initial_state = State(input_board, manhattan(input_board), 0, None)

    if args.algorithm == "dfs":
        sol = dfs(initial_state)
    elif args.algorithm == "a_star":
        sol = a_star(initial_state)
    else:
        raise ValueError(f"Invalid algorithm: {args.algorithm}")

    if sol:
        write_to_file(output_fp, sol)
        if not args.no_gui:
            run_gui(sol)
    else:
        print("No solution found.")

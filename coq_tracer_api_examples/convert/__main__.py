import sys
import gc
import pathlib
import argparse

import coq_tracer_api

sys.setrecursionlimit(1_000_000)
gc.disable()

parser = argparse.ArgumentParser(description="Convert a trace file, flattening it if needed.")
parser.add_argument("input", type=pathlib.Path)
parser.add_argument("output", type=pathlib.Path)
args = parser.parse_args()

trace = coq_tracer_api.load_trace(args.input, deep=True, show_tqdm=True)
coq_tracer_api.save_trace(args.output, trace)
del trace

from typing import Any, Callable, Protocol
from collections.abc import Iterator, Iterable
from dataclasses import dataclass
import os
import pathlib
from io import BytesIO
import json
import itertools
from zstd import ZSTD_compress, ZSTD_uncompress
import pickle
from tqdm import tqdm

from .tracer_types import Trace


def force_trace(trace: Trace) -> Trace:
    return Trace.model_construct(
        sub_filenames=list(trace.sub_filenames),
        declarations=list(trace.declarations),
    )


@dataclass
class _IterableFromIterator[T]:
    create_iterator: Callable[[], Iterator[T]]

    def __iter__(self) -> Iterator[T]:
        return self.create_iterator()


def join_traces(traces: Iterable[Trace]) -> Trace:
    return Trace.model_construct(
        sub_filenames=_IterableFromIterator(lambda: itertools.chain.from_iterable(trace.sub_filenames for trace in traces)),
        declarations=_IterableFromIterator(lambda: itertools.chain.from_iterable(trace.declarations for trace in traces)),
    )


def parse_trace(s: str | bytes | bytearray, use_pydantic_parser: bool = False) -> Trace:
    if use_pydantic_parser:
        return force_trace(Trace.model_validate_json(s))
    else:
        # Cannot use `model_validate_json` because it can give `ValueError: recursion limit exceeded`
        return force_trace(Trace.model_validate(json.loads(str(s))))


def stringify_trace(trace: Trace) -> str:
    return Trace.model_validate(dict(trace)).model_dump_json(indent=2)


class _ReadableFileobj(Protocol):
    def read(self, __n: int) -> bytes: ...
    def readline(self) -> bytes: ...


class _TqdmBytesReader(object):
    def __init__(self, fileobj: _ReadableFileobj, **kwargs: Any):
        self.fileobj = fileobj
        self.tqdm = tqdm(**kwargs)

    def read(self, size: int = -1):
        bytes = self.fileobj.read(size)
        self.tqdm.update(len(bytes))
        return bytes

    def readline(self):
        bytes = self.fileobj.readline()
        self.tqdm.update(len(bytes))
        return bytes

    def __enter__(self):
        self.tqdm.__enter__()
        return self

    def __exit__(self, *args: Any, **kwargs: Any):
        return self.tqdm.__exit__(*args, **kwargs)


def load_trace(filename: str | os.PathLike[str], deep: bool = False, use_pydantic_parser: bool = False, show_tqdm: bool = False) -> Trace:
    path = pathlib.Path(filename)
    compressed = str(path).endswith(".zst")
    pickled = str(path).endswith(".pickle") or str(path).endswith(".pickle.zst")
    if pickled:
        with open(path, mode="rb") as file:
            if compressed:
                uncompressed = ZSTD_uncompress(file.read())
                trace = pickle.load((lambda x: _TqdmBytesReader(x, total=len(uncompressed), leave=False) if show_tqdm else x)(BytesIO(uncompressed)))
            else:
                file_size = file.seek(0, os.SEEK_END)
                file.seek(0, os.SEEK_SET)
                trace = pickle.load((lambda x: _TqdmBytesReader(x, total=file_size, leave=False) if show_tqdm else x)(file))
            assert isinstance(trace, Trace)
            return trace
    else:
        if compressed:
            with open(path, mode="rb") as file:
                contents = ZSTD_uncompress(file.read()).decode()
        else:
            with open(path, mode="r") as file:
                contents = file.read()
        trace = parse_trace(contents, use_pydantic_parser=use_pydantic_parser)
        if deep:
            deep_trace = join_traces(
                _IterableFromIterator(
                    lambda: (lambda x: iter(tqdm(x, total=1 + len(list(trace.sub_filenames)), leave=False)) if show_tqdm and trace.sub_filenames else x)(
                        itertools.chain(
                            [Trace(sub_filenames=[], declarations=trace.declarations)],
                            (
                                load_trace(
                                    os.path.join(os.path.dirname(filename), sub_filename),
                                    deep=True,
                                    use_pydantic_parser=use_pydantic_parser,
                                    show_tqdm=show_tqdm,
                                )
                                for sub_filename in trace.sub_filenames
                            ),
                        )
                    )
                )
            )
            return Trace.model_construct(
                sub_filenames=[], declarations=deep_trace.declarations
            )  # An optimization, to not loop everything over again when iterating `sub_filenames`.
        else:
            return trace


def save_trace(filename: str | os.PathLike[str], trace: Trace) -> None:
    path = pathlib.Path(filename)
    compressed = str(path).endswith(".zst")
    pickled = str(path).endswith(".pickle") or str(path).endswith(".pickle.zst")
    if pickled:
        trace = force_trace(trace)
        with open(path, mode="wb") as file:
            if compressed:
                file.write(ZSTD_compress(pickle.dumps(trace)))
            else:
                file.write(pickle.dumps(trace))
    else:
        contents = stringify_trace(trace) + "\n"
        if compressed:
            with open(path, mode="wb") as file:
                file.write(ZSTD_compress(contents.encode()))
        else:
            with open(path, mode="w") as file:
                file.write(contents)

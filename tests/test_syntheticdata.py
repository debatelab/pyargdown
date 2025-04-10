"test main parser on synthetic datasets"


import datasets

from pyargdown.parser.main import parse_argdown

N_TESTS = 1000

def test_deepa2():

    ds = datasets.load_dataset("DebateLabKIT/deepa2-conversations", data_files='**/test*.parquet', split="train")
    ds = ds.shuffle(seed=42)
    ds_gen = iter(ds)

    def argdown_block():
        while True:
            line = next(ds_gen, None)
            if line is None:
                break
            content = dict(line["messages"][-1]).get("content")
            if content is not None and "```argdown" in content:
                content = content.split("```argdown")[1]
                content = content.split("```")[0]
                yield content

    for _ in range(N_TESTS):
        block = next(argdown_block())
        try:
            parse_argdown(block)
        except Exception as e:
            print(block)
            raise e




def test_deep_argmaps():

    ds = datasets.load_dataset("DebateLabKIT/deep-argmap-conversations", data_files='**/test*.parquet', split="train")
    ds = ds.shuffle(seed=42)
    ds_gen = iter(ds)

    def argdown_block():
        while True:
            line = next(ds_gen, None)
            if line is None:
                break
            content = line["messages"][-1].get("content")
            if content is not None and "```argdown" in content:
                content = content.split("```argdown")[1]
                content = content.split("```")[0]
                yield content

    for _ in range(N_TESTS):
        block = next(argdown_block())
        block = block.replace("?? ", "<+ ")
        try:
            parse_argdown(block)
        except Exception as e:
            print(block)
            raise e



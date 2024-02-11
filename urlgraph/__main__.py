from fire import Fire

from . import URLGraph


def main(*urls, time=60, workers=20):
    g = URLGraph()
    for url in urls:
        g.add_root(url)
    g.build(time=time, n_workers=workers)
    g.visualize()


Fire(main)

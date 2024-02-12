import asyncio

import aiohttp
import networkx as nx
from alive_progress import alive_bar
from bs4 import BeautifulSoup
from pyvis.network import Network


async def _scan(url, session):
    try:
        r = await session.get(url, verify=False)

        content_type = r.headers["content-type"]
        if "text/html" not in content_type:
            return

        text = await r.text()
        soup = BeautifulSoup(text, "html.parser")

        for link in soup.find_all("a"):
            yield link.get("href")

    except (aiohttp.ServerConnectionError, aiohttp.ClientOSError) as r:
        print(r)
        return


class URLGraph:
    def __init__(self):
        self.roots = list()
        self.visited = dict()
        self.graph = nx.Graph()

    def add_root(self, root):
        self.roots.append(root)
        self._add_node(root, root)

    def _add_node(self, url, root):
        self.visited[url] = 1
        self.graph.add_node(url, group=root)
        if hasattr(self, "bar"):
            self.bar()

    async def _search(self, url, session, root):
        async for child in _scan(url, session):
            if child and child.startswith(root):
                self.graph.add_edge(url, child)

                if child not in self.visited:
                    self._add_node(child, root)
                    asyncio.create_task(self._search(child, session, root))
                else:
                    self.visited[child] += 1

    def visualize(self):
        nt = Network("900px", "100%", directed=True, select_menu=True, filter_menu=True)
        nt.from_nx(self.graph)

        for n in nt.nodes:
            size = self.visited[n["label"]]
            n["size"] = size
            n["font"] = {"size": size * 0.5 + 2}

        nt.repulsion()
        nt.show_buttons(["physics"])
        nt.show("graph.html", notebook=False)

    def build(self, *, time=60, n_workers=20):
        async def _build():
            conn = aiohttp.TCPConnector(limit=n_workers)
            session = aiohttp.ClientSession(connector=conn)

            for root in self.roots:
                asyncio.create_task(self._search(root, session, root))

            await asyncio.sleep(time)
            await session.close()

        with alive_bar() as self.bar:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(_build())

        del self.bar
